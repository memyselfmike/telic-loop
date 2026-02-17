"""E2E test runner for telic-loop. Runs a real sprint against the API."""

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

from telic_loop.claude import Claude
from telic_loop.config import LoopConfig
from telic_loop.git import ensure_gitignore
from telic_loop.state import LoopState


def main():
    # Default sprint or take from CLI
    sprint = sys.argv[1] if len(sys.argv) > 1 else "temp-calc"
    sprint_dir = Path(f"sprints/{sprint}")

    config = LoopConfig(
        sprint=sprint,
        sprint_dir=sprint_dir,
        max_loop_iterations=20,  # Keep it bounded for testing
        max_fix_attempts=3,
        token_budget=0,  # Unlimited for now
        epic_feedback_timeout_minutes=10,  # 10min break between epics
    )

    # Ensure sprint dir exists
    config.sprint_dir.mkdir(parents=True, exist_ok=True)

    # Load or create state
    if config.state_file.exists():
        state = LoopState.load(config.state_file)
        print(f"Resuming sprint '{sprint}' at phase={state.phase}, iteration={state.iteration}")
    else:
        state = LoopState(sprint=sprint)
        print(f"Starting new sprint: '{sprint}'")

    # Create Claude factory
    claude = Claude(config, state)

    # Auto-maintain .gitignore
    ensure_gitignore(config.sprint_dir)

    # Run phases
    if state.phase == "pre_loop":
        from telic_loop.phases.preloop import run_preloop
        print("\n" + "=" * 60)
        print("  STARTING PRE-LOOP")
        print("=" * 60)
        if not run_preloop(config, state, claude):
            print("\nPRE-LOOP FAILED — cannot proceed.")
            state.save(config.state_file)
            sys.exit(1)

    if state.phase == "value_loop":
        if state.vision_complexity == "multi_epic" and state.epics:
            from telic_loop.phases.epic import run_epic_loop
            run_epic_loop(config, state, claude)
        else:
            from telic_loop.main import run_value_loop
            run_value_loop(config, state, claude)

    # Report results
    print("\n" + "=" * 60)
    print("  E2E TEST RESULTS")
    print("=" * 60)
    print(f"  Phase: {state.phase}")
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

    # Check deliverables
    index_html = sprint_dir / "index.html"
    if index_html.exists():
        print(f"\n  index.html EXISTS ({index_html.stat().st_size} bytes)")

    test_files = list(sprint_dir.glob("test_*.py"))
    if test_files:
        print(f"  Test files: {[f.name for f in test_files]}")
        import subprocess
        for tf in test_files:
            result = subprocess.run(
                ["python", "-m", "pytest", str(tf), "-v", "--timeout=30"],
                capture_output=True, text=True, timeout=120,
                cwd=str(sprint_dir),
            )
            print(f"\n  pytest {tf.name}:")
            for line in result.stdout.splitlines()[-15:]:
                print(f"    {line}")
            if result.returncode != 0 and result.stderr:
                for line in result.stderr.splitlines()[-5:]:
                    print(f"    STDERR: {line}")

    state.save(config.state_file)


if __name__ == "__main__":
    main()
