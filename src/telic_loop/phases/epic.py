"""Epic decomposition and feedback checkpoint."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import Epic, LoopState


def _log_epic_crash(config: LoopConfig, state: LoopState, phase: str, exc: Exception) -> None:
    """Log a crash during epic-level operations. Non-fatal — loop continues."""
    try:
        from ..crash_log import log_crash
        log_crash(
            config.sprint_dir / ".crash_log.jsonl",
            error=exc,
            phase=phase,
            iteration=state.iteration,
            tokens_used=state.total_tokens_used,
        )
    except Exception:
        import traceback
        traceback.print_exc()
    print(f"  CRASH in {phase}: {type(exc).__name__}: {str(exc)[:200]}")
    print(f"  Continuing epic loop...")


def run_epic_loop(config: LoopConfig, state: LoopState, claude: Claude) -> None:
    """Outer loop for multi_epic visions. Runs the value loop once per epic."""
    from ..claude import RateLimitError, parse_rate_limit_wait_seconds
    from ..main import _acquire_lock, _release_lock, run_value_loop
    from ..render import generate_delivery_report
    from .coherence import do_full_coherence_eval

    # Ensure lock is held (protects against direct callers like run_e2e.py)
    lock_path = config.sprint_dir / ".loop.lock"
    if not _acquire_lock(lock_path):
        raise RuntimeError(f"Another loop instance is running (lock: {lock_path})")

    try:
        for i in range(len(state.epics)):
            # Re-bind epic from state.epics[i] every time — _sync_state
            # replaces state.epics with a fresh list from disk after each
            # Claude API call, making previous references stale.
            epic = state.epics[i]

            # Skip already-completed epics on resume
            if epic.status == "completed":
                print(f"\n  EPIC {i + 1}/{len(state.epics)}: {epic.title} — already completed, skipping")
                continue

            state.current_epic_index = i
            state.epics[i].status = "in_progress"
            state.save(config.state_file)
            epic = state.epics[i]  # re-bind after save
            print(f"\n{'=' * 60}")
            print(f"  EPIC {i + 1}/{len(state.epics)}: {epic.title}")
            print(f"  Value: {epic.value_statement}")
            print(f"{'=' * 60}")

            # Check if this epic already has tasks (resume scenario)
            epic_id = state.epics[i].epic_id
            epic_has_tasks = any(
                t.epic_id == epic_id for t in state.tasks.values()
            )

            if not epic_has_tasks:
                # Reset per-epic state for NEW epics (fresh QC and exit gate)
                state.exit_gate_attempts = 0
                state.verifications = {}
                state.verification_categories = []
                state.tasks_since_last_critical_eval = 0
                if "verifications_generated" in state.gates_passed:
                    state.gates_passed.remove("verifications_generated")
                state.save(config.state_file)

                # Refine epic detail if needed (just-in-time decomposition)
                epic = state.epics[i]  # re-bind after save
                if epic.detail_level == "sketch":
                    _refine_epic_detail(config, state, claude, state.epics[i])
                    epic = state.epics[i]  # re-bind after Claude call

                # Run pre-loop scoped to this epic's deliverables
                _run_epic_preloop(config, state, claude, state.epics[i])
                epic = state.epics[i]  # re-bind after Claude calls
            else:
                print(f"  Epic already has tasks — skipping preloop (resume)")

            # Tag orphaned plan tasks that match this epic.
            # Initial plan generation creates tasks with empty epic_id.
            # If quality/VRC tasks caused epic_has_tasks=True, the preloop
            # (and its tagging logic) was skipped, leaving plan tasks invisible.
            epic = state.epics[i]  # re-bind before using epic_id
            tagged = _tag_unassigned_tasks(state, epic)
            if tagged:
                print(f"  Tagged {tagged} orphaned tasks with epic_id={epic.epic_id}")
                state.save(config.state_file)

            # Run value loop for this epic
            run_value_loop(config, state, claude, inside_epic_loop=True)

            # Epic boundary evaluations — wrapped so crashes don't kill the
            # entire epic loop.  Coherence eval, critical eval, and feedback
            # checkpoint all call Claude and can hit SDK timeouts.
            try:
                # Full coherence evaluation at epic boundary
                if config.coherence_full_at_epic_boundary:
                    do_full_coherence_eval(config, state, claude)

                # Critical evaluation at epic boundary — eval-fix loop
                # Runs BEFORE marking epic complete so findings get acted on.
                # Reset exit gate state so the fix loop can re-enter cleanly.
                state.exit_gate_attempts = 0
                state.verifications = {}
                state.verification_categories = []
                if "verifications_generated" in state.gates_passed:
                    state.gates_passed.remove("verifications_generated")
                state.save(config.state_file)

                from .critical_eval import do_critical_eval
                epic = state.epics[i]  # re-bind after save
                for eval_cycle in range(config.max_epic_eval_cycles):
                    print(f"  Epic eval cycle {eval_cycle + 1}/{config.max_epic_eval_cycles} for: {epic.title}")
                    found_issues = do_critical_eval(config, state, claude)
                    if not found_issues:
                        break
                    # Critical eval created CE-* fix tasks — re-enter value loop
                    print(f"  Critical eval found issues — re-entering value loop to fix")
                    run_value_loop(config, state, claude, inside_epic_loop=True)
                    epic = state.epics[i]  # re-bind after Claude calls
                else:
                    print(f"  Max eval cycles reached — proceeding with remaining issues")

            except RateLimitError as rle:
                import time
                wait_secs = parse_rate_limit_wait_seconds(rle)
                print(f"\n  RATE LIMIT in epic eval — sleeping {wait_secs // 60}m...")
                state.save(config.state_file)
                time.sleep(wait_secs)

            except Exception as exc:
                _log_epic_crash(config, state, f"epic_{i}_boundary_eval", exc)

            # Mark epic complete — use state.epics[i] directly to survive
            # any _sync_state that replaced the list since our last re-bind.
            state.epics[i].status = "completed"
            state.save(config.state_file)

            # Epic feedback checkpoint (skip for last epic)
            if i < len(state.epics) - 1:
                try:
                    epic = state.epics[i]  # re-bind for feedback
                    response = epic_feedback_checkpoint(config, state, claude, epic)
                    if response == "stop":
                        print("  Human requested stop. Shipping completed epics.")
                        break
                    elif response == "adjust":
                        epic = state.epics[i]  # re-bind after Claude call
                        _adjust_next_epic(config, state, claude, epic.feedback_notes)
                except RateLimitError as rle:
                    import time
                    wait_secs = parse_rate_limit_wait_seconds(rle)
                    print(f"\n  RATE LIMIT in feedback — sleeping {wait_secs // 60}m...")
                    state.save(config.state_file)
                    time.sleep(wait_secs)
                except Exception as exc:
                    _log_epic_crash(config, state, f"epic_{i}_feedback", exc)

        # Full end-to-end evaluation after all epics complete
        # Unscoped — evaluates the ENTIRE deliverable for regressions
        # and cross-epic integration issues
        try:
            _run_final_eval(config, state, claude)
        except RateLimitError as rle:
            import time
            wait_secs = parse_rate_limit_wait_seconds(rle)
            print(f"\n  RATE LIMIT in final eval — sleeping {wait_secs // 60}m...")
            state.save(config.state_file)
            time.sleep(wait_secs)
        except Exception as exc:
            _log_epic_crash(config, state, "final_eval", exc)

        generate_delivery_report(config, state)

        # Generate project docs after all epics complete
        from .docs import generate_project_docs
        generate_project_docs(config, state, claude)
    finally:
        _release_lock(lock_path)


def _run_final_eval(
    config: LoopConfig, state: LoopState, claude: Claude,
) -> None:
    """Full end-to-end evaluation after all epics complete.

    Evaluates the ENTIRE deliverable without epic scoping to catch:
    - Regressions from later epics breaking earlier work
    - Cross-epic integration issues
    - Quality/usability problems that only appear at full-product level
    """
    from ..main import run_value_loop
    from .critical_eval import do_critical_eval

    print(f"\n{'=' * 60}")
    print("  FINAL END-TO-END EVALUATION")
    print(f"{'=' * 60}")

    # Temporarily unscope from any specific epic so the evaluator
    # sees the full deliverable and CE-* tasks are globally visible
    saved_complexity = state.vision_complexity
    state.vision_complexity = "single_run"

    # Reset per-loop state so the fix loop starts fresh
    state.exit_gate_attempts = 0
    state.verifications = {}
    state.verification_categories = []
    state.tasks_since_last_critical_eval = 0
    if "verifications_generated" in state.gates_passed:
        state.gates_passed.remove("verifications_generated")

    try:
        for eval_cycle in range(config.max_epic_eval_cycles):
            print(f"  Final eval cycle {eval_cycle + 1}/{config.max_epic_eval_cycles}")
            found_issues = do_critical_eval(config, state, claude)
            if not found_issues:
                print("  End-to-end evaluation passed — no regressions found")
                break
            # Fix any findings before next eval cycle
            print(f"  Final eval found issues — running fix loop")
            run_value_loop(config, state, claude, inside_epic_loop=True)
        else:
            print(f"  Max final eval cycles reached — shipping with remaining issues")
    finally:
        state.vision_complexity = saved_complexity


def epic_feedback_checkpoint(
    config: LoopConfig, state: LoopState, claude: Claude, completed_epic: Epic,
) -> str:
    """Present curated epic summary to human. Returns: proceed | adjust | stop."""
    from ..claude import AgentRole, load_prompt

    epic_idx = state.current_epic_index

    session = claude.session(
        AgentRole.REASONER,
        system_extra=(
            "Generate a curated summary of this completed epic "
            "for the human to review. Focus on what was delivered, how it "
            "maps to the vision, and what comes next."
        ),
    )

    next_epic = (
        state.epics[epic_idx + 1]
        if epic_idx + 1 < len(state.epics) else None
    )

    prompt = load_prompt("epic_feedback",
        EPIC_TITLE=completed_epic.title,
        EPIC_NUMBER=epic_idx + 1,
        EPIC_TOTAL=len(state.epics),
        EPIC_VALUE_STATEMENT=completed_epic.value_statement,
        EPIC_COMPLETION_CRITERIA="\n".join(completed_epic.completion_criteria),
        NEXT_EPIC_TITLE=next_epic.title if next_epic else "N/A (final epic)",
        VRC_VALUE_SCORE=f"{state.latest_vrc.value_score:.0%}" if state.latest_vrc else "N/A",
        VRC_VERIFIED=state.latest_vrc.deliverables_verified if state.latest_vrc else 0,
        VRC_TOTAL=state.latest_vrc.deliverables_total if state.latest_vrc else 0,
        VRC_GAPS=json.dumps(state.latest_vrc.gaps if state.latest_vrc else []),
    )
    session.send(prompt)

    # Re-bind after _sync_state may have replaced state.epics
    epic = state.epics[epic_idx]

    summary = state.agent_results.get("epic_summary", {})

    print(f"\n{'=' * 60}")
    print(f"  EPIC {epic_idx + 1}/{len(state.epics)} COMPLETE: {epic.title}")
    print(f"{'=' * 60}")
    if summary.get("summary"):
        print(f"\n  {summary['summary'].get('vision_progress', '')}")
        print(f"\n  Confidence: {summary['summary'].get('confidence', 'N/A')}")
    if epic_idx + 1 < len(state.epics):
        next_epic = state.epics[epic_idx + 1]
        print(f"\n  Next: {next_epic.title} — {next_epic.value_statement}")
    print("\n  Options: [P]roceed (default)  |  [A]djust  |  [S]top")

    timeout_min = config.epic_feedback_timeout_minutes
    if timeout_min > 0:
        print(f"  Auto-proceed in {timeout_min} minutes if no response.")

    response = _wait_for_human_response(timeout_minutes=timeout_min)

    # Write feedback to the CURRENT state.epics reference (not stale param)
    epic = state.epics[epic_idx]
    if response is None or response.lower().startswith("p"):
        epic.feedback_response = "proceed" if response else "timeout"
        return "proceed"
    elif response.lower().startswith("a"):
        epic.feedback_response = "adjust"
        notes = input("  Adjustment notes: ")
        epic.feedback_notes = notes
        return "adjust"
    elif response.lower().startswith("s"):
        epic.feedback_response = "stop"
        return "stop"
    else:
        epic.feedback_response = "proceed"
        return "proceed"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _refine_epic_detail(
    config: LoopConfig, state: LoopState, claude: Claude, epic: Epic,
) -> None:
    """Just-in-time decomposition for sketch-level epics."""
    from ..claude import AgentRole, load_prompt

    # Capture epic index to re-bind after _sync_state
    epic_idx = state.current_epic_index

    session = claude.session(
        AgentRole.REASONER,
        system_extra=(
            "Refine this epic sketch into detailed tasks. "
            "Consider what was learned from previous epics."
        ),
    )
    prompt = load_prompt("plan",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        VISION=config.vision_file.read_text(encoding="utf-8") if config.vision_file.exists() else "",
        PRD=config.prd_file.read_text(encoding="utf-8") if config.prd_file.exists() else "",
        PLAN="",
    )
    session.send(
        f"Refine epic '{epic.title}' into detailed tasks:\n"
        f"Value: {epic.value_statement}\n"
        f"Deliverables: {', '.join(epic.deliverables)}\n"
        f"Task sketch: {', '.join(epic.task_sketch)}\n\n{prompt}"
    )
    # Re-bind after _sync_state may have replaced state.epics
    state.epics[epic_idx].detail_level = "full"


def _run_epic_preloop(
    config: LoopConfig, state: LoopState, claude: Claude, epic: Epic,
) -> None:
    """Run pre-loop steps scoped to an epic's deliverables.

    1. Context discovery (scoped to epic)
    2. Plan generation — agent creates tasks via manage_task tool
    3. Tag newly created tasks with this epic's ID
    4. Run quality gates on the new tasks
    """
    from ..claude import AgentRole, load_prompt
    from ..discovery import discover_context
    from ..render import render_plan_snapshot
    from .preloop import _run_quality_gates

    # Re-discover context scoped to this epic
    if epic.detail_level == "full":
        print(f"  Running scoped context discovery for epic: {epic.title}")
        discover_context(config, claude, state)

    # Track existing task IDs so we can identify newly created ones
    existing_task_ids = set(state.tasks.keys())

    # Plan generation — agent creates tasks via manage_task tool calls
    print(f"  Generating tasks for epic: {epic.title}")
    session = claude.session(AgentRole.REASONER)
    prompt = load_prompt("plan",
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
    )
    session.send(
        f"Generate tasks for epic '{epic.title}':\n"
        f"Value: {epic.value_statement}\n"
        f"Deliverables: {', '.join(epic.deliverables)}\n"
        f"Task sketch: {', '.join(epic.task_sketch)}\n\n{prompt}",
        task_source="plan",
    )

    # Tag tasks with this epic's ID.
    # If new tasks were created by the planner, tag only those.
    # If no new tasks (planner reused existing plan), tag all untagged pending tasks.
    new_task_ids = set(state.tasks.keys()) - existing_task_ids
    tagged = 0
    if new_task_ids:
        # Tag only newly created tasks
        for tid in new_task_ids:
            task = state.tasks[tid]
            task.epic_id = epic.epic_id
            tagged += 1
    else:
        # No new tasks — this epic's tasks already exist from initial planning.
        # Tag untagged pending tasks that match this epic by ID prefix (N.X → epic_N).
        tagged += _tag_unassigned_tasks(state, epic)
    print(f"  Tagged {tagged} tasks with epic_id={epic.epic_id}")

    render_plan_snapshot(config, state)

    # Run quality gates on the new task set
    _run_quality_gates(config, state, claude)

    state.save(config.state_file)


def _tag_unassigned_tasks(state: LoopState, epic: Epic) -> int:
    """Tag unassigned pending tasks that match this epic by ID prefix.

    Tasks from initial plan generation use the convention ``N.X`` where
    N matches the epic number (``epic_N``).  This catches tasks that were
    never tagged because the epic preloop was skipped.
    """
    prefix = epic.epic_id.replace("epic_", "") + "."
    tagged = 0
    for task in state.tasks.values():
        if not task.epic_id and task.status == "pending" and task.task_id.startswith(prefix):
            task.epic_id = epic.epic_id
            tagged += 1
    return tagged


def _adjust_next_epic(
    config: LoopConfig, state: LoopState, claude: Claude, notes: str,
) -> None:
    """Re-plan next epic with human's adjustment notes."""
    from ..claude import AgentRole

    next_idx = state.current_epic_index + 1
    if next_idx >= len(state.epics):
        return
    next_epic = state.epics[next_idx]
    session = claude.session(AgentRole.REASONER)
    session.send(
        f"Adjust epic '{next_epic.title}' based on human feedback:\n"
        f"{notes}\n\n"
        f"Current plan: {next_epic.value_statement}\n"
        f"Deliverables: {', '.join(next_epic.deliverables)}"
    )


def _wait_for_human_response(timeout_minutes: int = 0) -> str | None:
    """Wait for human response with optional timeout."""
    if timeout_minutes <= 0:
        try:
            return input("  Your choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            return None

    import threading

    result: list[str | None] = [None]

    def _get_input() -> None:
        try:
            result[0] = input("  Your choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            result[0] = None

    thread = threading.Thread(target=_get_input, daemon=True)
    thread.start()
    thread.join(timeout=timeout_minutes * 60)

    if thread.is_alive():
        print(f"\n  Timeout reached ({timeout_minutes}min) — auto-proceeding")
        return None

    return result[0]
