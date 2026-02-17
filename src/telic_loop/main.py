"""Entry point: pre-loop -> value loop (with exit gate)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .claude import Claude
from .config import LoopConfig
from .decision import Action, decide_next_action
from .render import generate_delivery_report, render_value_checklist
from .state import LoopState


def run_value_loop(
    config: LoopConfig, state: LoopState, claude: Claude,
    *,
    inside_epic_loop: bool = False,
) -> None:
    """The Value Loop: iterate until value is delivered or budget exhausted."""
    from .phases.coherence import quick_coherence_check
    from .phases.course_correct import do_course_correct
    from .phases.critical_eval import do_critical_eval
    from .phases.execute import do_execute, do_service_fix
    from .phases.exit_gate import do_exit_gate
    from .phases.pause import do_interactive_pause
    from .phases.plan_health import maybe_run_plan_health_check
    from .phases.process_monitor import maybe_run_strategy_reasoner
    from .phases.qc import do_fix, do_generate_qc, do_run_qc
    from .phases.research import do_research
    from .phases.vrc import run_vrc
    from .phases.coherence import do_full_coherence_eval

    print("\n" + "=" * 60)
    print("  THE VALUE LOOP")
    print("=" * 60)

    ACTION_HANDLERS = {
        Action.EXECUTE: do_execute,
        Action.GENERATE_QC: do_generate_qc,
        Action.RUN_QC: do_run_qc,
        Action.FIX: do_fix,
        Action.CRITICAL_EVAL: do_critical_eval,
        Action.COURSE_CORRECT: do_course_correct,
        Action.SERVICE_FIX: do_service_fix,
        Action.RESEARCH: do_research,
        Action.COHERENCE_EVAL: do_full_coherence_eval,
        Action.INTERACTIVE_PAUSE: do_interactive_pause,
    }

    start_iter = max(state.iteration + 1, 1)
    for iteration in range(start_iter, start_iter + config.max_loop_iterations):
        state.iteration = iteration

        # Budget check
        if config.token_budget and state.total_tokens_used > config.token_budget:
            print(f"TOKEN BUDGET EXHAUSTED ({state.total_tokens_used:,} tokens)")
            break

        # Budget-aware action gating
        budget_pct = (
            (state.total_tokens_used / config.token_budget * 100)
            if config.token_budget else 0
        )

        action = decide_next_action(config, state)

        if budget_pct >= 95:
            print(f"  BUDGET CRITICAL: {budget_pct:.0f}% consumed — completing current work only")
            if action not in (
                Action.FIX, Action.RUN_QC, Action.EXIT_GATE,
                Action.INTERACTIVE_PAUSE,
            ):
                action = Action.EXIT_GATE
        elif budget_pct >= 80:
            print(f"  BUDGET WARNING: {budget_pct:.0f}% consumed — economizing")

        print(f"\n── Iteration {iteration} ── Action: {action.value}")

        # Exit gate is special — it can terminate the loop
        if action == Action.EXIT_GATE:
            exit_passed = do_exit_gate(config, state, claude)
            if exit_passed:
                if not inside_epic_loop:
                    # Only generate delivery report for single-run sprints.
                    # Epic loop generates its own report after all epics complete.
                    generate_delivery_report(config, state)
                print("\n  VALUE DELIVERED — exit gate passed")
                state.save(config.state_file)
                return
            progress = True
        else:
            handler = ACTION_HANDLERS.get(action)
            if handler:
                progress = handler(config, state, claude)
            else:
                print(f"  WARNING: No handler for action {action.value}")
                progress = False

        state.record_progress(action.value, "progress" if progress else "no_progress", progress)

        # Process monitor (after every action)
        maybe_run_strategy_reasoner(
            state, config, claude, action=action.value, made_progress=progress,
        )

        # Plan health check — force after course correction
        if action == Action.COURSE_CORRECT and progress:
            maybe_run_plan_health_check(config, state, claude, force=True)
        else:
            maybe_run_plan_health_check(config, state, claude)

        # VRC heartbeat and coherence check — skip during pause and after exit gate
        # (exit gate runs its own fresh VRC; pause should not burn tokens)
        if state.pause is None and action != Action.EXIT_GATE:
            # Force full VRC after critical eval or course correction
            force_full_vrc = action in (Action.CRITICAL_EVAL, Action.COURSE_CORRECT)
            vrc = run_vrc(config, state, claude, force_full=force_full_vrc)
            print(
                f"  VRC #{len(state.vrc_history)}: {vrc.value_score:.0%} value | "
                f"{vrc.deliverables_verified}/{vrc.deliverables_total} | "
                f"→ {vrc.recommendation}"
            )

            # Quick coherence check
            quick_coherence_check(config, state)

        # Render updated value checklist
        render_value_checklist(config, state)

        state.save(config.state_file)

    print("\n  MAX ITERATIONS REACHED — generating partial delivery report")
    generate_delivery_report(config, state)


def main() -> None:
    """CLI entry point."""
    from .git import ensure_gitignore, setup_sprint_branch

    if len(sys.argv) < 2:
        print("Usage: telic-loop <sprint-name> [--sprint-dir <path>]")
        sys.exit(1)

    sprint = sys.argv[1]
    sprint_dir = Path(f"sprints/{sprint}")

    # Parse optional --sprint-dir
    if "--sprint-dir" in sys.argv:
        idx = sys.argv.index("--sprint-dir")
        if idx + 1 < len(sys.argv):
            sprint_dir = Path(sys.argv[idx + 1])

    config = LoopConfig(sprint=sprint, sprint_dir=sprint_dir)

    # Ensure sprint directory exists
    config.sprint_dir.mkdir(parents=True, exist_ok=True)

    # Acquire lock
    lock_path = config.sprint_dir / ".loop.lock"
    lock = _acquire_lock(lock_path)
    if not lock:
        print(f"ERROR: Another loop instance is running (lock: {lock_path})")
        sys.exit(1)

    try:
        # Ensure git repo
        _ensure_git_repo(config)

        # Auto-maintain .gitignore
        ensure_gitignore(config.sprint_dir)

        # Load or create state
        if config.state_file.exists():
            state = LoopState.load(config.state_file)
            print(f"Resuming sprint '{sprint}' at phase={state.phase}, iteration={state.iteration}")
        else:
            state = LoopState(sprint=sprint)
            print(f"Starting new sprint: '{sprint}'")

        # Recover from interrupted rollback
        _recover_interrupted_rollback(config, state)

        # Create Claude factory
        claude = Claude(config, state)

        # Setup git branch
        if not state.git.branch_name:
            setup_sprint_branch(config, state)

        # Run phases
        if state.phase == "pre_loop":
            from .phases.preloop import run_preloop
            if not run_preloop(config, state, claude):
                print("\nPRE-LOOP FAILED — cannot proceed.")
                sys.exit(1)

        if state.phase == "value_loop":
            from .phases.epic import run_epic_loop
            if state.vision_complexity == "multi_epic" and state.epics:
                run_epic_loop(config, state, claude)
            else:
                run_value_loop(config, state, claude)

        # Exit code based on delivery
        if state.value_delivered:
            sys.exit(0)
        elif state.latest_vrc and state.latest_vrc.value_score > 0.5:
            sys.exit(2)  # partial
        else:
            sys.exit(1)

    finally:
        _release_lock(lock_path)


# ---------------------------------------------------------------------------
# Infrastructure helpers
# ---------------------------------------------------------------------------

def _acquire_lock(lock_path: Path) -> bool:
    """Acquire a file-based lock. Returns True if acquired."""
    import os

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        # Check if the PID in the lock file is still running
        try:
            pid = int(lock_path.read_text().strip())
            try:
                os.kill(pid, 0)  # Check if process exists
                return False  # Process still running
            except OSError:
                # Stale lock — remove and retry
                lock_path.unlink(missing_ok=True)
                return _acquire_lock(lock_path)
        except (ValueError, OSError):
            # Corrupt lock file — remove and retry
            lock_path.unlink(missing_ok=True)
            return _acquire_lock(lock_path)


def _release_lock(lock_path: Path) -> None:
    """Release file-based lock."""
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
        wal_data = json.loads(wal_path.read_text())
        if wal_data.get("status") == "started":
            import subprocess
            # Complete the interrupted reset
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


if __name__ == "__main__":
    main()
