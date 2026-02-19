"""Epic decomposition and feedback checkpoint."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import Epic, LoopState


def run_epic_loop(config: LoopConfig, state: LoopState, claude: Claude) -> None:
    """Outer loop for multi_epic visions. Runs the value loop once per epic."""
    from ..main import _acquire_lock, _release_lock, run_value_loop
    from ..render import generate_delivery_report
    from .coherence import do_full_coherence_eval

    # Ensure lock is held (protects against direct callers like run_e2e.py)
    lock_path = config.sprint_dir / ".loop.lock"
    if not _acquire_lock(lock_path):
        raise RuntimeError(f"Another loop instance is running (lock: {lock_path})")

    try:
        for i, epic in enumerate(state.epics):
            # Skip already-completed epics on resume
            if epic.status == "completed":
                print(f"\n  EPIC {i + 1}/{len(state.epics)}: {epic.title} — already completed, skipping")
                continue

            state.current_epic_index = i
            epic.status = "in_progress"
            print(f"\n{'=' * 60}")
            print(f"  EPIC {i + 1}/{len(state.epics)}: {epic.title}")
            print(f"  Value: {epic.value_statement}")
            print(f"{'=' * 60}")

            # Check if this epic already has tasks (resume scenario)
            epic_has_tasks = any(
                t.epic_id == epic.epic_id for t in state.tasks.values()
            )

            if not epic_has_tasks:
                # Reset per-epic state for NEW epics (fresh QC and exit gate)
                state.exit_gate_attempts = 0
                state.verifications = {}
                state.verification_categories = []
                state.tasks_since_last_critical_eval = 0
                if "verifications_generated" in state.gates_passed:
                    state.gates_passed.remove("verifications_generated")

                # Refine epic detail if needed (just-in-time decomposition)
                if epic.detail_level == "sketch":
                    _refine_epic_detail(config, state, claude, epic)

                # Run pre-loop scoped to this epic's deliverables
                _run_epic_preloop(config, state, claude, epic)
            else:
                print(f"  Epic already has tasks — skipping preloop (resume)")

            # Run value loop for this epic
            run_value_loop(config, state, claude, inside_epic_loop=True)

            # Mark epic complete
            epic.status = "completed"

            # Full coherence evaluation at epic boundary
            if config.coherence_full_at_epic_boundary:
                do_full_coherence_eval(config, state, claude)

            # Critical evaluation at epic boundary
            from .critical_eval import do_critical_eval
            print(f"  Running critical evaluation for completed epic: {epic.title}")
            do_critical_eval(config, state, claude)

            # Epic feedback checkpoint (skip for last epic)
            if i < len(state.epics) - 1:
                response = epic_feedback_checkpoint(config, state, claude, epic)
                if response == "stop":
                    print("  Human requested stop. Shipping completed epics.")
                    break
                elif response == "adjust":
                    _adjust_next_epic(config, state, claude, epic.feedback_notes)

        generate_delivery_report(config, state)
    finally:
        _release_lock(lock_path)


def epic_feedback_checkpoint(
    config: LoopConfig, state: LoopState, claude: Claude, completed_epic: Epic,
) -> str:
    """Present curated epic summary to human. Returns: proceed | adjust | stop."""
    from ..claude import AgentRole, load_prompt

    session = claude.session(
        AgentRole.REASONER,
        system_extra=(
            "Generate a curated summary of this completed epic "
            "for the human to review. Focus on what was delivered, how it "
            "maps to the vision, and what comes next."
        ),
    )

    next_epic = (
        state.epics[state.current_epic_index + 1]
        if state.current_epic_index + 1 < len(state.epics) else None
    )

    prompt = load_prompt("epic_feedback",
        EPIC_TITLE=completed_epic.title,
        EPIC_NUMBER=state.current_epic_index + 1,
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

    summary = state.agent_results.get("epic_summary", {})

    print(f"\n{'=' * 60}")
    print(f"  EPIC {state.current_epic_index + 1}/{len(state.epics)} COMPLETE: {completed_epic.title}")
    print(f"{'=' * 60}")
    if summary.get("summary"):
        print(f"\n  {summary['summary'].get('vision_progress', '')}")
        print(f"\n  Confidence: {summary['summary'].get('confidence', 'N/A')}")
    if next_epic:
        print(f"\n  Next: {next_epic.title} — {next_epic.value_statement}")
    print("\n  Options: [P]roceed (default)  |  [A]djust  |  [S]top")

    timeout_min = config.epic_feedback_timeout_minutes
    if timeout_min > 0:
        print(f"  Auto-proceed in {timeout_min} minutes if no response.")

    response = _wait_for_human_response(timeout_minutes=timeout_min)

    if response is None or response.lower().startswith("p"):
        completed_epic.feedback_response = "proceed" if response else "timeout"
        return "proceed"
    elif response.lower().startswith("a"):
        completed_epic.feedback_response = "adjust"
        notes = input("  Adjustment notes: ")
        completed_epic.feedback_notes = notes
        return "adjust"
    elif response.lower().startswith("s"):
        completed_epic.feedback_response = "stop"
        return "stop"
    else:
        completed_epic.feedback_response = "proceed"
        return "proceed"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _refine_epic_detail(
    config: LoopConfig, state: LoopState, claude: Claude, epic: Epic,
) -> None:
    """Just-in-time decomposition for sketch-level epics."""
    from ..claude import AgentRole, load_prompt

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
    epic.detail_level = "full"


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
        # Tag untagged pending tasks that match this epic's deliverables.
        for task in state.tasks.values():
            if not task.epic_id and task.status == "pending":
                task.epic_id = epic.epic_id
                tagged += 1
    print(f"  Tagged {tagged} tasks with epic_id={epic.epic_id}")

    render_plan_snapshot(config, state)

    # Run quality gates on the new task set
    _run_quality_gates(config, state, claude)

    state.save(config.state_file)


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
