"""Critical evaluation: use deliverable as real user (Evaluator agent)."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


def _needs_browser_eval(state: LoopState) -> bool:
    """Check whether the deliverable warrants browser-based evaluation."""
    ctx = state.context
    has_node = any(
        "node" in t or "npx" in t
        for t in ctx.environment.get("tools_found", [])
    )
    return (
        has_node
        and ctx.deliverable_type == "software"
        and ctx.project_type in ("web_app", "web_application", "spa", "pwa")
    )


def _build_playwright_config(config: LoopConfig) -> dict:
    """Build MCP server config dict for Playwright."""
    args = [
        "@playwright/mcp",
        "--caps", "vision",
        "--viewport-size", config.browser_eval_viewport,
    ]
    if config.browser_eval_headless:
        args.append("--headless")
    return {"playwright": {"command": "npx", "args": args}}


def do_critical_eval(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Critical evaluation — Evaluator agent USES the deliverable as a real user.

    Not running tests. Not checking code. An agent EXPERIENCING the deliverable:
    - Does it make sense? Intuitive?
    - Data flows correctly end-to-end?
    - Would a real user figure this out without docs?
    - Delivers the EXPERIENCE promised by the Vision?
    """
    from ..claude import AgentRole, PLAYWRIGHT_MCP_TOOLS, load_prompt
    from ..git import git_commit

    state.tasks_since_last_critical_eval = 0

    # Determine whether to inject browser tools
    use_browser = _needs_browser_eval(state)

    mcp_servers = _build_playwright_config(config) if use_browser else None
    extra_tools = list(PLAYWRIGHT_MCP_TOOLS) if use_browser else None

    session = claude.session(
        AgentRole.EVALUATOR,
        system_extra=(
            "You are a demanding critical evaluator. USE the deliverable "
            "as the intended user would. Navigate the UI. Read the document. "
            "Run the tool. Report everything: what works, what's confusing, "
            "what's missing."
        ),
        mcp_servers=mcp_servers,
        extra_tools=extra_tools,
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

    # Build browser-specific prompt section (empty string if not a web app)
    browser_section = ""
    services_json = ""
    if use_browser:
        browser_section = load_prompt(
            "critical_eval_browser",
            SPRINT_DIR=str(config.sprint_dir),
            SERVICES_JSON=json.dumps(state.context.services, indent=2),
        )
        print("  Browser evaluation enabled — Playwright MCP injected")

    prompt = load_prompt("critical_eval",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        COMPLETED_TASKS=completed_summary,
        VISION=config.vision_file.read_text() if config.vision_file.exists() else "",
        BROWSER_SECTION=browser_section,
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
