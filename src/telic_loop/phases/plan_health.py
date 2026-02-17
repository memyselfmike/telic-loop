"""Mid-loop plan quality validation (Layer 2)."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


def maybe_run_plan_health_check(
    config: LoopConfig, state: LoopState, claude: Claude,
    force: bool = False,
) -> None:
    """Check plan quality when mid-loop task count exceeds threshold."""
    from ..claude import AgentRole, load_prompt
    from ..render import render_plan_markdown
    from .process_monitor import format_code_health

    should_run = (
        force
        or state.mid_loop_tasks_since_health_check >= config.plan_health_after_n_tasks
    )
    if not should_run:
        return

    mid_loop_tasks = [
        t for t in state.tasks.values()
        if t.source != "plan" and not t.health_checked
    ]
    if not mid_loop_tasks:
        state.mid_loop_tasks_since_health_check = 0
        return

    print(f"\n  PLAN HEALTH CHECK — reviewing {len(mid_loop_tasks)} mid-loop tasks")

    session = claude.session(
        AgentRole.REASONER,
        system_extra=(
            "You are a plan quality reviewer. Check new tasks "
            "against existing plan for DRY violations, contradictions, "
            "SOLID breaches, dependency issues, and scope drift."
        ),
    )

    delta_summary = "\n".join(
        f"  [{t.task_id}] (source: {t.source}) {t.description}\n"
        f"    value: {t.value}\n    acceptance: {t.acceptance}\n"
        f"    deps: {t.dependencies}"
        for t in mid_loop_tasks
    )
    existing_summary = "\n".join(
        f"  [{t.task_id}] ({t.status}) {t.description}"
        for t in state.tasks.values()
        if t.source == "plan" and t.status != "descoped"
    )

    prompt = load_prompt("plan_health_check",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        PRD=config.prd_file.read_text() if config.prd_file.exists() else "",
        PLAN=render_plan_markdown(state),
        EXISTING_TASKS=existing_summary,
        NEW_TASKS=delta_summary,
        CODE_HEALTH=format_code_health(state),
    )
    session.send(prompt)

    for t in mid_loop_tasks:
        t.health_checked = True
    state.mid_loop_tasks_since_health_check = 0
