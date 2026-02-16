"""Context Discovery: derive sprint context from Vision + PRD + codebase."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .claude import Claude
    from .config import LoopConfig
    from .state import LoopState


def validate_inputs(config: LoopConfig) -> list[str]:
    """Validate that required input files exist. Returns list of errors."""
    errors = []
    if not config.vision_file.exists():
        errors.append(f"Vision file not found: {config.vision_file}")
    if not config.prd_file.exists():
        errors.append(f"PRD file not found: {config.prd_file}")
    if not config.sprint_dir.exists():
        errors.append(f"Sprint directory not found: {config.sprint_dir}")
    return errors


def discover_context(config: LoopConfig, claude: Claude, state: LoopState) -> None:
    """Run Context Discovery agent to populate state.context (SprintContext).

    Uses REASONER (Opus) with discover_context.md prompt. The agent examines
    the Vision, PRD, and codebase, then calls report_discovery to populate
    state.context with deliverable type, project type, environment, services,
    verification strategy, and value proofs.
    """
    from .claude import AgentRole, load_prompt

    session = claude.session(AgentRole.REASONER)
    prompt = load_prompt("discover_context",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
    )
    session.send(prompt)

    # report_discovery tool handler populates state.context
    if state.context.unresolved_questions:
        print("  DISCOVERY needs clarification:")
        for q in state.context.unresolved_questions:
            print(f"    ? {q}")


def critique_prd(
    config: LoopConfig, claude: Claude, state: LoopState,
) -> dict:
    """Run PRD Critique agent. Returns critique result dict.

    Uses REASONER (Opus) with prd_critique.md prompt. The agent evaluates
    whether the PRD is achievable given the discovered context, then calls
    report_critique with a verdict (PASS, DESCOPE, REJECT) and reason.
    """
    import json

    from .claude import AgentRole, load_prompt

    session = claude.session(AgentRole.REASONER)
    prompt = load_prompt("prd_critique",
        SPRINT_CONTEXT=json.dumps(state.context.__dict__, default=str),
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
    )
    session.send(prompt)

    critique = state.agent_results.get("critique", {})
    # Phase 1: if REJECT, warn but proceed (Phase 3 adds interactive negotiation)
    if critique.get("verdict") == "REJECT":
        print(f"  WARNING: PRD critique returned REJECT: {critique.get('reason', '')}")
        print("  Phase 3 will add interactive refinement. Proceeding for now.")
        critique["verdict"] = "DESCOPE"
    return critique


def refine_vision(
    config: LoopConfig, state: LoopState, claude: Claude,
) -> dict:
    """Run Vision Validation (Phase 3 full, Phase 1 stub).

    Phase 1: auto-passes. Phase 3: 5-pass challenge with Opus,
    interactive negotiation on NEEDS_REVISION.
    """
    from .claude import AgentRole, load_prompt

    if not config.vision_file.exists():
        return {"verdict": "PASS", "reason": "No vision file to validate"}

    session = claude.session(AgentRole.REASONER)
    prompt = load_prompt("vision_validate",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
    )
    session.send(prompt)

    validation = state.agent_results.get("vision_validation", {})
    verdict = validation.get("verdict", "PASS")

    if verdict == "NEEDS_REVISION":
        issues = validation.get("issues", [])
        hard_issues = [i for i in issues if i.get("severity") == "HARD"]

        if hard_issues:
            print("  VISION has hard issues requiring revision:")
            for issue in hard_issues:
                print(f"    ! {issue.get('description', '')}")
            # Phase 3: interactive negotiation loop would go here
            # For now, warn and proceed
            print("  Proceeding with acknowledged issues (Phase 3 adds negotiation)")
        else:
            print("  VISION has soft suggestions (non-blocking)")

    return validation


def classify_vision_complexity(
    config: LoopConfig, claude: Claude, state: LoopState,
) -> str:
    """Classify vision as single_run or multi_epic.

    Phase 1: always returns single_run.
    Phase 3: uses Opus to assess complexity signals.
    """
    from .claude import AgentRole

    vision_text = config.vision_file.read_text() if config.vision_file.exists() else ""
    prd_text = config.prd_file.read_text() if config.prd_file.exists() else ""

    # Quick heuristic: if both files are small, skip LLM classification
    combined_length = len(vision_text) + len(prd_text)
    if combined_length < 500:
        state.vision_complexity = "single_run"
        return "single_run"

    session = claude.session(
        AgentRole.REASONER,
        system_extra=(
            "Assess vision complexity. Count independently valuable "
            "deliverables. Be conservative: any complexity signal → multi_epic."
        ),
    )
    response = session.send(
        f"Classify this vision as 'single_run' or 'multi_epic'.\n\n"
        f"VISION:\n{vision_text}\n\n"
        f"PRD:\n{prd_text}\n\n"
        f"Complexity signals (any → multi_epic):\n"
        f"- >3 independently valuable deliverables\n"
        f"- >15 estimated tasks\n"
        f"- >2 layers of sequential dependencies\n"
        f"- >2 distinct technology domains\n"
        f"- Multiple external system integrations\n\n"
        f"Respond with ONLY 'single_run' or 'multi_epic' on the first line."
    )
    first_line = response.strip().split("\n")[0].strip().lower()
    classification = "multi_epic" if "multi_epic" in first_line else "single_run"
    state.vision_complexity = classification
    return classification


def decompose_into_epics(
    config: LoopConfig, claude: Claude, state: LoopState,
) -> list:
    """Decompose multi_epic vision into deliverable value blocks.

    Phase 1: no-op (only single_run supported).
    Phase 3: uses Opus with epic_decompose.md prompt, agent calls
    report_epic_decomposition to populate state.epics.
    """
    from .claude import AgentRole, load_prompt

    vision_text = config.vision_file.read_text() if config.vision_file.exists() else ""
    prd_text = config.prd_file.read_text() if config.prd_file.exists() else ""

    session = claude.session(AgentRole.REASONER)
    prompt = load_prompt("epic_decompose",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        VISION=vision_text,
        PRD=prd_text,
    )
    session.send(prompt)

    # report_epic_decomposition handler populates state.epics
    return list(state.epics)
