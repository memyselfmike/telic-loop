"""E2E test runner for telic-loop V4. Runs a real sprint against the API."""

import os
import sys
from pathlib import Path

# Unbuffered output so prints appear immediately when run from a parent process
os.environ["PYTHONUNBUFFERED"] = "1"

# Allow nested Claude Code sessions
os.environ.pop("CLAUDECODE", None)

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from telic_loop.agent import Agent
from telic_loop.config import LoopConfig
from telic_loop.git import ensure_gitignore, setup_sprint_branch
from telic_loop.main import determine_phase, run_loop
from telic_loop.state import LoopState


def _run():
    sprint = sys.argv[1] if len(sys.argv) > 1 else "temp-calc"
    sprint_dir = Path(f"sprints/{sprint}")

    generate_docs = "--no-docs" not in sys.argv

    config = LoopConfig(
        sprint=sprint,
        sprint_dir=sprint_dir,
        max_iterations=80,
        max_fix_attempts=3,
        token_budget=0,
        generate_docs=generate_docs,
    )

    config.sprint_dir.mkdir(parents=True, exist_ok=True)

    if config.state_file.exists():
        state = LoopState.load(config.state_file)
        print(f"Resuming sprint '{sprint}' at iteration {state.iteration}, phase={determine_phase(state)}")
    else:
        state = LoopState(sprint=sprint)
        print(f"Starting new sprint: '{sprint}'")

    agent = Agent(config, state)
    ensure_gitignore(config.sprint_dir)

    if not state.git.branch_name:
        setup_sprint_branch(config, state)

    state.save(config.state_file)
    run_loop(config, state, agent)

    # Report results
    print("\n" + "=" * 60)
    print("  E2E TEST RESULTS")
    print("=" * 60)
    print(f"  Phase: {determine_phase(state)}")
    print(f"  Iterations: {state.iteration}")
    print(f"  Tasks: {len(state.tasks)}")
    for tid, task in state.tasks.items():
        print(f"    {tid}: [{task.status}] {task.description[:80]}")
    print(f"  VRC snapshots: {len(state.vrc_history)}")
    if state.latest_vrc:
        vrc = state.latest_vrc
        print(f"  Latest VRC: {vrc.value_score:.0%} value | {vrc.recommendation}")
    print(f"  Tokens used: {state.total_tokens_used:,}")
    print(f"  Value delivered: {state.value_delivered}")

    state.save(config.state_file)


def main():
    import time
    import traceback
    from telic_loop.errors import backoff_seconds, classify_error, log_crash_jsonl

    sprint = sys.argv[1] if len(sys.argv) > 1 else "temp-calc"
    sprint_dir = Path(f"sprints/{sprint}")

    max_restarts = 3
    for attempt in range(1, max_restarts + 1):
        try:
            _run()
            return
        except SystemExit:
            raise
        except Exception as exc:
            error_kind = classify_error(exc)
            print(f"\n{'=' * 60}")
            print(f"  E2E RUNNER CRASHED (attempt {attempt}/{max_restarts}) [{error_kind}]")
            traceback.print_exc()
            print(f"{'=' * 60}")

            log_crash_jsonl(
                sprint_dir / ".crash_log.jsonl",
                error=exc,
                phase="e2e_runner",
                iteration=0,
                error_kind=error_kind,
                extra={"restart_attempt": attempt},
            )

            if attempt < max_restarts:
                wait = backoff_seconds(attempt - 1, base=5.0, cap=60.0)
                print(f"  Restarting in {wait:.0f} seconds...")
                time.sleep(wait)
            else:
                print("  Max restarts reached.")
                sys.exit(1)


if __name__ == "__main__":
    main()
