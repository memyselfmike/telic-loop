"""E2E test runner for telic-loop. Runs a real sprint against the API."""

import os
import sys
from pathlib import Path

# Allow nested Claude Code sessions
os.environ.pop("CLAUDECODE", None)

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from telic_loop.claude import Claude
from telic_loop.config import LoopConfig
from telic_loop.git import ensure_gitignore, setup_sprint_branch
from telic_loop.state import LoopState


def main():
    sprint = "temp-calc"
    sprint_dir = Path("sprints/temp-calc")

    config = LoopConfig(
        sprint=sprint,
        sprint_dir=sprint_dir,
        max_loop_iterations=20,  # Keep it bounded for testing
        max_fix_attempts=3,
        token_budget=0,  # Unlimited for now
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

    # Setup git branch (skip for e2e test to keep things simple)
    # setup_sprint_branch(config, state)

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
        print(f"    {tid}: [{task.status}] {task.description[:60]}")
    print(f"  VRC snapshots: {len(state.vrc_history)}")
    if state.latest_vrc:
        vrc = state.latest_vrc
        print(f"  Latest VRC: {vrc.value_score:.0%} value | {vrc.recommendation}")
    print(f"  Tokens used: {state.total_tokens_used:,}")
    print(f"  Value delivered: {state.value_delivered}")

    # Check if the output exists
    temp_calc = sprint_dir / "temp_calc.py"
    if temp_calc.exists():
        print(f"\n  temp_calc.py EXISTS ({temp_calc.stat().st_size} bytes)")
        # Try running the acceptance tests
        import subprocess
        tests = [
            (["python", str(temp_calc), "100", "C", "F"], "212"),
            (["python", str(temp_calc), "32", "F", "C"], "0"),
            (["python", str(temp_calc), "0", "K", "C"], "-273.15"),
        ]
        for cmd, expected in tests:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            output = result.stdout.strip()
            passed = expected in output
            mark = "PASS" if passed else "FAIL"
            print(f"  [{mark}] {' '.join(cmd[-3:])} -> {output} (expected {expected})")
    else:
        print(f"\n  temp_calc.py NOT FOUND")

    state.save(config.state_file)


if __name__ == "__main__":
    main()
