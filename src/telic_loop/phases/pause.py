"""Interactive Pause: human action needed."""

from __future__ import annotations

import subprocess
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


def do_interactive_pause(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Handle interactive pause — wait for human action and verify."""
    from ..state import PauseState

    if state.pause is not None:
        # Resuming — verify human's action
        if _verify_human_action(state.pause.verification, config):
            print("  Human action verified — resuming")
            for task in state.tasks.values():
                if task.status == "blocked" and task.blocked_reason.startswith("HUMAN_ACTION:"):
                    task.status = "pending"
                    task.blocked_reason = ""
            state.pause = None
            return True
        else:
            print(f"  Not yet completed. Instructions: {state.pause.instructions}")
            input("  Press Enter when ready...")
            return False

    # First time — set up pause
    human_blocked = [
        t for t in state.tasks.values()
        if t.status == "blocked" and t.blocked_reason.startswith("HUMAN_ACTION:")
    ]
    if not human_blocked:
        return False

    task = human_blocked[0]
    action_needed = task.blocked_reason.replace("HUMAN_ACTION:", "").strip()

    state.pause = PauseState(
        reason=action_needed,
        instructions=action_needed,
        verification=task.acceptance or "",
        requested_at=datetime.now().isoformat(),
    )
    print(f"\n  {'=' * 50}")
    print("  INTERACTIVE PAUSE — Human action needed")
    print(f"  {'=' * 50}")
    print(f"  {action_needed}")
    state.save(config.state_file)
    input("  Press Enter when done...")
    return False


def _verify_human_action(verification: str, config: LoopConfig) -> bool:
    """Run verification command for human action.

    Uses shell=True because verification commands are defined by the orchestrator
    (from task acceptance criteria), not by untrusted LLM output.
    """
    if not verification:
        return True
    try:
        result = subprocess.run(
            verification, shell=True, capture_output=True, timeout=30,
            cwd=str(config.sprint_dir),
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
