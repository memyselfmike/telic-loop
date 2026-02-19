"""Runner for beep2b sprint with crash recovery."""
import sys
import os
import time
import traceback

os.environ["PYTHONUNBUFFERED"] = "1"
os.environ.pop("CLAUDECODE", None)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
from telic_loop.claude import Claude
from telic_loop.config import LoopConfig
from telic_loop.git import ensure_gitignore
from telic_loop.state import LoopState

sprint = "beep2b"
sprint_dir = Path(f"sprints/{sprint}")

config = LoopConfig(
    sprint=sprint,
    sprint_dir=sprint_dir,
    max_loop_iterations=60,
    max_fix_attempts=3,
    token_budget=0,
    epic_feedback_timeout_minutes=10,
    sdk_query_timeout_sec=600,
)

config.sprint_dir.mkdir(parents=True, exist_ok=True)

max_restarts = 3
for attempt in range(1, max_restarts + 1):
    try:
        if config.state_file.exists():
            state = LoopState.load(config.state_file)
            print(f"Resuming sprint at phase={state.phase}, iteration={state.iteration}")
        else:
            state = LoopState(sprint=sprint)
            print(f"Starting new sprint: {sprint}")

        claude = Claude(config, state)
        ensure_gitignore(config.sprint_dir)

        if state.phase == "pre_loop":
            from telic_loop.phases.preloop import run_preloop
            if not run_preloop(config, state, claude):
                print("PRE-LOOP FAILED")
                state.save(config.state_file)
                sys.exit(1)

        if state.phase == "value_loop":
            if state.vision_complexity == "multi_epic" and state.epics:
                from telic_loop.phases.epic import run_epic_loop
                run_epic_loop(config, state, claude)
            else:
                from telic_loop.main import run_value_loop
                run_value_loop(config, state, claude)

        # Clean exit
        sep = "=" * 60
        print(f"\n{sep}")
        print("  SPRINT COMPLETE")
        print(sep)
        print(f"  Iterations: {state.iteration}")
        print(f"  Tokens: {state.total_tokens_used:,}")
        if state.latest_vrc:
            print(f"  VRC: {state.latest_vrc.value_score:.0%} value")
        state.save(config.state_file)
        break

    except SystemExit:
        raise
    except Exception as exc:
        sep = "=" * 60
        print(f"\n{sep}")
        print(f"  LOOP CRASHED (attempt {attempt}/{max_restarts})")
        print(f"  Error: {exc}")
        traceback.print_exc()
        print(sep)
        if attempt < max_restarts:
            wait = 10 * attempt
            print(f"  Restarting in {wait}s...")
            time.sleep(wait)
        else:
            print("  Max restarts reached.")
            sys.exit(1)
