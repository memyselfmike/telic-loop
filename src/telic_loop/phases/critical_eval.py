"""Critical evaluation: use deliverable as real user (Evaluator agent)."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


def do_critical_eval(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Critical evaluation — Evaluator agent USES the deliverable as a real user.

    Not running tests. Not checking code. An agent EXPERIENCING the deliverable:
    - Does it make sense? Intuitive?
    - Data flows correctly end-to-end?
    - Would a real user figure this out without docs?
    - Delivers the EXPERIENCE promised by the Vision?
    """
    from ..claude import AgentRole, load_prompt
    from ..git import git_commit

    state.tasks_since_last_critical_eval = 0

    session = claude.session(
        AgentRole.EVALUATOR,
        system_extra=(
            "You are a demanding critical evaluator. USE the deliverable "
            "as the intended user would. Navigate the UI. Read the document. "
            "Run the tool. Report everything: what works, what's confusing, "
            "what's missing."
        ),
    )

    # Get recently completed tasks
    recent_tasks = [t for t in state.tasks.values() if t.status == "done" and t.completed_at]
    recent_tasks.sort(key=lambda t: t.completed_at, reverse=True)
    completed_summary = "\n".join(
        f"  [{t.task_id}] {t.description}\n"
        f"    Value: {t.value}\n"
        f"    Files: {', '.join(t.files_created + t.files_modified)}"
        for t in recent_tasks[:10]
    )

    prompt = load_prompt("critical_eval",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        COMPLETED_TASKS=completed_summary,
        VISION=config.vision_file.read_text() if config.vision_file.exists() else "",
    )

    session.send(prompt)

    # Findings arrive via report_eval_finding tool calls.
    # Critical/blocking findings auto-create CE-* tasks.
    new_tasks = len([
        t for t in state.tasks.values()
        if t.source == "critical_eval"
        and t.task_id.startswith(f"CE-{state.iteration}")
    ])

    if new_tasks > 0:
        print(f"  Critical evaluation: {new_tasks} issues found")
        git_commit(
            config, state,
            f"telic-loop({config.sprint}): Critical eval — {new_tasks} issues",
        )
    else:
        print("  Critical evaluation: deliverable meets experience bar")

    return new_tasks > 0
