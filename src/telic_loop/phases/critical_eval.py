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


def _cleanup_playwright_artifacts(config: LoopConfig, pre_existing_pngs: set[str]) -> None:
    """Remove Playwright screenshots and logs created during evaluation."""
    import shutil

    project_dir = config.effective_project_dir

    # Delete .playwright-mcp/ directory (console logs)
    pw_dir = project_dir / ".playwright-mcp"
    if pw_dir.is_dir():
        shutil.rmtree(pw_dir, ignore_errors=True)
        print("    Cleaned .playwright-mcp/")

    # Delete screenshots from project root that weren't there before
    cleaned = 0
    for png in project_dir.glob("*.png"):
        if str(png) not in pre_existing_pngs:
            png.unlink(missing_ok=True)
            cleaned += 1
    if cleaned:
        print(f"    Cleaned {cleaned} screenshot(s) from project root")


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
            "You are an ADVERSARIAL quality gatekeeper. Your job is to BREAK things, "
            "find every gap, and ensure NOTHING ships that doesn't meet the Vision's "
            "promises. Test EVERY view, EVERY workflow, EVERY edge case. You are the "
            "last line of defense before the user sees this. Be thorough. Be relentless."
        ),
        mcp_servers=mcp_servers,
        extra_tools=extra_tools,
    )

    # All completed tasks (full scope, not just recent)
    all_done = [t for t in state.tasks.values() if t.status == "done"]
    done_summary = "\n".join(
        f"  [{t.task_id}] {t.description}"
        for t in all_done
    )

    # Pending/in-progress tasks for context
    pending_summary = "\n".join(
        f"  [{t.task_id}] ({t.status}) {t.description}"
        for t in state.tasks.values() if t.status != "done"
    )

    # Value proofs as explicit test checklist
    value_proofs = "\n".join(
        f"  {i+1}. {proof}"
        for i, proof in enumerate(state.context.value_proofs)
    )

    # Epic scope for multi-epic sprints
    epic_scope = ""
    if (state.vision_complexity == "multi_epic"
            and state.epics
            and state.current_epic_index < len(state.epics)):
        epic = state.epics[state.current_epic_index]
        epic_scope = (
            f"Current Epic: {epic.title}\n"
            f"Value: {epic.value_statement}\n"
            f"Deliverables: {', '.join(epic.deliverables)}\n"
            f"Completion Criteria:\n"
            + "\n".join(f"  - {c}" for c in epic.completion_criteria)
        )

    # Build browser-specific prompt section (empty string if not a web app)
    browser_section = ""
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
        VISION=config.vision_file.read_text() if config.vision_file.exists() else "",
        VALUE_PROOFS=value_proofs,
        DONE_TASKS=done_summary,
        PENDING_TASKS=pending_summary,
        EPIC_SCOPE=epic_scope,
        BROWSER_SECTION=browser_section,
    )

    # Capture pre-existing screenshots for cleanup
    from pathlib import Path
    project_dir = Path(config.effective_project_dir)
    pre_pngs = {str(p) for p in project_dir.glob("*.png")} if use_browser else set()

    try:
        session.send(prompt)
    finally:
        if use_browser:
            _cleanup_playwright_artifacts(config, pre_pngs)

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
