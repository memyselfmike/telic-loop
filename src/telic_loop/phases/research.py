"""External research: web search, documentation retrieval, synthesis."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


def do_research(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Research agent finds current, accurate information the loop doesn't have.

    Triggered when fixes are exhausted. Uses web_search and web_fetch
    provider tools to find library docs, GitHub issues, changelogs, workarounds.
    """
    from ..claude import AgentRole, load_prompt

    failing = {
        v.verification_id: v
        for v in state.verifications.values()
        if v.status == "failed" and v.attempts >= config.max_fix_attempts
    }
    if not failing:
        state.research_attempted_for_current_failures = True
        return False

    failure_context = [
        {
            "verification": v_id,
            "last_error": v.last_error,
            "attempt_history": v.attempt_history,
            "attempts": v.attempts,
        }
        for v_id, v in failing.items()
    ]

    session = claude.session(
        AgentRole.RESEARCHER,
        system_extra=(
            "You are a research agent. Find CURRENT, ACCURATE information "
            "the loop doesn't have. Search for: library docs, GitHub issues, "
            "changelogs, workarounds. Focus on what CHANGED since training data."
        ),
    )

    prompt = load_prompt("research").format(
        FAILURES=json.dumps(failure_context, indent=2),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        VISION_SUMMARY=(
            config.vision_file.read_text()[:2000]
            if config.vision_file.exists() else ""
        ),
    )

    session.send(prompt)

    # Research findings via report_research tool call
    if (
        state.research_briefs
        and state.research_briefs[-1].get("iteration") == state.iteration
    ):
        brief = state.research_briefs[-1]
        print(f"  Research found: {brief['topic']}")
        # Reset fix attempts so fixer can retry with new knowledge
        for v_id in failing:
            state.verifications[v_id].attempts = 0
        state.research_attempted_for_current_failures = True
        return True

    state.research_attempted_for_current_failures = True

    # Last resort: human insight
    print("\n  REQUESTING HUMAN INSIGHT — fixes and research exhausted")
    for v_id, v in failing.items():
        print(f"    - {v_id}: {v.last_error[:200] if v.last_error else 'unknown'}")
    insight = input("  Guidance (Enter to skip): ").strip()
    if insight:
        state.research_briefs.append({
            "topic": "Human insight",
            "findings": insight,
            "sources": ["human"],
            "iteration": state.iteration,
        })
        for v_id in failing:
            state.verifications[v_id].attempts = 0
        return True
    return False


def get_research_context(state: LoopState) -> str:
    """Get all research briefs for the fix agent's context."""
    if not state.research_briefs:
        return ""
    relevant = [
        f"## Research Brief: {b['topic']}\n"
        f"Findings: {b['findings']}\n"
        f"Sources: {', '.join(b.get('sources', []))}\n"
        for b in state.research_briefs
    ]
    return "\n--- EXTERNAL RESEARCH ---\n" + "\n".join(relevant) + "\n--- END RESEARCH ---\n"
