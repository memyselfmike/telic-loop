"""Context Discovery: derive sprint context from Vision + PRD + codebase."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .claude import Claude
    from .config import LoopConfig
    from .state import LoopState, RefinementState


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
    """Run PRD Critique agent with interactive refinement on REJECT.

    Uses REASONER (Opus) with prd_critique.md prompt. If verdict is REJECT,
    enters interactive loop where human revises PRD.md and re-critiques.
    Tracks rounds in state.prd_refinement for crash resumability.
    """
    import json

    from .claude import AgentRole, load_prompt
    from .state import RefinementRound

    ref = state.prd_refinement

    # Crash-resume: if we were awaiting input, skip straight to prompt
    if ref.status == "awaiting_input":
        print("\n  Resuming PRD critique (was waiting for input)...")
        action = _prd_prompt_loop(config, state)
        if action == "quit":
            raise SystemExit("User quit during PRD refinement.")
        # action == "revised" — fall through to re-critique

    while True:
        ref.status = "running"
        ref.current_round += 1
        state.save(config.state_file)

        session = claude.session(AgentRole.REASONER)
        prompt = load_prompt("prd_critique",
            SPRINT_CONTEXT=json.dumps(state.context.__dict__, default=str),
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
        )
        session.send(prompt)

        critique = state.agent_results.get("critique", {})
        verdict = critique.get("verdict", "APPROVE")

        # Record this round
        ref.rounds.append(RefinementRound(
            round_num=ref.current_round,
            timestamp=datetime.now().isoformat(),
            analysis_result=critique,
            hard_issues=[{"verdict": verdict, "reason": critique.get("reason", "")}]
                if verdict == "REJECT" else [],
            soft_issues=[],
        ))

        if verdict != "REJECT":
            ref.status = "done"
            ref.consensus_reason = critique.get("reason", "")
            state.save(config.state_file)
            return critique

        # REJECT — interactive refinement
        _present_prd_rejection(critique)

        ref.status = "awaiting_input"
        state.save(config.state_file)

        action = _prd_prompt_loop(config, state)
        if action == "quit":
            raise SystemExit("User quit during PRD refinement.")

        # action == "revised" — loop back to re-critique
        ref.rounds[-1].human_action = "revised"
        print(f"\n  Re-running PRD critique (round {ref.current_round + 1})...")


def refine_vision(
    config: LoopConfig, state: LoopState, claude: Claude,
) -> dict:
    """Run Vision Validation with interactive refinement on NEEDS_REVISION.

    Uses REASONER (Opus) with vision_validate.md prompt (5-pass analysis).
    If verdict is NEEDS_REVISION:
      - HARD issues: human must revise VISION.md, then re-validate
      - SOFT issues only: human can [A]cknowledge and proceed, or [R]evise
    Tracks rounds in state.vision_refinement for crash resumability.
    """
    from .claude import AgentRole, load_prompt
    from .state import RefinementRound

    if not config.vision_file.exists():
        return {"verdict": "PASS", "reason": "No vision file to validate"}

    ref = state.vision_refinement

    # Crash-resume: if we were awaiting input, skip straight to prompt
    if ref.status == "awaiting_input":
        print("\n  Resuming vision refinement (was waiting for input)...")
        has_hard = any(
            i.get("severity") == "hard"
            for i in state.agent_results.get("vision_validation", {}).get("issues", [])
        )
        action = _vision_prompt_loop(config, state, has_hard_issues=has_hard)
        if action == "quit":
            raise SystemExit("User quit during vision refinement.")
        if action == "acknowledge":
            ref.status = "done"
            ref.consensus_reason = "Soft issues acknowledged by human"
            state.save(config.state_file)
            return state.agent_results.get("vision_validation", {})
        # action == "revised" — fall through to re-validate

    while True:
        ref.status = "running"
        ref.current_round += 1
        state.save(config.state_file)

        session = claude.session(AgentRole.REASONER)
        prompt = load_prompt("vision_validate",
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
        )
        session.send(prompt)

        validation = state.agent_results.get("vision_validation", {})
        verdict = validation.get("verdict", "PASS")
        issues = validation.get("issues", [])
        hard_issues = [i for i in issues if i.get("severity") == "hard"]
        soft_issues = [i for i in issues if i.get("severity") == "soft"]

        # Record this round
        ref.rounds.append(RefinementRound(
            round_num=ref.current_round,
            timestamp=datetime.now().isoformat(),
            analysis_result=validation,
            hard_issues=hard_issues,
            soft_issues=soft_issues,
        ))

        if verdict == "PASS":
            ref.status = "done"
            ref.consensus_reason = validation.get("reason", "")
            state.save(config.state_file)
            return validation

        # NEEDS_REVISION — present findings and enter interactive loop
        _present_vision_brief(validation)

        ref.status = "awaiting_input"
        state.save(config.state_file)

        action = _vision_prompt_loop(config, state, has_hard_issues=bool(hard_issues))

        if action == "quit":
            raise SystemExit("User quit during vision refinement.")

        if action == "acknowledge":
            # Soft issues only — human accepts the risk
            ref.status = "done"
            ref.consensus_reason = "Soft issues acknowledged by human"
            ref.acknowledged_soft_issues = [i.get("id", "") for i in soft_issues]
            ref.rounds[-1].human_action = "acknowledged"
            state.save(config.state_file)
            return validation

        # action == "revised" — loop back to re-validate
        ref.rounds[-1].human_action = "revised"
        print(f"\n  Re-running vision validation (round {ref.current_round + 1})...")


# ---------------------------------------------------------------------------
# Interactive refinement helpers
# ---------------------------------------------------------------------------

_DIMENSION_LABELS = {
    "outcome_grounded": "Outcome-Grounded",
    "adoption_realistic": "Adoption-Realistic",
    "causally_sound": "Causally-Sound",
    "failure_aware": "Failure-Aware",
}


def _present_vision_brief(validation: dict) -> None:
    """Print a structured terminal summary of vision validation findings."""
    print("\n" + "=" * 60)
    print("  VISION VALIDATION — NEEDS REVISION")
    print("=" * 60)

    # Dimensions
    dims = validation.get("dimensions", {})
    if dims:
        print("\n  Dimensions:")
        for key, label in _DIMENSION_LABELS.items():
            score = dims.get(key, "?")
            marker = " !!" if score in ("WEAK", "CRITICAL") else ""
            print(f"    {label:24s} {score}{marker}")

    # Strengths
    strengths = validation.get("strengths", [])
    if strengths:
        print("\n  Strengths:")
        for s in strengths:
            print(f"    + {s}")

    # Issues — HARD first, then SOFT
    issues = validation.get("issues", [])
    hard = [i for i in issues if i.get("severity") == "hard"]
    soft = [i for i in issues if i.get("severity") == "soft"]

    if hard:
        print("\n  HARD issues (must resolve before proceeding):")
        for i in hard:
            print(f"    ! [{i.get('category', '?')}] {i.get('description', '')}")
            if i.get("suggested_revision"):
                print(f"      Suggestion: {i['suggested_revision']}")

    if soft:
        print("\n  SOFT issues (advisory — can acknowledge and proceed):")
        for i in soft:
            print(f"    ~ [{i.get('category', '?')}] {i.get('description', '')}")
            if i.get("suggested_revision"):
                print(f"      Suggestion: {i['suggested_revision']}")

    # Overall reason
    reason = validation.get("reason", "")
    if reason:
        print(f"\n  Summary: {reason}")

    print()


def _vision_prompt_loop(
    config: "LoopConfig", state: "LoopState", *, has_hard_issues: bool,
) -> str:
    """Interactive input loop for vision refinement.

    Returns: "revised" | "acknowledge" | "quit"
    """
    vision_path = config.vision_file

    if has_hard_issues:
        print(f"  HARD issues found — you must revise {vision_path}")
        print("  Options:")
        print("    [R] Revise — edit VISION.md, then press Enter to re-validate")
        print("    [Q] Quit")
        valid = {"r", "q"}
    else:
        print("  Only SOFT issues found — you may proceed or revise.")
        print("  Options:")
        print("    [A] Acknowledge risks and proceed")
        print("    [R] Revise — edit VISION.md, then press Enter to re-validate")
        print("    [Q] Quit")
        valid = {"a", "r", "q"}

    while True:
        try:
            choice = input("\n  Your choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "quit"

        if not choice:
            continue

        if choice[0] not in valid:
            print(f"  Invalid choice. Enter one of: {', '.join(sorted(valid)).upper()}")
            continue

        if choice[0] == "q":
            return "quit"
        if choice[0] == "a":
            return "acknowledge"
        if choice[0] == "r":
            print(f"\n  Edit {vision_path} now, then press Enter when ready...")
            try:
                input("  Press Enter to re-validate >> ")
            except (EOFError, KeyboardInterrupt):
                return "quit"
            return "revised"


def _present_prd_rejection(critique: dict) -> None:
    """Print a structured terminal summary of PRD rejection."""
    print("\n" + "=" * 60)
    print("  PRD CRITIQUE — REJECTED")
    print("=" * 60)

    reason = critique.get("reason", "")
    if reason:
        print(f"\n  Reason: {reason}")

    amendments = critique.get("amendments", [])
    if amendments:
        print("\n  Suggested amendments:")
        for i, a in enumerate(amendments, 1):
            print(f"    {i}. {a}")

    descope = critique.get("descope_suggestions", [])
    if descope:
        print("\n  Descope suggestions:")
        for i, s in enumerate(descope, 1):
            print(f"    {i}. {s}")

    print()


def _prd_prompt_loop(config: "LoopConfig", state: "LoopState") -> str:
    """Interactive input loop for PRD refinement.

    Returns: "revised" | "quit"
    """
    prd_path = config.prd_file

    print(f"  PRD was REJECTED — you must revise {prd_path}")
    print("  Options:")
    print("    [R] Revise — edit PRD.md, then press Enter to re-critique")
    print("    [Q] Quit")

    while True:
        try:
            choice = input("\n  Your choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "quit"

        if not choice:
            continue

        if choice[0] not in {"r", "q"}:
            print("  Invalid choice. Enter R or Q.")
            continue

        if choice[0] == "q":
            return "quit"
        if choice[0] == "r":
            print(f"\n  Edit {prd_path} now, then press Enter when ready...")
            try:
                input("  Press Enter to re-critique >> ")
            except (EOFError, KeyboardInterrupt):
                return "quit"
            return "revised"


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
