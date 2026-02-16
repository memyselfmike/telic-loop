"""Vision Reality Check: the heartbeat."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState, VRCSnapshot


def run_vrc(
    config: LoopConfig, state: LoopState, claude: Claude,
    force_full: bool = False,
) -> VRCSnapshot:
    """Vision Reality Check. Full VRC (Opus) or Quick VRC (Haiku).

    Full VRC runs every 5th iteration, first 3 iterations, after course
    correction, and at exit gate. Quick VRC all other iterations.
    """
    from ..claude import AgentRole, load_prompt
    from ..render import render_plan_markdown
    from ..state import VRCSnapshot

    is_full_vrc = (
        force_full
        or (state.iteration % 5 == 0)
        or (state.iteration <= 3)
    )

    # Budget > 80%: force quick VRC to save tokens
    if config.token_budget:
        budget_pct = state.total_tokens_used / config.token_budget * 100
        if budget_pct >= 80 and not force_full:
            is_full_vrc = False

    if is_full_vrc:
        session = claude.session(
            AgentRole.REASONER,
            system_extra=(
                "You are evaluating progress toward VISION delivery. "
                "This is a FULL VRC — thoroughly assess value delivery quality."
            ),
        )
    else:
        session = claude.session(AgentRole.CLASSIFIER)

    prompt = load_prompt("vrc",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        IS_FULL_VRC="FULL" if is_full_vrc else "QUICK",
        ITERATION=state.iteration,
        VISION=config.vision_file.read_text() if config.vision_file.exists() else "",
        PLAN=render_plan_markdown(state),
        TASK_SUMMARY=build_task_summary(state),
        PREVIOUS_VRC=format_latest_vrc(state),
    )

    vrc_count_before = len(state.vrc_history)
    session.send(prompt)

    # Fallback if agent didn't call report_vrc
    if len(state.vrc_history) == vrc_count_before:
        done = len([t for t in state.tasks.values() if t.status == "done"])
        total = len(state.tasks) or 1
        snapshot = VRCSnapshot(
            iteration=state.iteration,
            timestamp=datetime.now().isoformat(),
            deliverables_total=total,
            deliverables_verified=done,
            deliverables_blocked=len([t for t in state.tasks.values() if t.status == "blocked"]),
            value_score=done / total,
            gaps=[],
            recommendation="CONTINUE",
            summary=f"Fallback VRC: {done}/{total} tasks done",
        )
        state.vrc_history.append(snapshot)

    return state.vrc_history[-1]


def do_vrc_heartbeat(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Run VRC heartbeat during the value loop."""
    run_vrc(config, state, claude)
    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_task_summary(state: LoopState) -> str:
    """Brief task status for VRC and other agents."""
    lines: list[str] = []
    done = len([t for t in state.tasks.values() if t.status == "done"])
    total = len(state.tasks)
    blocked = len([t for t in state.tasks.values() if t.status == "blocked"])
    lines.append(f"Tasks: {done}/{total} complete, {blocked} blocked")

    passed = len([v for v in state.verifications.values() if v.status == "passed"])
    failed = len([v for v in state.verifications.values() if v.status == "failed"])
    lines.append(f"QC checks: {passed}/{len(state.verifications)} passing, {failed} failing")

    recent = state.progress_log[-5:]
    if recent:
        lines.append("Recent actions:")
        for entry in recent:
            lines.append(f"  [{entry['iteration']}] {entry['action']}: {entry['result']}")

    return "\n".join(lines)


def format_latest_vrc(state: LoopState) -> str:
    """Format the most recent VRC snapshot for context."""
    if not state.vrc_history:
        return "No previous VRC."
    vrc = state.vrc_history[-1]
    return (
        f"Iteration {vrc.iteration}: {vrc.value_score:.0%} value | "
        f"{vrc.deliverables_verified}/{vrc.deliverables_total} verified | "
        f"{vrc.recommendation}\n"
        f"Summary: {vrc.summary}\n"
        f"Gaps: {len(vrc.gaps)}"
    )
