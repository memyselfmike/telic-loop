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

    # Epic scoping: in multi-epic mode, VRC evaluates the current epic's
    # deliverables, not the full Vision. This prevents the exit gate from
    # passing prematurely on partial Vision delivery.
    epic_scope = ""
    if (state.vision_complexity == "multi_epic"
            and state.epics
            and state.current_epic_index < len(state.epics)):
        epic = state.epics[state.current_epic_index]
        epic_scope = (
            f"\n\n## EPIC SCOPE — Evaluate ONLY this epic's deliverables:\n"
            f"Epic {state.current_epic_index + 1}/{len(state.epics)}: {epic.title}\n"
            f"Value: {epic.value_statement}\n"
            f"Deliverables:\n"
            + "\n".join(f"- {d}" for d in epic.deliverables)
            + f"\nCompletion Criteria:\n"
            + "\n".join(f"- {c}" for c in epic.completion_criteria)
            + f"\n\nIMPORTANT: Score deliverables_total and deliverables_verified "
            f"against THIS EPIC's {len(epic.deliverables)} deliverables, "
            f"not the full Vision. Set SHIP_READY only when all of this epic's "
            f"completion criteria are met."
        )

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
        EPIC_SCOPE=epic_scope,
    )

    vrc_count_before = len(state.vrc_history)
    session.send(prompt)

    # Fallback if agent didn't call report_vrc
    if len(state.vrc_history) == vrc_count_before:
        # Use the previous VRC's deliverables baseline (Vision-based) if available,
        # NOT task counts — task completion ≠ value delivery.
        prev = state.vrc_history[-1] if state.vrc_history else None
        if prev:
            # Carry forward previous VRC scores — we can't improve on them without
            # a real evaluation. This prevents phantom score jumps from task counting.
            snapshot = VRCSnapshot(
                iteration=state.iteration,
                timestamp=datetime.now().isoformat(),
                deliverables_total=prev.deliverables_total,
                deliverables_verified=prev.deliverables_verified,
                deliverables_blocked=prev.deliverables_blocked,
                value_score=prev.value_score,
                gaps=prev.gaps,
                recommendation=prev.recommendation,
                summary=f"Fallback VRC: carried forward from iteration {prev.iteration} ({prev.value_score:.0%})",
            )
        else:
            snapshot = VRCSnapshot(
                iteration=state.iteration,
                timestamp=datetime.now().isoformat(),
                deliverables_total=0,
                deliverables_verified=0,
                deliverables_blocked=0,
                value_score=0.0,
                gaps=[],
                recommendation="CONTINUE",
                summary="Fallback VRC: no previous evaluation available",
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
