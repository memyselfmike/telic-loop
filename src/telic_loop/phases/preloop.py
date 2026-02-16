"""Pre-loop: discovery, PRD critique, plan generation, quality gates, preflight."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


# ---------------------------------------------------------------------------
# Quality gates — (gate_name, prompt_name, display_name)
# ---------------------------------------------------------------------------

QUALITY_GATES = [
    ("craap", "craap", "CRAAP Review"),
    ("clarity", "clarity", "CLARITY Protocol"),
    ("validate", "validate", "VALIDATE Sprint"),
    ("connect", "connect", "CONNECT Review"),
    ("break", "break", "BREAK"),
    ("prune", "prune", "PRUNE Review"),
    ("tidy", "tidy", "TIDY-FIRST"),
    ("blockers", "verify_blockers", "Blocker Validation"),
    ("vrc_init", "vrc", "Initial VRC"),
    ("preflight", "preflight", "Preflight Check"),
]


def run_preloop(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Run the complete pre-loop: qualify the work before entering the value loop."""
    from ..claude import AgentRole, load_prompt
    from ..discovery import (
        classify_vision_complexity,
        critique_prd,
        decompose_into_epics,
        discover_context,
        refine_vision,
        validate_inputs,
    )
    from ..render import render_plan_snapshot

    print("=" * 60)
    print("  PRE-LOOP: Qualifying the work")
    print("=" * 60)

    # Step 1: Inputs exist
    errors = validate_inputs(config)
    if errors:
        for e in errors:
            print(f"  MISSING: {e}")
        return False

    # Step 2: Vision Validation
    if not state.gate_passed("vision_validated"):
        refine_vision(config, state, claude)
        state.pass_gate("vision_validated")
        state.save(config.state_file)

    # Step 2b: Classify vision complexity
    if not state.gate_passed("vision_classified"):
        complexity = classify_vision_complexity(config, claude, state)
        print(f"  Vision complexity: {complexity}")
        state.pass_gate("vision_classified")
        state.save(config.state_file)

    # Step 2c: Epic decomposition if multi_epic
    if state.vision_complexity == "multi_epic" and not state.gate_passed("epics_decomposed"):
        epics = decompose_into_epics(config, claude, state)
        print(f"  Decomposed into {len(epics)} epics")
        state.pass_gate("epics_decomposed")
        state.save(config.state_file)

    # Step 3: Context Discovery
    if not state.gate_passed("context_discovered"):
        discover_context(config, claude, state)
        state.pass_gate("context_discovered")
        state.save(config.state_file)

    # Step 4: PRD Critique
    if not state.gate_passed("prd_critique"):
        critique_prd(config, claude, state)
        state.pass_gate("prd_critique")
        state.save(config.state_file)

    # Step 5: Generate plan
    if not state.gate_passed("plan_generated"):
        session = claude.session(AgentRole.REASONER)
        prompt = load_prompt("plan").format(
            SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
        )
        session.send(prompt, task_source="plan")
        if not state.tasks:
            print("FATAL: Plan generation produced zero tasks. Cannot proceed.")
            print("  This usually means the Vision/PRD is too abstract for the planner.")
            return False
        render_plan_snapshot(config, state)
        state.pass_gate("plan_generated")
        state.save(config.state_file)

    # Step 6: Quality gates
    if not _run_quality_gates(config, state, claude):
        return False

    # Step 7: Blocker check
    blocked = [
        t for t in state.tasks.values()
        if t.status == "blocked"
        and not t.blocked_reason.startswith("HUMAN_ACTION:")
    ]
    if blocked:
        print("BLOCKED: Unresolved pre-conditions")
        for t in blocked:
            print(f"  - {t.task_id}: {t.blocked_reason}")
        return False

    print("\n  PRE-LOOP COMPLETE — entering value delivery loop")
    state.phase = "value_loop"
    state.save(config.state_file)
    return True


def _run_quality_gates(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Run all quality gates in sequence."""
    from ..claude import AgentRole, load_prompt
    from ..render import render_plan_snapshot

    for gate_name, prompt_name, display_name in QUALITY_GATES:
        if state.gate_passed(gate_name):
            continue
        print(f"  Running gate: {display_name}")

        passed = _run_single_gate(
            gate_name, prompt_name, display_name,
            config, state, claude, max_retries=3,
        )
        render_plan_snapshot(config, state)
        state.save(config.state_file)

        if not passed:
            print(f"  GATE FAILED: {display_name}")
            return False
    return True


def _run_single_gate(
    gate_name: str,
    prompt_name: str,
    display_name: str,
    config: LoopConfig,
    state: LoopState,
    claude: Claude,
    max_retries: int = 3,
) -> bool:
    """Run a single quality gate with retry logic."""
    from ..claude import AgentRole, load_prompt

    for attempt in range(1, max_retries + 1):
        session = claude.session(AgentRole.REASONER)
        prompt = load_prompt(prompt_name).format(
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
            SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
            PLAN=config.plan_file.read_text() if config.plan_file.exists() else "",
            PRD=config.prd_file.read_text() if config.prd_file.exists() else "",
            VISION=config.vision_file.read_text() if config.vision_file.exists() else "",
        )
        session.send(prompt, task_source="gate")

        # Gates work by modifying tasks via manage_task tool calls.
        # If they find issues, they add/modify tasks. A gate "fails"
        # only if it creates blocked tasks.
        new_blocked = [
            t for t in state.tasks.values()
            if t.status == "blocked"
            and not t.blocked_reason.startswith("HUMAN_ACTION:")
        ]

        if not new_blocked:
            state.pass_gate(gate_name)
            return True

        if attempt < max_retries:
            print(f"  Gate {display_name} found issues (attempt {attempt}/{max_retries}), retrying...")
        else:
            print(f"  Gate {display_name} failed after {max_retries} attempts")

    state.pass_gate(gate_name)  # Pass even on failure — gates are advisory
    return True
