"""Critical evaluation: use deliverable as real user (Evaluator agent)."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


def _needs_browser_eval(state: LoopState, config: LoopConfig | None = None) -> bool:
    """Check whether the deliverable warrants browser-based evaluation.

    Browser eval is essential for web apps — without it, visual/UX defects
    go undetected. Uses multiple signals to avoid false negatives from
    incomplete environment discovery.
    """
    import shutil

    ctx = state.context

    # Must be a web-facing deliverable.  Discovery agents don't always use
    # the exact enumerated values, so check both fields with broad sets.
    web_types = {"web_app", "web_application", "spa", "pwa", "fullstack"}
    is_web_app = (
        ctx.deliverable_type in ("software", *web_types)
        and ctx.project_type in web_types
    ) or (
        # Fallback: services with http health checks are a strong signal
        any(
            str(svc.get("health_check", "")).startswith("http")
            for svc in (ctx.services.values() if isinstance(ctx.services, dict) else ctx.services)
        )
    )
    if not is_web_app:
        return False

    # Check multiple signals for Node availability (don't rely only on discovery)
    has_node = any(
        "node" in t or "npx" in t
        for t in ctx.environment.get("tools_found", [])
    )
    if not has_node:
        # Fallback: check if npx is on PATH (discovery may have missed it)
        has_node = shutil.which("npx") is not None
    if not has_node and config:
        # Fallback: check for package.json in project dir (strong signal)
        has_node = (config.effective_project_dir / "package.json").exists()

    return has_node


def _build_playwright_config(config: LoopConfig) -> dict:
    """Build MCP server config dict for Playwright."""
    eval_dir = config.sprint_dir / "eval"
    eval_dir.mkdir(exist_ok=True)
    args = [
        "@playwright/mcp",
        "--caps", "vision",
        "--viewport-size", config.browser_eval_viewport,
        "--output-dir", str(eval_dir),
    ]
    if config.browser_eval_headless:
        args.append("--headless")
    return {"playwright": {"command": "npx", "args": args}}


def _cleanup_playwright_artifacts(config: LoopConfig) -> None:
    """Collect eval screenshots into sprint eval/ dir and remove temp files."""
    import shutil

    project_dir = config.effective_project_dir
    eval_dir = config.sprint_dir / "eval"
    eval_dir.mkdir(exist_ok=True)

    # Playwright MCP browser_take_screenshot saves relative to the agent's
    # CWD (project dir), not --output-dir.  Move stray screenshots into the
    # sprint eval/ directory so they're preserved for review.
    stray = list(project_dir.glob("eval-*.png"))
    for p in stray:
        dest = eval_dir / p.name
        shutil.move(str(p), str(dest))
    if stray:
        print(f"    Collected {len(stray)} screenshot(s) into eval/")

    # Delete .playwright-mcp/ directory (console logs — not useful to keep)
    pw_dir = project_dir / ".playwright-mcp"
    if pw_dir.is_dir():
        shutil.rmtree(pw_dir, ignore_errors=True)


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
    use_browser = _needs_browser_eval(state, config)

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
        VISION=config.vision_file.read_text(encoding="utf-8") if config.vision_file.exists() else "",
        VALUE_PROOFS=value_proofs,
        DONE_TASKS=done_summary,
        PENDING_TASKS=pending_summary,
        EPIC_SCOPE=epic_scope,
        BROWSER_SECTION=browser_section,
    )

    try:
        session.send(prompt)
    finally:
        if use_browser:
            _cleanup_playwright_artifacts(config)

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
