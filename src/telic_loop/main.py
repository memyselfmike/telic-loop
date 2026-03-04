"""Entry point: plan → review → implement → evaluate → complete."""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from .agent import Agent, AgentRole, RateLimitError, load_prompt, parse_rate_limit_wait_seconds
from .config import LoopConfig
from .render import generate_delivery_report, render_plan_snapshot, render_value_checklist
from .state import LoopState


# ---------------------------------------------------------------------------
# Phase determination
# ---------------------------------------------------------------------------

def determine_phase(state: LoopState) -> str:
    """Compute current phase from gate state. Never stored — always derived."""
    if "plan_generated" not in state.gates_passed:
        return "plan"
    if "plan_reviewed" not in state.gates_passed:
        return "review"
    if _has_work_remaining(state):
        return "implement"
    if "critical_eval_passed" not in state.gates_passed:
        return "evaluate"
    if _value_gate_passes(state):
        return "complete"
    return "implement"  # Eval found gaps → back to building


def _has_work_remaining(state: LoopState) -> bool:
    """True if there are pending/in_progress tasks or failing verifications."""
    has_pending = any(
        t.status in ("pending", "in_progress") for t in state.tasks.values()
    )
    has_failing = any(
        v.status == "failed" for v in state.verifications.values()
    )
    return has_pending or has_failing


def _value_gate_passes(state: LoopState) -> bool:
    """True when all work is done and evaluation has passed."""
    all_done = all(
        t.status in ("done", "blocked", "descoped") for t in state.tasks.values()
    )
    all_pass = all(
        v.status in ("passed", "blocked") for v in state.verifications.values()
    )
    has_eval = "critical_eval_passed" in state.gates_passed
    return all_done and all_pass and has_eval


# ---------------------------------------------------------------------------
# Phase dispatchers
# ---------------------------------------------------------------------------

def _run_plan_phase(config: LoopConfig, state: LoopState, agent: Agent) -> bool:
    """Planner discovers context and creates implementation tasks."""
    prompt = load_prompt("planner",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        PROJECT_DIR=str(config.effective_project_dir),
        MAX_TASK_DESC_CHARS=str(config.max_task_description_chars),
        MAX_FILES_PER_TASK=str(config.max_files_per_task),
    )
    session = agent.session(AgentRole.PLANNER, system_extra=prompt)
    session.send(
        "Read the Vision and PRD, discover the project context, "
        "then create a complete implementation plan as structured tasks.",
        task_source="plan",
    )
    if state.tasks:
        state.pass_gate("plan_generated")
        render_plan_snapshot(config, state)
        return True
    return False


def _run_review_phase(config: LoopConfig, state: LoopState, agent: Agent) -> bool:
    """Reviewer evaluates plan quality in a separate context."""
    plan_state = _format_plan_state(state)
    prompt = load_prompt("reviewer",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        PROJECT_DIR=str(config.effective_project_dir),
        PLAN_STATE=plan_state,
    )
    session = agent.session(AgentRole.REVIEWER, system_extra=prompt)
    session.send(
        "Review the implementation plan. Report findings via report_eval_finding. "
        "Use verdict 'SHIP_READY' if the plan is ready, or list issues if it needs revision.",
    )

    # Check if reviewer approved (critical_eval_passed gate set by handle_eval_finding)
    if state.gate_passed("critical_eval_passed"):
        state.pass_gate("plan_reviewed")
        # Clear the critical_eval_passed gate — it will be re-used for the real eval
        state.gates_passed.discard("critical_eval_passed")
        return True

    # Reviewer found issues — planner needs to revise
    state.exit_gate_attempts += 1
    if state.exit_gate_attempts >= config.max_plan_review_attempts:
        # Accept the plan after max review attempts
        state.pass_gate("plan_reviewed")
        state.exit_gate_attempts = 0
        return True

    # Remove plan_generated to trigger re-planning
    state.gates_passed.discard("plan_generated")
    return False


def _run_implement_phase(config: LoopConfig, state: LoopState, agent: Agent) -> bool:
    """Builder implements, verifies, and fixes."""
    state_summary = _format_state_summary(state)
    budget_warning = _format_budget_warning(config, state)

    prompt = load_prompt("builder",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        PROJECT_DIR=str(config.effective_project_dir),
        ITERATION=str(state.iteration),
        MAX_ITERATIONS=str(config.max_iterations),
        STATE_SUMMARY=state_summary,
        MAX_FIX_ATTEMPTS=str(config.max_fix_attempts),
        BUDGET_WARNING=budget_warning,
    )
    session = agent.session(AgentRole.BUILDER, system_extra=prompt)

    # Reset exit request flag before each builder session
    state.exit_requested = False

    session.send(
        "Review the current state and work through your priorities. "
        "Fix failures first, then execute pending tasks, then generate verifications.",
        task_source="agent",
    )

    # Run verification scripts independently (builder doesn't grade own work)
    _run_verifications(config, state)

    return True


def _run_evaluate_phase(config: LoopConfig, state: LoopState, agent: Agent) -> bool:
    """Evaluator judges quality adversarially."""
    state_summary = _format_state_summary(state)

    prompt = load_prompt("evaluator",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        PROJECT_DIR=str(config.effective_project_dir),
        STATE_SUMMARY=state_summary,
    )

    # Add Playwright MCP for UI evaluation
    mcp_servers = {}
    extra_tools: list[str] = []
    services = state.context.services
    if services or state.context.deliverable_type in ("software",):
        from .agent import PLAYWRIGHT_MCP_TOOLS
        mcp_servers = {
            "playwright": {
                "command": "npx",
                "args": ["@anthropic-ai/mcp-server-playwright"],
            }
        }
        extra_tools = list(PLAYWRIGHT_MCP_TOOLS)

    session = agent.session(
        AgentRole.EVALUATOR,
        system_extra=prompt,
        mcp_servers=mcp_servers,
        extra_tools=extra_tools,
    )

    state.exit_gate_attempts += 1
    session.send(
        "Evaluate the deliverable against the Vision and PRD. "
        "Report findings via report_eval_finding. "
        "Use verdict 'SHIP_READY' if ready to ship, or list issues to fix.",
    )
    return True


def _run_verifications(config: LoopConfig, state: LoopState) -> None:
    """Run verification scripts and update state with results."""
    from .testing import run_tests_parallel

    pending = [
        v for v in state.verifications.values()
        if v.status in ("pending", "failed") and v.script_path
    ]
    if not pending:
        return

    results = run_tests_parallel(pending, timeout=120)

    from .state import FailureRecord
    from datetime import datetime

    for vid, (exit_code, stdout, stderr) in results.items():
        v = state.verifications.get(vid)
        if not v:
            continue
        v.attempts += 1
        if exit_code == 0:
            v.status = "passed"
            state.regression_baseline.add(vid)
        else:
            v.status = "failed"
            v.failures.append(FailureRecord(
                timestamp=datetime.now().isoformat(),
                attempt=v.attempts,
                exit_code=exit_code,
                stdout=stdout[:2000],
                stderr=stderr[:2000],
            ))


# ---------------------------------------------------------------------------
# State formatting helpers
# ---------------------------------------------------------------------------

def _format_plan_state(state: LoopState) -> str:
    """Format task list for reviewer prompt."""
    lines = []
    for t in sorted(state.tasks.values(), key=lambda x: x.task_id):
        deps = f" (deps: {', '.join(t.dependencies)})" if t.dependencies else ""
        lines.append(f"- {t.task_id} [{t.status}]: {t.description}")
        lines.append(f"  Value: {t.value}")
        lines.append(f"  Acceptance: {t.acceptance}{deps}")
        if t.files_expected:
            lines.append(f"  Files: {', '.join(t.files_expected)}")
    return "\n".join(lines) or "(no tasks)"


def _format_state_summary(state: LoopState) -> str:
    """Format full state for builder/evaluator prompts."""
    lines = []

    # Tasks
    done = sum(1 for t in state.tasks.values() if t.status == "done")
    total = len(state.tasks)
    lines.append(f"## Tasks: {done}/{total} complete")
    for t in sorted(state.tasks.values(), key=lambda x: x.task_id):
        lines.append(f"- {t.task_id} [{t.status}]: {t.description}")
        if t.status == "blocked":
            lines.append(f"  Blocked: {t.blocked_reason}")
    lines.append("")

    # Verifications
    if state.verifications:
        passed = sum(1 for v in state.verifications.values() if v.status == "passed")
        lines.append(f"## Verifications: {passed}/{len(state.verifications)} passing")
        for v in state.verifications.values():
            lines.append(f"- {v.verification_id} [{v.status}] ({v.category})")
            if v.status == "failed" and v.last_error:
                error_preview = v.last_error[:500]
                lines.append(f"  Last error: {error_preview}")
        lines.append("")

    # VRC
    vrc = state.latest_vrc
    if vrc:
        lines.append(f"## Latest VRC: {vrc.value_score:.0%} value | {vrc.recommendation}")
        lines.append(f"  {vrc.summary}")
        if vrc.gaps:
            for gap in vrc.gaps[:5]:
                lines.append(f"  Gap: {gap.get('description', '')}")
        lines.append("")

    return "\n".join(lines)


def _format_budget_warning(config: LoopConfig, state: LoopState) -> str:
    """Generate budget warning text for builder prompt."""
    remaining = config.max_iterations - state.iteration
    if remaining <= config.max_iterations * 0.2:
        return f"WARNING: Only {remaining} iterations remaining out of {config.max_iterations}. Focus on completing critical tasks and generating verifications."
    if config.token_budget and state.total_tokens_used > config.token_budget * 0.8:
        pct = state.total_tokens_used / config.token_budget * 100
        return f"WARNING: {pct:.0f}% of token budget consumed. Economize."
    return "Budget is healthy. Proceed normally."


# ---------------------------------------------------------------------------
# Core loop
# ---------------------------------------------------------------------------

def run_loop(config: LoopConfig, state: LoopState, agent: Agent) -> None:
    """The main loop: iterate phases until value is delivered or budget exhausted."""
    lock_path = config.sprint_dir / ".loop.lock"
    if not _acquire_lock(lock_path):
        raise RuntimeError(f"Another loop instance is running (lock: {lock_path})")

    try:
        print("\n" + "=" * 60)
        print("  TELIC LOOP V4")
        print("=" * 60)

        from .git import git_commit

        start_iter = max(state.iteration + 1, 1)
        for iteration in range(start_iter, start_iter + config.max_iterations):
            state.iteration = iteration

            # Hard limits
            if config.token_budget and state.total_tokens_used > config.token_budget:
                print(f"  TOKEN BUDGET EXHAUSTED ({state.total_tokens_used:,} tokens)")
                break

            phase = determine_phase(state)
            if phase == "complete":
                print("\n  VALUE DELIVERED — all gates passed")
                state.pass_gate("exit_gate")
                generate_delivery_report(config, state)
                state.save(config.state_file)
                return

            print(f"\n── Iteration {iteration} ── Phase: {phase}")

            # Timing + token tracking
            inp_before = state.total_input_tokens
            out_before = state.total_output_tokens
            t0 = time.perf_counter()

            crash_record = None
            progress = False
            try:
                if phase == "plan":
                    progress = _run_plan_phase(config, state, agent)
                elif phase == "review":
                    progress = _run_review_phase(config, state, agent)
                elif phase == "implement":
                    progress = _run_implement_phase(config, state, agent)
                elif phase == "evaluate":
                    progress = _run_evaluate_phase(config, state, agent)

            except RateLimitError as rle:
                wait_secs = parse_rate_limit_wait_seconds(rle)
                print(f"\n  RATE LIMIT HIT — sleeping {wait_secs // 60}m...")
                state.save(config.state_file)
                time.sleep(wait_secs)
                continue

            except Exception as exc:
                crash_record = _log_iteration_crash(config, state, phase, exc, iteration)

            elapsed = round(time.perf_counter() - t0, 1)
            phase_inp = state.total_input_tokens - inp_before
            phase_out = state.total_output_tokens - out_before
            result_str = "crash" if crash_record else ("progress" if progress else "no_progress")
            state.record_progress(
                phase, result_str, progress,
                input_tokens=phase_inp,
                output_tokens=phase_out,
                duration_sec=elapsed,
                crash_type=crash_record.get("crash_type", "") if crash_record else "",
            )

            # Git commit after implement phases
            if phase == "implement" and progress:
                git_commit(config, state, f"telic-loop({config.sprint}): iter {iteration}")

            # Render artifacts
            render_value_checklist(config, state)
            if state.tasks:
                render_plan_snapshot(config, state)

            state.save(config.state_file)

        # Max iterations reached
        print("\n  MAX ITERATIONS REACHED — generating partial delivery report")
        generate_delivery_report(config, state)

    finally:
        _release_lock(lock_path)


def _log_iteration_crash(
    config: LoopConfig, state: LoopState,
    phase: str, exc: Exception, iteration: int,
) -> dict:
    """Log a crash during a loop iteration and reset in_progress tasks."""
    from datetime import datetime
    import traceback

    print(f"\n  CRASH in {phase}: {type(exc).__name__}: {exc}")
    traceback.print_exc()

    crash_record = {
        "timestamp": datetime.now().isoformat(),
        "crash_type": type(exc).__name__,
        "phase": phase,
        "iteration": iteration,
        "error": f"{type(exc).__name__}: {str(exc)[:200]}",
    }
    state.crash_log.append(crash_record)

    # Reset any in_progress tasks back to pending
    for task in state.tasks.values():
        if task.status == "in_progress":
            task.status = "pending"
    state.save(config.state_file)

    return crash_record


# ---------------------------------------------------------------------------
# Infrastructure helpers
# ---------------------------------------------------------------------------

_lock_refcount: dict[str, int] = {}


def _acquire_lock(lock_path: Path) -> bool:
    """Acquire a file-based lock. Re-entrant for the same process."""
    key = str(lock_path.resolve())
    if key in _lock_refcount:
        _lock_refcount[key] += 1
        return True

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        _lock_refcount[key] = 1
        return True
    except FileExistsError:
        try:
            pid = int(lock_path.read_text(encoding="utf-8").strip())
            if pid == os.getpid():
                _lock_refcount[key] = 1
                return True
            try:
                os.kill(pid, 0)
                return False
            except OSError:
                lock_path.unlink(missing_ok=True)
                return _acquire_lock(lock_path)
        except (ValueError, OSError):
            lock_path.unlink(missing_ok=True)
            return _acquire_lock(lock_path)


def _release_lock(lock_path: Path) -> None:
    """Release file-based lock."""
    key = str(lock_path.resolve())
    count = _lock_refcount.get(key, 0)
    if count > 1:
        _lock_refcount[key] = count - 1
        return
    _lock_refcount.pop(key, None)
    lock_path.unlink(missing_ok=True)


def _ensure_git_repo(config: LoopConfig) -> None:
    """Ensure we're in a git repository."""
    import subprocess
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("ERROR: Not inside a git repository. Initialize one with 'git init'.")
        sys.exit(1)


def _recover_interrupted_rollback(config: LoopConfig, state: LoopState) -> None:
    """Recover from WAL if a rollback was interrupted."""
    wal_path = config.state_file.with_suffix(".rollback_wal")
    if not wal_path.exists():
        return

    print("  WARNING: Recovering from interrupted rollback...")
    try:
        wal_data = json.loads(wal_path.read_text(encoding="utf-8"))
        if wal_data.get("status") == "started":
            import subprocess
            subprocess.run(
                ["git", "reset", "--hard", wal_data["to_hash"]],
                check=True,
            )
            subprocess.run(["git", "clean", "-fd"], check=True)
            state.git.last_commit_hash = wal_data["to_hash"]
            print(f"  Recovered: reset to {wal_data['to_hash'][:8]}")
    except Exception as e:
        print(f"  WARNING: Could not recover from WAL: {e}")
    finally:
        wal_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point with crash recovery."""
    max_restarts = 3
    for attempt in range(1, max_restarts + 1):
        try:
            _run_main()
            return
        except SystemExit:
            raise
        except Exception as exc:
            print(f"\n{'=' * 60}")
            print(f"  LOOP CRASHED (attempt {attempt}/{max_restarts})")
            import traceback
            traceback.print_exc()
            print(f"{'=' * 60}")
            if attempt < max_restarts:
                wait = 10 * attempt
                print(f"  Restarting in {wait} seconds...")
                time.sleep(wait)
            else:
                print("  Max restarts reached.")
                sys.exit(1)


def _run_main() -> None:
    """Core loop logic — called by main() with crash recovery."""
    from .git import ensure_gitignore, setup_sprint_branch

    if len(sys.argv) < 2:
        print("Usage: telic-loop <sprint-name> [--sprint-dir <path>] [--project-dir <path>]")
        sys.exit(1)

    sprint = sys.argv[1]
    sprint_dir = Path(f"sprints/{sprint}")
    project_dir: Path | None = None

    if "--sprint-dir" in sys.argv:
        idx = sys.argv.index("--sprint-dir")
        if idx + 1 < len(sys.argv):
            sprint_dir = Path(sys.argv[idx + 1])

    if "--project-dir" in sys.argv:
        idx = sys.argv.index("--project-dir")
        if idx + 1 < len(sys.argv):
            project_dir = Path(sys.argv[idx + 1])

    config = LoopConfig(
        sprint=sprint, sprint_dir=sprint_dir, project_dir=project_dir,
    )

    config.sprint_dir.mkdir(parents=True, exist_ok=True)

    lock_path = config.sprint_dir / ".loop.lock"
    lock = _acquire_lock(lock_path)
    if not lock:
        print(f"ERROR: Another loop instance is running (lock: {lock_path})")
        sys.exit(1)

    try:
        _ensure_git_repo(config)
        ensure_gitignore(config.sprint_dir)

        if config.state_file.exists():
            state = LoopState.load(config.state_file)
            print(f"Resuming sprint '{sprint}' at iteration {state.iteration}")
        else:
            state = LoopState(sprint=sprint)
            print(f"Starting new sprint: '{sprint}'")

        _recover_interrupted_rollback(config, state)

        state.max_task_description_chars = config.max_task_description_chars
        state.max_files_per_task = config.max_files_per_task

        agent = Agent(config, state)

        if not state.git.branch_name:
            setup_sprint_branch(config, state)

        state.save(config.state_file)
        run_loop(config, state, agent)

        if state.value_delivered:
            sys.exit(0)
        elif state.latest_vrc and state.latest_vrc.value_score > 0.5:
            sys.exit(2)
        else:
            sys.exit(1)

    finally:
        _release_lock(lock_path)


if __name__ == "__main__":
    main()
