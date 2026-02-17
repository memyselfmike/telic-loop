"""Re-planning, descoping, restructuring."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


def do_course_correct(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Opus-driven course correction when the loop is stuck."""
    from ..claude import AgentRole, load_prompt
    from ..git import check_and_fix_services, execute_rollback, git_commit
    from ..render import render_plan_snapshot
    from ..state import PauseState
    from .process_monitor import format_code_health
    from .vrc import build_task_summary, format_latest_vrc

    session = claude.session(
        AgentRole.REASONER,
        system_extra=(
            "You are diagnosing WHY the value loop is stuck. "
            "Analyze attempts, identify root cause, recommend correction."
        ),
    )

    prompt = load_prompt("course_correct",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        VISION=config.vision_file.read_text() if config.vision_file.exists() else "",
        PRD=config.prd_file.read_text() if config.prd_file.exists() else "",
        PLAN=config.plan_file.read_text() if config.plan_file.exists() else "",
        TASK_SUMMARY=build_task_summary(state),
        VRC_HISTORY=_format_vrc_history(state),
        GIT_CHECKPOINTS=_format_git_checkpoints(state),
        STUCK_REASON=_format_stuck_reason(state),
        CODE_HEALTH=format_code_health(state),
    )

    state.agent_results.pop("course_correction", None)
    session.send(prompt)

    correction = state.agent_results.get("course_correction")
    if not correction:
        return False

    action = correction.get("action", "")

    if action == "restructure":
        state.iterations_without_progress = 0
        state.invalidate_tests()
        render_plan_snapshot(config, state)
        git_commit(config, state, f"telic-loop({config.sprint}): Course correction — restructured")
        return True

    if action == "descope":
        render_plan_snapshot(config, state)
        git_commit(config, state, f"telic-loop({config.sprint}): Descoped items")
        return True

    if action == "new_tasks":
        render_plan_snapshot(config, state)
        git_commit(config, state, f"telic-loop({config.sprint}): CC — added new tasks")
        return True

    if action == "rollback":
        label = correction.get("rollback_to_checkpoint", "")
        if not label:
            print("  ROLLBACK: No checkpoint label provided")
            return False
        checkpoint = next(
            (cp for cp in state.git.checkpoints if cp.label == label), None,
        )
        if not checkpoint:
            print(f"  ROLLBACK: Checkpoint '{label}' not found")
            return False
        if len(state.git.rollbacks) >= config.max_rollbacks_per_sprint:
            print(f"  ROLLBACK: Max rollbacks ({config.max_rollbacks_per_sprint}) exhausted")
            return False
        execute_rollback(config, state, checkpoint, correction["reason"])
        if state.context.services:
            check_and_fix_services(config, state)
        render_plan_snapshot(config, state)
        return True

    if action == "regenerate_tests":
        state.invalidate_tests()
        return True

    if action == "escalate":
        print(f"\n  ESCALATION: {correction['reason']}")
        state.pause = PauseState(
            reason=f"Escalation: {correction['reason']}",
            instructions=correction["reason"],
            requested_at=datetime.now().isoformat(),
        )
        return False

    return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_vrc_history(state: LoopState) -> str:
    """Format recent VRC history for agent context."""
    if not state.vrc_history:
        return "No VRC history yet."
    lines: list[str] = []
    for vrc in state.vrc_history[-10:]:
        lines.append(
            f"[Iter {vrc.iteration}] {vrc.value_score:.0%} value | "
            f"{vrc.deliverables_verified}/{vrc.deliverables_total} | "
            f"{vrc.recommendation}: {vrc.summary}"
        )
    return "\n".join(lines)


def _format_git_checkpoints(state: LoopState) -> str:
    """Format git checkpoints for course correction agent context."""
    if not state.git.checkpoints:
        return "No checkpoints yet."
    lines: list[str] = []
    for cp in state.git.checkpoints:
        lines.append(
            f"[{cp.label}] {cp.timestamp} | "
            f"hash: {cp.commit_hash[:8]} | "
            f"{len(cp.tasks_completed)} tasks done | "
            f"{len(cp.verifications_passing)} verifications passing | "
            f"value: {cp.value_score:.0%}"
        )
    return "\n".join(lines)


def _format_stuck_reason(state: LoopState) -> str:
    """Summarize why the loop is stuck based on state."""
    lines = [f"{state.iterations_without_progress} iterations without progress."]

    failing = [v for v in state.verifications.values() if v.status == "failed"]
    if failing:
        lines.append(f"Failing verifications ({len(failing)}):")
        for v in failing[:5]:
            lines.append(
                f"  - {v.verification_id}: "
                f"{v.last_error[:200] if v.last_error else 'unknown'} "
                f"({v.attempts} attempts)"
            )

    blocked = [t for t in state.tasks.values() if t.status == "blocked"]
    if blocked:
        lines.append(f"Blocked tasks ({len(blocked)}):")
        for t in blocked[:5]:
            lines.append(f"  - {t.task_id}: {t.blocked_reason}")

    recent = state.progress_log[-10:]
    if recent:
        lines.append("Recent progress log:")
        for entry in recent:
            lines.append(f"  [{entry['iteration']}] {entry['action']}: {entry['result']}")

    return "\n".join(lines)
