# Loop V3: Phase 3 Plan — +Critical Eval + Research + Process Monitor + Vision Validation

**Date**: 2026-02-15
**Prerequisite**: Phase 2 complete and tested
**Architecture**: V3_ARCHITECTURE.md
**Requirements**: V3_PRD.md (R8, R22-R24, R28-R30, R32)

---

## Scope

### What Phase 3 Adds
- **Vision Refinement** (interactive) — 5-pass analysis + collaborative negotiation with human
- **Vision Complexity Classification** — single_run vs. multi_epic
- **Epic Decomposition** — break complex visions into deliverable value blocks
- **Epic Feedback Checkpoint** — between-epic human confirmation gate (optional, with timeout)
- **Critical Evaluation** — Evaluator agent uses deliverable as real user
- **External Research** — web search for current docs when fixes exhausted
- **Process Monitor** — 3-layer execution pattern analysis + strategy reasoning
- **Full Coherence Evaluation** — all 7 dimensions at epic boundaries and pre-exit-gate

### What Changes from Phase 2
- `refine_vision` stub → interactive 5-pass refinement (analysis + HARD/SOFT classification + alternative research + human negotiation)
- `classify_vision_complexity` stub → Opus-driven complexity assessment
- `decompose_into_epics` stub → horizontal value-slice decomposition
- `epic_feedback_checkpoint` stub → curated summary + Proceed/Adjust/Stop + timeout
- `do_critical_eval` stub → Evaluator agent (Opus, read-only tools)
- `do_research` stub → Research agent (Opus + web_search + web_fetch)
- `do_full_coherence_eval` stub → Opus 7-dimension system evaluation
- Value loop gains process monitor call after every action
- Value loop runs per-epic for multi_epic visions (outer epic loop added)
- Fix agent gains `{RESEARCH_CONTEXT}` injection

### After Phase 3
All stubs are replaced. The system matches the full Architecture Reference specification.

---

## 1. Vision Refinement (Interactive)

Replaces Phase 1 stub. Runs before Context Discovery in the pre-loop.

Vision refinement is a **collaborative negotiation**, not a pass/fail gate. The loop does deep analysis, classifies issues by severity, researches alternatives for hard blockers, and works with the human until consensus. The human is present at launch time — the loop uses them.

### 1.1 The 5-Pass Analysis (unchanged analytical core)

```python
def run_vision_analysis(config: LoopConfig, claude: Claude, state: LoopState) -> dict:
    """
    5-pass Vision analysis. Each pass uses a separate Opus session.
    Returns structured findings via report_vision_validation tool.
    """
    vision = config.vision_file.read_text()
    prompt_template = load_prompt("vision_validate")

    # Pass 1: Extraction (faithful comprehension)
    session_p1 = claude.session(AgentRole.REASONER,
        system_extra="You are extracting a structured model from a Vision document. "
        "Do not judge yet — map what the Vision claims. "
        "Extract goals, causal chains, metrics, target user, assumptions."
    )
    p1_result = session_p1.send(format_pass(prompt_template, "Pass 1", VISION=vision))

    # Pass 2: Force Analysis (adversarial empathy)
    session_p2 = claude.session(AgentRole.REASONER,
        system_extra="You are modeling forces for and against adoption. "
        "Think like the target user, not the builder. Be honest about "
        "anxiety and habit — these kill products."
    )
    p2_result = session_p2.send(format_pass(prompt_template, "Pass 2",
        VISION=vision, PASS_1_OUTPUT=p1_result))

    # Pass 3: Causal Audit (logical rigor)
    session_p3 = claude.session(AgentRole.REASONER,
        system_extra="You are auditing causal logic. Every If→Then needs "
        "a mechanism ('because'). Every metric needs a gaming scenario."
    )
    p3_result = session_p3.send(format_pass(prompt_template, "Pass 3",
        VISION=vision, PASS_1_OUTPUT=p1_result, PASS_2_OUTPUT=p2_result))

    # Pass 4: Pre-Mortem (imaginative pessimism)
    session_p4 = claude.session(AgentRole.REASONER,
        system_extra="You are conducting a pre-mortem. The project FAILED. "
        "18 months later, the deliverable was abandoned. WHY? "
        "Generate specific, plausible failure scenarios."
    )
    p4_result = session_p4.send(format_pass(prompt_template, "Pass 4",
        VISION=vision, PASS_2_OUTPUT=p2_result, PASS_3_OUTPUT=p3_result))

    # Pass 5: Synthesis (balanced judgment + issue classification)
    session_p5 = claude.session(AgentRole.REASONER,
        system_extra="You are producing a balanced final assessment. "
        "Score on: outcome-grounded, adoption-realistic, causally-sound, failure-aware. "
        "Classify every issue as HARD (impossible/contradictory) or SOFT (risky/weak)."
    )
    p5_result = session_p5.send(format_pass(prompt_template, "Pass 5",
        VISION=vision, PASS_1_OUTPUT=p1_result, PASS_2_OUTPUT=p2_result,
        PASS_3_OUTPUT=p3_result, PASS_4_OUTPUT=p4_result))

    validation = state.agent_results.get("vision_validation")
    if not validation:
        validation = {"verdict": "NEEDS_REVISION", "reason": "Agent did not call reporting tool",
                      "issues": [], "strengths": []}
    return validation
```

### 1.1b Utility: format_pass() and format_prompt()

These are used throughout Phase 3 for prompt template formatting.

```python
def format_pass(template: str, pass_label: str, **kwargs) -> str:
    """Format a prompt template for a specific analysis pass.
    Extracts the section for the given pass and substitutes variables."""
    # The template contains sections like "## Pass 1: ...", "## Pass 2: ..."
    # Extract the relevant section and format with provided kwargs
    sections = template.split("## ")
    pass_section = ""
    for section in sections:
        if section.startswith(pass_label):
            pass_section = "## " + section
            break
    if not pass_section:
        pass_section = template  # Fallback: use full template
    # Substitute only the kwargs that have placeholders in the section
    formatted = pass_section
    for key, value in kwargs.items():
        formatted = formatted.replace(f"{{{key}}}", str(value))
    return formatted


def format_prompt(template: str, **kwargs) -> str:
    """Format a prompt template by substituting {KEY} placeholders with values."""
    if isinstance(template, Path):
        template = template.read_text()
    result = template
    for key, value in kwargs.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result
```

### 1.2 Alternative Research (for HARD issues)

```python
def research_vision_alternative(claude: Claude, state: LoopState, issue: dict, vision_text: str) -> dict:
    """
    Use Researcher agent (Opus + web tools) to find alternatives for a HARD issue.
    Returns {alternatives: [str], sources: [str], recommendation: str}.
    """
    session = claude.session(AgentRole.RESEARCHER)
    prompt = (
        f"A Vision document describes: {vision_text[:2000]}\n\n"
        f"This has a hard issue that must be resolved:\n"
        f"  Issue: {issue['description']}\n"
        f"  Category: {issue['category']}\n"
        f"  Evidence: {issue['evidence']}\n\n"
        f"Research alternatives that achieve the same user outcome "
        f"without the impossible/contradictory element. "
        f"Be specific — name actual technologies, APIs, approaches. "
        f"For each alternative, explain trade-offs.\n\n"
        f"Report via report_research tool."
    )
    session.send(prompt)
    research = state.agent_results.get("research", {})
    return {
        "alternatives": research.get("findings", []),
        "sources": research.get("sources", []),
        "recommendation": research.get("topic", ""),
    }
```

### 1.3 The Interactive Refinement Loop

Uses `RefinementState` for crash resumability and audit trail. State is saved after
every expensive operation (analysis, research) and every human decision.

```python
def refine_vision(config: LoopConfig, state: LoopState, claude: Claude) -> dict:
    """
    Interactive vision refinement. Runs 5-pass analysis, then negotiates
    with the human until consensus. Never exits silently — the human can
    always Ctrl+C to abort.

    Resumable: on crash, checks state.vision_refinement to skip completed work.
    Auditable: every round's findings and human decisions are persisted.

    - HARD issues (impossible/contradictory): loop holds firm, researches
      alternatives, human must revise. Cannot be overridden.
    - SOFT issues (risky/weak): loop advises strongly, human can acknowledge
      risk and proceed.
    """
    ref = state.vision_refinement

    # Resume check: if we crashed while awaiting input, skip straight to prompt
    if ref.status == "awaiting_input" and ref.rounds:
        last_round = ref.rounds[-1]
        print(f"\n  Resuming vision refinement from round {last_round.round_num}...")
        print(f"  (Previous analysis and research results preserved)")
        validation = last_round.analysis_result
        hard_issues = last_round.hard_issues
        soft_issues = last_round.soft_issues
        alternatives = last_round.research_results
        # Skip to presenting + prompting
        return _vision_prompt_loop(config, state, claude, ref, validation,
                                    hard_issues, soft_issues, alternatives)

    while True:
        ref.current_round += 1
        ref.status = "analyzing"
        state.save(config.state_file)

        print(f"\n{'=' * 60}")
        print(f"  VISION REFINEMENT — Round {ref.current_round}")
        print(f"{'=' * 60}")

        # Run 5-pass analysis
        validation = run_vision_analysis(config, claude, state)

        # PASS — consensus reached
        if validation["verdict"] == "PASS":
            print("\n  ✓ Vision validated — consensus reached.")
            ref.status = "consensus"
            ref.consensus_reason = "pass"
            ref.rounds.append(RefinementRound(
                round_num=ref.current_round,
                timestamp=datetime.now().isoformat(),
                analysis_result=validation,
                hard_issues=[], soft_issues=[],
                human_action="n/a",
            ))
            state.save(config.state_file)
            return validation

        # Extract classified issues
        issues = validation.get("issues", [])
        hard_issues = [i for i in issues if i.get("severity") == "hard"]
        soft_issues = [i for i in issues if i.get("severity") == "soft"]

        # Research alternatives for each HARD issue
        alternatives = {}
        if hard_issues:
            ref.status = "researching"
            state.save(config.state_file)
            print(f"\n  Researching alternatives for {len(hard_issues)} hard issue(s)...")
            for issue in hard_issues:
                alternatives[issue["id"]] = research_vision_alternative(
                    claude, state, issue, config.vision_file.read_text()
                )

        # Create round record and save BEFORE waiting for human
        current_round = RefinementRound(
            round_num=ref.current_round,
            timestamp=datetime.now().isoformat(),
            analysis_result=validation,
            hard_issues=hard_issues,
            soft_issues=soft_issues,
            research_results=alternatives,
        )
        ref.rounds.append(current_round)
        ref.status = "awaiting_input"
        state.save(config.state_file)  # CRITICAL: save before blocking on human

        result = _vision_prompt_loop(config, state, claude, ref, validation,
                                      hard_issues, soft_issues, alternatives)
        if result is not None:
            return result
        # result is None means "revised, loop again"


def _vision_prompt_loop(config, state, claude, ref, validation,
                        hard_issues, soft_issues, alternatives) -> dict | None:
    """Present findings and get human decision. Returns validation on consensus, None on revise."""
    strengths = validation.get("strengths", [])

    present_vision_brief(
        round_num=ref.current_round,
        dimensions=validation.get("dimensions", {}),
        strengths=strengths,
        hard_issues=hard_issues,
        alternatives=alternatives,
        soft_issues=soft_issues,
    )

    while True:  # input validation loop
        if hard_issues:
            print("\n  Hard issues remain — vision must be revised.")
            print(f"  [R] Edit {config.vision_file.name} and re-validate")
            print(f"  [Q] Quit")
            choice = input("\n  > ").strip().upper()
        else:
            print(f"\n  [R] Edit {config.vision_file.name} and re-validate")
            print(f"  [A] Acknowledge soft risks and proceed")
            print(f"  [Q] Quit")
            choice = input("\n  > ").strip().upper()

        if choice == "Q":
            print("\n  Vision refinement aborted by user.")
            sys.exit(0)

        if choice == "A" and not hard_issues:
            ref.rounds[-1].human_action = "acknowledged"
            ref.acknowledged_soft_issues = [i["id"] for i in soft_issues]
            ref.status = "consensus"
            ref.consensus_reason = "soft_risks_acknowledged"
            state.save(config.state_file)
            print("\n  ✓ Soft risks acknowledged — proceeding with vision as-is.")
            validation["verdict"] = "PASS"
            return validation

        if choice == "R":
            ref.rounds[-1].human_action = "revised"
            state.save(config.state_file)
            print(f"\n  Edit {config.vision_file} now.")
            input("  Press Enter when done editing...")
            return None  # signal: re-run analysis

        print(f"\n  Unrecognized option: {choice}")


def present_vision_brief(round_num, dimensions, strengths, hard_issues, alternatives, soft_issues):
    """Print the refinement brief to terminal."""
    # Strengths
    if strengths:
        print("\n  Strengths:")
        for s in strengths:
            print(f"    ✓ {s}")

    # Dimension scores
    if dimensions:
        print("\n  Dimensions:")
        for dim, score in dimensions.items():
            icon = "✓" if score in ("STRONG", "ADEQUATE") else "✗"
            print(f"    {icon} {dim}: {score}")

    # Hard issues
    if hard_issues:
        print(f"\n  ✗ Hard Issues ({len(hard_issues)}) — must resolve:")
        for i, issue in enumerate(hard_issues, 1):
            print(f"\n    {i}. [{issue['category'].upper()}] {issue['description']}")
            print(f"       Evidence: {issue['evidence']}")
            if issue["id"] in alternatives and alternatives[issue["id"]]["alternatives"]:
                print(f"       Researched alternatives:")
                for j, alt in enumerate(alternatives[issue["id"]]["alternatives"], 1):
                    alt_text = alt if isinstance(alt, str) else alt.get("finding", str(alt))
                    print(f"         {chr(96+j)}) {alt_text}")
            if issue.get("suggested_revision"):
                print(f"       Suggested revision: {issue['suggested_revision']}")

    # Soft issues
    if soft_issues:
        print(f"\n  ⚠ Soft Issues ({len(soft_issues)}) — advisory:")
        for i, issue in enumerate(soft_issues, 1):
            print(f"\n    {i}. [{issue['category'].upper()}] {issue['description']}")
            if issue.get("suggested_revision"):
                print(f"       Recommendation: {issue['suggested_revision']}")
```

### 1.4 PRD Refinement (same principle)

The PRD critique follows the same interactive model with `RefinementState` tracking.
APPROVE, AMEND, DESCOPE proceed normally. Only REJECT triggers interactive negotiation.

```python
def refine_prd(config: LoopConfig, state: LoopState, claude: Claude) -> dict:
    """
    Interactive PRD refinement. On REJECT, researches what IS feasible
    and negotiates with the human until the PRD is achievable.

    Resumable via state.prd_refinement. Same crash-safety as refine_vision().
    """
    ref = state.prd_refinement

    # Resume check
    if ref.status == "awaiting_input" and ref.rounds:
        last_round = ref.rounds[-1]
        print(f"\n  Resuming PRD refinement from round {last_round.round_num}...")
        critique = last_round.analysis_result
        alternatives = last_round.research_results
        return _prd_prompt_loop(config, state, ref, critique, alternatives)

    while True:
        ref.current_round += 1
        ref.status = "analyzing"
        state.save(config.state_file)

        # Run PRD critique
        session = claude.session(AgentRole.REASONER)
        prompt = load_prompt("prd_critique").format(
            SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
        )
        session.send(prompt)
        critique = state.agent_results.get("critique", {})
        verdict = critique.get("verdict", "APPROVE")

        if verdict in ("APPROVE", "AMEND", "DESCOPE"):
            if verdict == "AMEND":
                print(f"  PRD amended: {critique.get('reason', '')}")
            elif verdict == "DESCOPE":
                print(f"  PRD descoped: {critique.get('reason', '')}")
                for s in critique.get("descope_suggestions", []):
                    print(f"    - {s}")
            ref.status = "consensus"
            ref.consensus_reason = verdict.lower()
            ref.rounds.append(RefinementRound(
                round_num=ref.current_round,
                timestamp=datetime.now().isoformat(),
                analysis_result=critique,
                hard_issues=[], soft_issues=[],
                human_action="n/a",
            ))
            state.save(config.state_file)
            return critique

        # REJECT — research alternatives and negotiate
        ref.status = "researching"
        state.save(config.state_file)

        print(f"\n{'=' * 60}")
        print(f"  PRD REFINEMENT — Round {ref.current_round}")
        print(f"{'=' * 60}")
        print(f"\n  The PRD has infeasible requirements:")
        print(f"  {critique.get('reason', 'No reason provided')}")

        print(f"\n  Researching feasible alternatives...")
        research_session = claude.session(AgentRole.RESEARCHER)
        research_session.send(
            f"A PRD was rejected as infeasible: {critique.get('reason', '')}\n\n"
            f"PRD content: {config.prd_file.read_text()[:3000]}\n\n"
            f"Research what IS feasible that achieves the same user outcomes. "
            f"Propose concrete alternatives with trade-offs. "
            f"Report via report_research tool."
        )
        alternatives = state.agent_results.get("research", {})

        # Save round before blocking on human
        ref.rounds.append(RefinementRound(
            round_num=ref.current_round,
            timestamp=datetime.now().isoformat(),
            analysis_result=critique,
            hard_issues=[{"description": critique.get("reason", ""), "category": "infeasible"}],
            soft_issues=[],
            research_results=alternatives,
        ))
        ref.status = "awaiting_input"
        state.save(config.state_file)

        result = _prd_prompt_loop(config, state, ref, critique, alternatives)
        if result is not None:
            return result


def _prd_prompt_loop(config, state, ref, critique, alternatives) -> dict | None:
    """Present PRD findings and get human decision. Returns critique on proceed, None on revise."""
    if alternatives.get("findings"):
        print(f"\n  Feasible alternatives:")
        for f in alternatives["findings"]:
            finding = f if isinstance(f, str) else f.get("finding", str(f))
            print(f"    - {finding}")

    while True:
        print(f"\n  [R] Edit {config.prd_file.name} and re-critique")
        print(f"  [Q] Quit")
        choice = input("\n  > ").strip().upper()

        if choice == "Q":
            print("\n  PRD refinement aborted by user.")
            sys.exit(0)

        if choice == "R":
            ref.rounds[-1].human_action = "revised"
            state.save(config.state_file)
            print(f"\n  Edit {config.prd_file} now.")
            input("  Press Enter when done editing...")
            return None

        print(f"\n  Unrecognized option: {choice}")
```

**Prompt**: `vision_validate.md` (5-pass analysis with HARD/SOFT issue classification)
**Key design**: The loop is advisory but forceful — HARD issues cannot be overridden, only resolved. SOFT issues can be acknowledged. No iteration cap — human can always Ctrl+C.

---

## 2. Critical Evaluation

Replaces Phase 2 stub. Evaluator agent (Opus) uses the deliverable as a real user. For web app deliverables, the evaluator gets **Playwright MCP browser tools** injected conditionally — it opens a real browser, navigates the UI, takes screenshots, and interacts with the application.

### Browser Evaluation (Web Apps)

The `_needs_browser_eval()` predicate gates browser tool injection on:
- Node.js available in the environment
- `deliverable_type == "software"`
- `project_type` in `("web_app", "web_application", "spa", "pwa")`

When active, `@playwright/mcp` is launched with `--caps vision` (for screenshot-based visual evaluation) and the evaluator receives 15 `mcp__playwright__browser_*` tools in addition to its read-only tools. Non-web deliverables get the existing readonly evaluation unchanged.

```python
def _needs_browser_eval(state: LoopState) -> bool:
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
    args = [
        "@playwright/mcp",
        "--caps", "vision",
        "--viewport-size", config.browser_eval_viewport,
    ]
    if config.browser_eval_headless:
        args.append("--headless")
    return {"playwright": {"command": "npx", "args": args}}

def do_critical_eval(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    Critical evaluation. Separate Opus agent USES the deliverable as a real user.

    For web apps: opens a real browser via Playwright MCP, navigates the UI,
    takes screenshots (visual evaluation), and interacts with elements.
    For non-web deliverables: uses read-only file tools only.
    """
    state.tasks_since_last_critical_eval = 0

    # Conditionally inject browser tools for web app deliverables
    use_browser = _needs_browser_eval(state)
    mcp_servers = _build_playwright_config(config) if use_browser else None
    extra_tools = list(PLAYWRIGHT_MCP_TOOLS) if use_browser else None

    session = claude.session(
        AgentRole.EVALUATOR,
        system_extra="You are a demanding critical evaluator. USE the deliverable "
        "as the intended user would. Navigate the UI. Read the document. Run the tool. "
        "Report everything: what works, what's confusing, what's missing.",
        mcp_servers=mcp_servers,
        extra_tools=extra_tools,
    )

    # Browser section conditionally injected into prompt
    browser_section = ""
    if use_browser:
        browser_section = load_prompt("critical_eval_browser",
            SPRINT_DIR=str(config.sprint_dir),
            SERVICES_JSON=json.dumps(state.context.services, indent=2),
        )

    prompt = load_prompt("critical_eval",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        COMPLETED_TASKS=completed_summary,
        VISION=config.vision_file.read_text(),
        BROWSER_SECTION=browser_section,
    )

    response = session.send(prompt)

    # Findings arrive via report_eval_finding tool calls.
    # Critical/blocking findings auto-create CE-* tasks.
    new_tasks = len([
        t for t in state.tasks.values()
        if t.source == "critical_eval" and t.task_id.startswith(f"CE-{state.iteration}")
    ])

    if new_tasks > 0:
        print(f"  Critical evaluation: {new_tasks} issues found")
        git_commit(config, state, f"telic-loop({config.sprint}): Critical eval — {new_tasks} issues")
    else:
        print(f"  Critical evaluation: deliverable meets experience bar")

    return new_tasks > 0
```

### Evaluation by Deliverable Type

| Type | What the Evaluator Does |
|------|------------------------|
| `web_app` | **Opens browser via Playwright MCP**, navigates UI, takes screenshots, completes workflows |
| `cli` | Runs tool with realistic inputs, evaluates output |
| `api` | Exercises endpoints as consuming app |
| `library` | Writes example code using the library |
| `report` | Reads as intended audience |
| `pipeline` | Provides input, examines output quality |
| `config` | Applies config, uses the system |

### report_eval_finding Handler

```python
def handle_eval_finding(input, state):
    """Handle report_eval_finding — auto-create tasks for critical/blocking."""
    severity = input["severity"]
    if severity in ("critical", "blocking"):
        task_id = f"CE-{state.iteration}-{len(state.tasks)}"
        state.add_task(TaskState(
            task_id=task_id,
            source="critical_eval",
            description=input.get("suggested_fix", input["description"]),
            value=input["user_impact"],
            acceptance=f"Fix: {input['description']}",
            created_at=datetime.now().isoformat(),
        ))
    return f"Finding recorded: [{severity}] {input['description']}"
```

---

## 3. External Research

Replaces Phase 2 stub. Opus + web_search + web_fetch searches for current docs when fixes exhausted.

```python
def do_research(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    failing = {
        v.verification_id: v for v in state.verifications.values()
        if v.status == "failed" and v.attempts >= config.max_fix_attempts
    }
    if not failing:
        state.research_attempted_for_current_failures = True
        return False

    failure_context = [
        {"verification": v_id, "last_error": v.last_error,
         "attempt_history": v.attempt_history, "attempts": v.attempts}
        for v_id, v in failing.items()
    ]

    session = claude.session(AgentRole.RESEARCHER,
        system_extra="You are a research agent. Find CURRENT, ACCURATE information "
        "the loop doesn't have. Search for: library docs, GitHub issues, changelogs, "
        "workarounds. Focus on what CHANGED since training data."
    )

    prompt = load_prompt("research").format(
        FAILURES=json.dumps(failure_context, indent=2),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        VISION_SUMMARY=config.vision_file.read_text()[:2000],
    )

    response = session.send(prompt)

    # Research findings via report_research tool call
    if state.research_briefs and state.research_briefs[-1]["iteration"] == state.iteration:
        brief = state.research_briefs[-1]
        print(f"  Research found: {brief['topic']}")
        # Reset fix attempts so fixer can retry with new knowledge
        for v_id in failing:
            state.verifications[v_id].attempts = 0
        state.research_attempted_for_current_failures = True
        return True
    else:
        state.research_attempted_for_current_failures = True
        # Last resort: human insight
        print(f"\n  REQUESTING HUMAN INSIGHT — fixes and research exhausted")
        for v_id, v in failing.items():
            print(f"    - {v_id}: {v.last_error[:200] if v.last_error else 'unknown'}")
        insight = input("  Guidance (Enter to skip): ").strip()
        if insight:
            state.research_briefs.append({
                "topic": "Human insight", "findings": insight,
                "sources": ["human"], "iteration": state.iteration,
            })
            for v_id in failing:
                state.verifications[v_id].attempts = 0
            return True
        return False
```

### Research Brief Injection

```python
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
```

**Phase 3 update to do_fix**: Replace `RESEARCH_CONTEXT=""` with `RESEARCH_CONTEXT=get_research_context(state)` in the fix agent prompt.

---

## 4. Process Monitor (3-Layer)

### 4.1 Layer 0: Metric Collectors (every iteration, zero cost)

```python
def update_process_metrics(state: LoopState, action: str, made_progress: bool):
    """Update process monitor metrics from current state. Called every iteration."""
    pm = state.process_monitor
    alpha = 0.3  # from config.process_monitor_ema_alpha

    # Value velocity EMA
    vrc_scores = [v.value_score for v in state.vrc_history]
    vrc_delta = vrc_scores[-1] - vrc_scores[-2] if len(vrc_scores) >= 2 else 0
    pm.value_velocity_ema = alpha * vrc_delta + (1 - alpha) * pm.value_velocity_ema

    # Token efficiency EMA (approximate from total tokens and iteration count)
    if state.iteration > 1:
        avg_tokens_per_iter = state.total_tokens_used / state.iteration
        efficiency = vrc_delta / max(avg_tokens_per_iter, 1)
        pm.token_efficiency_ema = alpha * efficiency + (1 - alpha) * pm.token_efficiency_ema

    # CUSUM for efficiency deviation
    pm.cusum_efficiency = max(0, pm.cusum_efficiency + (pm.token_efficiency_ema - (vrc_delta / max(state.total_tokens_used / max(state.iteration, 1), 1))))

    # Task churn (retry_count tracking)
    for task in state.tasks.values():
        if task.retry_count >= 2:
            pm.churn_counts[task.task_id] = task.retry_count

    # Error hash tracking — derive from verification failures
    for v in state.verifications.values():
        if v.status == "failed" and v.failures:
            latest = v.failures[-1]
            h = hash_error(latest.stderr or latest.stdout or "unknown")
            if h not in pm.error_hashes:
                pm.error_hashes[h] = {"count": 0, "tasks": []}
            pm.error_hashes[h]["count"] = len([
                f for f in v.failures if hash_error(f.stderr or f.stdout or "unknown") == h
            ])

    # File touch tracking — derive from completed tasks
    for task in state.tasks.values():
        if task.status == "done":
            for f in task.files_created + task.files_modified:
                pm.file_touches[f] = pm.file_touches.get(f, 0) + 1
```

### 4.2 Layer 1: Trigger Evaluation (every iteration, zero cost)

```python
def evaluate_process_triggers(state, config) -> str:
    """Returns GREEN, YELLOW, or RED."""
    pm = state.process_monitor
    iteration = state.iteration

    # Guard: don't evaluate too early, during cooldown, or near budget end
    if iteration < config.process_monitor_min_iterations: return "GREEN"
    if iteration - pm.last_strategy_change_iteration < config.process_monitor_cooldown: return "GREEN"
    budget_pct = (state.total_tokens_used / config.token_budget * 100) if config.token_budget else 0
    if budget_pct >= 95: return "GREEN"

    triggers = []

    # Plateau: value velocity below threshold
    if pm.value_velocity_ema < config.pm_plateau_threshold:
        triggers.append(("plateau", "RED"))

    # Churn: task oscillating fail→fix→fail
    max_churn = max(pm.churn_counts.values(), default=0)
    if max_churn >= config.pm_churn_red: triggers.append(("churn", "RED"))
    elif max_churn >= config.pm_churn_yellow: triggers.append(("churn", "YELLOW"))

    # Error recurrence: same error hash N times
    max_error = max((e["count"] for e in pm.error_hashes.values()), default=0)
    if max_error >= config.pm_error_recurrence: triggers.append(("error_recurrence", "RED"))

    # Budget-value divergence
    value_pct = len([t for t in state.tasks.values() if t.status == "done"]) / max(len(state.tasks), 1) * 100
    if budget_pct > 0 and value_pct > 0 and budget_pct / value_pct >= config.pm_budget_value_ratio:
        triggers.append(("budget_divergence", "RED"))

    # File hotspot
    if pm.file_touches:
        max_touches = max(pm.file_touches.values())
        if max_touches > iteration * (config.pm_file_hotspot_pct / 100):
            triggers.append(("file_hotspot", "YELLOW"))

    if any(level == "RED" for _, level in triggers): return "RED"
    if any(level == "YELLOW" for _, level in triggers): return "YELLOW"
    return "GREEN"
```

### 4.3 Layer 2: Strategy Reasoner (Opus, RED trigger only)

```python
def maybe_run_strategy_reasoner(state, config, claude, action: str = "", made_progress: bool = True):
    pm = state.process_monitor

    # Layer 0: metrics (always) — derives from LoopState, no IterationResult needed
    update_process_metrics(state, action=action, made_progress=made_progress)

    # Layer 1: triggers (always)
    new_status = evaluate_process_triggers(state, config)
    pm.status = new_status

    if new_status != "RED":
        return

    # Layer 2: Opus Strategy Reasoner
    print(f"\n  PROCESS MONITOR — RED trigger, invoking Strategy Reasoner")

    session = claude.session(AgentRole.REASONER,
        system_extra=load_prompt("process_monitor").format(
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
            ITERATION=state.iteration,
            BUDGET_PCT=_budget_pct(state, config),
            CURRENT_STRATEGY=json.dumps(pm.current_strategy, indent=2),
            METRICS_DASHBOARD=format_metrics_dashboard(pm),
            TRIGGER_DETAILS=format_trigger_details(pm),
            WINDOW_SIZE=config.process_monitor_min_iterations * 2,
            EXECUTION_HISTORY=format_recent_history(state, window=config.process_monitor_min_iterations * 2),
            CURRENT_TEST_APPROACH=pm.current_strategy["test_approach"],
            CURRENT_FIX_APPROACH=pm.current_strategy["fix_approach"],
            CURRENT_EXECUTION_ORDER=pm.current_strategy["execution_order"],
            CURRENT_MAX_FIX=pm.current_strategy["max_fix_attempts"],
            CURRENT_RESEARCH_TRIGGER=pm.current_strategy["research_trigger"],
            CURRENT_SCOPE=pm.current_strategy["scope_per_task"],
            CURRENT_TRIAGE=pm.current_strategy["error_triage"],
        ),
    )

    session.send("Analyze process metrics and recommend strategy change.")

    # Result via report_strategy_change tool call
    change = state.agent_results.get("strategy_change")
    if change and change.get("action") == "STRATEGY_CHANGE":
        for dim, value in change["changes"].items():
            pm.current_strategy[dim] = value
        pm.last_strategy_change_iteration = state.iteration
        pm.strategy_history.append({
            "iteration": state.iteration,
            "changes": change["changes"],
            "reason": change["rationale"],
            "pattern": change["pattern"],
        })
        print(f"  Strategy changed: {change['changes']}")
    elif change and change.get("action") == "ESCALATE":
        print(f"  Process Monitor ESCALATION: {change['rationale']}")
```

### 4.4 Value Loop Integration

Add to value loop (after action dispatch, before VRC heartbeat):
```python
if state.pause is None and action != Action.EXIT_GATE:
    maybe_run_strategy_reasoner(state, config, claude,
                                 action=action.value, made_progress=progress)
```

The Decision Engine reads `state.process_monitor.current_strategy` for execution parameters (max_fix_attempts, execution_order, etc.).

---

## 5. Epic Decomposition + Feedback Checkpoint (R28-R30)

### 5.1 Vision Complexity Classification

Runs once, immediately after Vision Validation passes.

```python
def classify_vision_complexity(config: LoopConfig, claude: Claude, state: LoopState) -> str:
    """
    Classify vision as single_run or multi_epic.
    Uses Opus to assess complexity signals.
    Conservative: any complexity signal → multi_epic.
    """
    vision = config.vision_file.read_text()
    prd = config.prd_file.read_text()

    session = claude.session(AgentRole.REASONER,
        system_extra="Assess vision complexity. Count independently valuable "
        "deliverables, estimate task count, assess dependency depth and "
        "technology breadth. Be conservative — when in doubt, classify as multi_epic."
    )

    response = session.send(
        f"VISION:\n{vision}\n\nPRD:\n{prd}\n\n"
        f"Classify this vision as single_run or multi_epic.\n"
        f"Classification criteria (any one triggers multi_epic):\n"
        f"- >3 independently valuable deliverables\n"
        f"- >15 estimated tasks\n"
        f"- >2 layers of sequential dependencies\n"
        f"- >2 distinct technology domains\n"
        f"- Multiple external system integrations\n\n"
        f"Respond with ONLY 'single_run' or 'multi_epic' on the first line."
    )
    # Parse classification from agent response
    first_line = response.strip().split("\n")[0].strip().lower()
    classification = "multi_epic" if "multi_epic" in first_line else "single_run"
    state.vision_complexity = classification
    return classification
```

### 5.2 Epic Decomposition

For `multi_epic` visions only. Decomposes into 2-5 ordered epics.

```python
def decompose_into_epics(config: LoopConfig, claude: Claude, state: LoopState) -> list[Epic]:
    """
    Decompose a multi_epic vision into deliverable value blocks.
    Each epic delivers independently demonstrable value (horizontal slicing).
    Epic 1 is fully detailed; later epics are sketched.
    """
    vision = config.vision_file.read_text()
    prd = config.prd_file.read_text()
    prompt = load_prompt("epic_decompose")

    session = claude.session(AgentRole.REASONER,
        system_extra="Decompose this complex vision into 2-5 epics. "
        "Each epic must deliver independently demonstrable value. "
        "Use horizontal (value) slicing, not vertical (layer) slicing."
    )

    session.send(format_prompt(prompt, VISION=vision, PRD=prd,
        VISION_VALIDATION_RESULT=state.agent_results.get("vision_validation", "")))

    # Result via report_epic_decomposition tool call
    decomposition = state.agent_results.get("epic_decomposition")
    if decomposition and decomposition.get("vision_too_large"):
        print("  WARNING: Vision too large for 5 epics — recommend splitting into separate visions")

    epics = []
    for epic_data in decomposition.get("epics", []):
        epic = Epic(
            epic_id=epic_data["epic_id"],
            title=epic_data["title"],
            value_statement=epic_data["value_statement"],
            deliverables=epic_data["deliverables"],
            completion_criteria=epic_data["completion_criteria"],
            depends_on=epic_data.get("depends_on", []),
            detail_level=epic_data.get("detail_level", "sketch"),
            task_sketch=epic_data.get("task_sketch", []),
        )
        epics.append(epic)

    state.epics = epics
    return epics
```

### 5.3 Epic Feedback Checkpoint

Runs between epics, after the current epic's exit gate passes.

```python
def epic_feedback_checkpoint(
    config: LoopConfig, state: LoopState, claude: Claude, completed_epic: Epic
) -> str:
    """
    Present curated epic summary to human. Three options:
    - Proceed: deliver next value block (default, auto-proceed on timeout)
    - Adjust: re-plan next epic with human's notes
    - Stop: ship completed epics, exit

    Returns: "proceed" | "adjust" | "stop"
    """
    # Generate curated summary
    prompt = load_prompt("epic_feedback")
    session = claude.session(AgentRole.REASONER,
        system_extra="Generate a curated summary of this completed epic "
        "for the human to review. Focus on what was delivered, how it "
        "maps to the vision, and what comes next."
    )
    next_epic = state.epics[state.current_epic_index + 1] if state.current_epic_index + 1 < len(state.epics) else None

    session.send(format_prompt(prompt,
        EPIC_TITLE=completed_epic.title,
        EPIC_NUMBER=state.current_epic_index + 1,
        EPIC_TOTAL=len(state.epics),
        EPIC_VALUE_STATEMENT=completed_epic.value_statement,
        EPIC_COMPLETION_CRITERIA="\n".join(completed_epic.completion_criteria),
        NEXT_EPIC_TITLE=next_epic.title if next_epic else "N/A (final epic)",
        VRC_VALUE_SCORE=state.latest_vrc.value_score if state.latest_vrc else "N/A",
        VRC_VERIFIED=state.latest_vrc.deliverables_verified if state.latest_vrc else 0,
        VRC_TOTAL=state.latest_vrc.deliverables_total if state.latest_vrc else 0,
        VRC_GAPS=state.latest_vrc.gaps if state.latest_vrc else [],
    ))

    summary = state.agent_results.get("epic_summary", {})

    # Present to human
    print(f"\n{'=' * 60}")
    print(f"  EPIC {state.current_epic_index + 1}/{len(state.epics)} COMPLETE: {completed_epic.title}")
    print(f"{'=' * 60}")
    print(f"\n  {summary.get('summary', {}).get('vision_progress', '')}")
    print(f"\n  Confidence: {summary.get('summary', {}).get('confidence', 'N/A')}")
    if next_epic:
        print(f"\n  Next: {next_epic.title} — {next_epic.value_statement}")
    print(f"\n  Options: [P]roceed (default)  |  [A]djust  |  [S]top")

    timeout_min = config.epic_feedback_timeout_minutes
    if timeout_min > 0:
        print(f"  Auto-proceed in {timeout_min} minutes if no response.")

    # Wait for response (with timeout)
    response = wait_for_human_response(timeout_minutes=timeout_min)

    if response is None or response.lower().startswith("p"):
        completed_epic.feedback_response = "proceed" if response else "timeout"
        return "proceed"
    elif response.lower().startswith("a"):
        completed_epic.feedback_response = "adjust"
        notes = input("  Adjustment notes: ")
        completed_epic.feedback_notes = notes
        return "adjust"
    elif response.lower().startswith("s"):
        completed_epic.feedback_response = "stop"
        return "stop"
    else:
        completed_epic.feedback_response = "proceed"
        return "proceed"


def wait_for_human_response(timeout_minutes: int) -> str | None:
    """Wait for human input with timeout. Returns None on timeout."""
    import select
    import sys

    if timeout_minutes <= 0:
        return input("  > ")

    # Platform-appropriate timeout input
    # (Implementation varies by OS — see NF1)
    try:
        import msvcrt
        import time
        end_time = time.time() + timeout_minutes * 60
        chars = []
        while time.time() < end_time:
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                if char == '\r':
                    print()
                    return ''.join(chars) or None
                chars.append(char)
            time.sleep(0.1)
        print(f"\n  (timeout — auto-proceeding)")
        return None
    except ImportError:
        # Unix: use select
        ready, _, _ = select.select([sys.stdin], [], [], timeout_minutes * 60)
        if ready:
            return sys.stdin.readline().strip() or None
        print(f"\n  (timeout — auto-proceeding)")
        return None
```

### 5.4 Outer Epic Loop

For `multi_epic` visions, the entry point wraps the value loop in an epic loop:

```python
def run_epic_loop(config: LoopConfig, state: LoopState, claude: Claude):
    """
    Outer loop for multi_epic visions. Runs the value loop once per epic.
    For single_run visions, this is not called — run_value_loop runs directly.
    """
    for i, epic in enumerate(state.epics):
        state.current_epic_index = i
        epic.status = "in_progress"
        print(f"\n{'=' * 60}")
        print(f"  EPIC {i + 1}/{len(state.epics)}: {epic.title}")
        print(f"  Value: {epic.value_statement}")
        print(f"{'=' * 60}")

        # Refine epic detail if needed (just-in-time decomposition)
        if epic.detail_level == "sketch":
            refine_epic_detail(config, state, claude, epic)

        # Run pre-loop scoped to this epic's deliverables
        run_epic_preloop(config, state, claude, epic)

        # Run value loop for this epic
        run_value_loop(config, state, claude)

        # Mark epic complete
        epic.status = "completed"

        # Full coherence evaluation at epic boundary
        if config.coherence_full_at_epic_boundary:
            do_full_coherence_eval(config, state, claude)

        # Epic feedback checkpoint (skip for last epic)
        if i < len(state.epics) - 1:
            response = epic_feedback_checkpoint(config, state, claude, epic)
            if response == "stop":
                print("  Human requested stop. Shipping completed epics.")
                break
            elif response == "adjust":
                # Re-plan next epic with human's adjustment notes
                adjust_next_epic(config, state, claude, epic.feedback_notes)

    generate_delivery_report(config, state)
```

### 5.5 Utility Functions (Phase 3)

```python
def hash_error(error_text: str) -> str:
    """Hash an error message for deduplication. Strips line numbers, paths, timestamps."""
    import re, hashlib
    # Normalize: remove line numbers, file paths, timestamps
    normalized = re.sub(r'line \d+', 'line N', error_text)
    normalized = re.sub(r'[A-Z]:\\[^\s]+|/[^\s]+\.\w+', 'PATH', normalized)
    normalized = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', 'TIMESTAMP', normalized)
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def _budget_pct(state: LoopState, config: LoopConfig) -> float:
    """Calculate budget consumption percentage."""
    if not config.token_budget:
        return 0.0
    return (state.total_tokens_used / config.token_budget) * 100


def format_metrics_dashboard(pm: ProcessMonitorState) -> str:
    """Format process monitor metrics for the Strategy Reasoner."""
    lines = [
        f"Value velocity (EMA): {pm.value_velocity_ema:.4f}",
        f"Token efficiency (EMA): {pm.token_efficiency_ema:.6f}",
        f"CUSUM efficiency: {pm.cusum_efficiency:.4f}",
        f"Status: {pm.status}",
    ]
    if pm.churn_counts:
        top_churn = sorted(pm.churn_counts.items(), key=lambda x: -x[1])[:5]
        lines.append(f"Task churn (top 5): {', '.join(f'{k}={v}' for k, v in top_churn)}")
    if pm.error_hashes:
        top_errors = sorted(pm.error_hashes.items(), key=lambda x: -x[1]['count'])[:3]
        lines.append(f"Recurring errors: {len(pm.error_hashes)} unique, top: {', '.join(f'{k}({v[\"count\"]}x)' for k, v in top_errors)}")
    if pm.file_touches:
        hotspots = sorted(pm.file_touches.items(), key=lambda x: -x[1])[:5]
        lines.append(f"File hotspots: {', '.join(f'{k}({v}x)' for k, v in hotspots)}")
    return "\n".join(lines)


def format_trigger_details(pm: ProcessMonitorState) -> str:
    """Format trigger details for the Strategy Reasoner."""
    # Triggers are evaluated in evaluate_process_triggers — we summarize what fired
    return f"Process monitor status: {pm.status}"


def format_recent_history(state: LoopState, window: int = 10) -> str:
    """Format recent execution history for the Strategy Reasoner."""
    recent = state.progress_log[-window:]
    if not recent:
        return "No execution history yet."
    lines = []
    for entry in recent:
        lines.append(f"  [{entry['iteration']}] {entry['action']}: {entry['result']}")
    return "\n".join(lines)


def refine_epic_detail(config: LoopConfig, state: LoopState, claude: Claude, epic: Epic):
    """Just-in-time decomposition for sketch-level epics."""
    session = claude.session(AgentRole.REASONER,
        system_extra="Refine this epic sketch into detailed tasks. "
        "Consider what was learned from previous epics."
    )
    prompt = format_prompt(load_prompt("plan"),
        VISION=config.vision_file.read_text(),
        PRD=config.prd_file.read_text(),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
    )
    session.send(f"Refine epic '{epic.title}' into detailed tasks:\n"
                 f"Value: {epic.value_statement}\n"
                 f"Deliverables: {', '.join(epic.deliverables)}\n"
                 f"Task sketch: {', '.join(epic.task_sketch)}\n\n{prompt}")
    epic.detail_level = "full"


def run_epic_preloop(config: LoopConfig, state: LoopState, claude: Claude, epic: Epic):
    """Run pre-loop steps scoped to an epic's deliverables."""
    # Plan generation for this epic — agent creates tasks via manage_task tool
    session = claude.session(AgentRole.REASONER)
    prompt = load_prompt("plan").format(
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
    )
    session.send(f"Generate tasks for epic '{epic.title}':\n"
                 f"Value: {epic.value_statement}\n"
                 f"Deliverables: {', '.join(epic.deliverables)}\n"
                 f"Task sketch: {', '.join(epic.task_sketch)}\n\n{prompt}",
                 task_source="plan")

    # Tag newly created tasks with this epic's ID (decision engine uses this for scoping)
    for task in state.tasks.values():
        if not task.epic_id and task.status == "pending":
            task.epic_id = epic.epic_id

    # Re-run quality gates for epic's tasks
    run_quality_gates(config, state, claude)


def adjust_next_epic(config: LoopConfig, state: LoopState, claude: Claude, notes: str):
    """Re-plan next epic incorporating human's adjustment notes."""
    next_idx = state.current_epic_index + 1
    if next_idx >= len(state.epics):
        return
    next_epic = state.epics[next_idx]
    session = claude.session(AgentRole.REASONER)
    session.send(
        f"Adjust the next epic based on human feedback:\n"
        f"Epic: {next_epic.title}\n"
        f"Human's notes: {notes}\n"
        f"Revise the epic's task sketch and deliverables accordingly."
    )
```

---

## 6. Full Coherence Evaluation (R32)

Replaces Phase 2 stub. All 7 dimensions evaluated by Opus.

```python
def do_full_coherence_eval(config: LoopConfig, state: LoopState, claude: Claude) -> CoherenceReport:
    """
    Full 7-dimension coherence evaluation using Opus.
    Runs at epic boundaries and pre-exit-gate.
    """
    prompt = load_prompt("coherence_eval")
    previous = state.coherence_history[-1] if state.coherence_history else None

    session = claude.session(AgentRole.EVALUATOR,
        system_extra="Evaluate system-level coherence across all 7 dimensions. "
        "Focus on emergent properties: issues that arise from feature INTERACTIONS, "
        "not from any individual feature being wrong."
    )

    session.send(format_prompt(prompt,
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        EVAL_MODE="full",
        ITERATION=state.iteration,
        FEATURE_COUNT=sum(1 for t in state.tasks.values() if t.status == "done"),
        PREVIOUS_REPORT=json.dumps(previous.__dict__) if previous else "None (first evaluation)",
    ))

    # Result via report_coherence tool call
    result = state.agent_results.get("coherence")
    if result:
        report = CoherenceReport(
            iteration=state.iteration,
            mode="full",
            timestamp=datetime.now().isoformat(),
            dimensions=result.get("dimensions", {}),
            overall=result.get("overall", "HEALTHY"),
            top_findings=result.get("top_findings", []),
        )
        state.coherence_history.append(report)
        state.tasks_since_last_coherence = 0

        if report.overall == "CRITICAL":
            print(f"  COHERENCE CRITICAL — system-level issues detected")
            # Findings will trigger Course Correction via decision engine
        return report
```

---

## 7. Migration Checklist (Phase 3)

### Vision Refinement (Interactive)
- [ ] Add `RefinementRound` and `RefinementState` dataclasses to `state.py`
- [ ] Add `vision_refinement` and `prd_refinement` fields to `LoopState`
- [ ] Implement `refine_vision()` in `phases/preloop.py` (replace stub)
- [ ] Implement `run_vision_analysis()` — the 5-pass analytical core
- [ ] Implement `research_vision_alternative()` — Researcher agent for HARD issues
- [ ] Implement `present_vision_brief()` — terminal output formatting
- [ ] Implement `_vision_prompt_loop()` — human interaction with input validation
- [ ] Implement `refine_prd()` in `phases/preloop.py` (replace stub)
- [ ] Implement `_prd_prompt_loop()` — PRD negotiation interaction
- [ ] Create prompt: `vision_validate.md` (5-pass framework with HARD/SOFT classification)
- [ ] Add report_vision_validation structured tool schema + handler (verdict: PASS/NEEDS_REVISION, issues with severity)
- [ ] Verify `state.save()` is called after every expensive operation (analysis, research) and before blocking on human input
- [ ] Test: crash after analysis → resumes at prompt, doesn't re-run 5 passes
- [ ] Test: crash after research → resumes at prompt with research results preserved
- [ ] Test: run on a flawed Vision → NEEDS_REVISION with HARD issues, human revises, re-validates → PASS
- [ ] Test: run on a risky Vision → NEEDS_REVISION with SOFT issues only, human acknowledges → PASS
- [ ] Test: PRD REJECT → researches alternatives, human revises, re-critique → APPROVE
- [ ] Test: round history preserved in state after multi-round refinement

### Critical Evaluation
- [x] Implement `phases/critical_eval.py` — do_critical_eval with conditional browser injection
- [x] Create prompt: `critical_eval.md` (Evaluator agent — be the user, with `{BROWSER_SECTION}` placeholder)
- [x] Create prompt: `critical_eval_browser.md` (Playwright MCP browser evaluation instructions)
- [x] Add `_needs_browser_eval()` predicate + `_build_playwright_config()` helper
- [x] Add report_eval_finding structured tool schema + handle_eval_finding
- [x] Wire into value loop (every N tasks + all-pass trigger)
- [x] Verify Evaluator gets read-only tools by default, Playwright MCP tools for web apps
- [x] Add `browser_eval_headless` and `browser_eval_viewport` to LoopConfig
- [x] Add `PLAYWRIGHT_MCP_TOOLS` constant + `mcp_servers`/`extra_tools` plumbing in `claude.py`
- [x] E2E test: smart-dash sprint — evaluator opened browser, took 20+ screenshots, found 4 UX issues

### External Research
- [ ] Implement `phases/research.py` — do_research (replace stub)
- [ ] Implement get_research_context() for fix agent injection
- [ ] Create prompt: `research.md`
- [ ] Add report_research structured tool schema + handler
- [ ] Add provider tools (web_search, web_fetch) to RESEARCHER role
- [ ] Update fix agent prompt: inject `{RESEARCH_CONTEXT}`

### Process Monitor
- [ ] Create `phases/process_monitor.py` — ProcessMonitorState already in state (Phase 1)
- [ ] Implement update_process_metrics (Layer 0)
- [ ] Implement evaluate_process_triggers (Layer 1)
- [ ] Implement maybe_run_strategy_reasoner (Layer 2)
- [ ] Create prompt: `process_monitor.md` (Strategy Reasoner)
- [ ] Add report_strategy_change structured tool schema + handler
- [ ] Wire into value loop (after action, before VRC)
- [ ] Update decision engine to read current_strategy for execution params

### Epic Decomposition + Feedback
- [ ] Implement classify_vision_complexity in `phases/epic.py` (replace stub)
- [ ] Implement decompose_into_epics in `phases/epic.py` (replace stub)
- [ ] Implement epic_feedback_checkpoint in `phases/epic.py` (replace stub)
- [ ] Implement run_epic_loop — outer loop wrapping value loop
- [ ] Implement refine_epic_detail — just-in-time decomposition for sketch epics
- [ ] Implement wait_for_human_response — platform-aware timeout input
- [ ] Create prompt: `epic_decompose.md` (value-slice decomposition)
- [ ] Create prompt: `epic_feedback.md` (curated epic summary)
- [ ] Add report_epic_decomposition structured tool schema + handler
- [ ] Add report_epic_summary structured tool schema + handler
- [ ] Add Epic dataclass to state module
- [ ] Verify epic loop dispatch in main() works (wired in Phase 1 with conditional on vision_complexity)

### Full Coherence Evaluation
- [ ] Implement do_full_coherence_eval in `phases/coherence.py` (replace Phase 1 stub)
- [ ] Create prompt: `coherence_eval.md` (7-dimension evaluation)
- [ ] Wire full coherence into epic boundaries and pre-exit-gate
- [ ] Verify COHERENCE_EVAL action in decision engine (P8b wired in Phase 1, clears coherence_critical_pending)

### Integration
- [ ] Test Vision Validation end-to-end (5-pass with real Vision)
- [ ] Test Vision Complexity Classification (simple → single_run, complex → multi_epic)
- [ ] Test Epic Decomposition (verify horizontal value slicing)
- [ ] Test Epic Feedback Checkpoint (proceed, adjust, stop, and timeout)
- [ ] Test Critical Eval (verify it creates tasks for issues)
- [ ] Test Research (verify web search fires and brief injects)
- [ ] Test Process Monitor (force RED trigger, verify strategy changes)
- [ ] Test Full Coherence Evaluation (verify 7-dimension report)
- [ ] Full E2E: run complete loop through all phases (single_run)
- [ ] Full E2E: run complete loop with multi_epic vision

---

## Appendix: Phase 3 Structured Tool Schemas

### report_eval_finding
```python
{"name": "report_eval_finding", "input_schema": {"properties": {
    "severity": {"type": "string", "enum": ["critical","blocking","degraded","polish"]},
    "description": {"type": "string"},
    "user_impact": {"type": "string"},
    "suggested_fix": {"type": "string"},
    "evidence": {"type": "string"},
}, "required": ["severity", "description", "user_impact"]}}
```

### report_research
```python
{"name": "report_research", "input_schema": {"properties": {
    "topic": {"type": "string"},
    "findings": {"type": "string"},
    "sources": {"type": "array", "items": {"type": "string"}},
    "affected_verifications": {"type": "array", "items": {"type": "string"}},
}, "required": ["topic", "findings", "sources"]}}
```

### report_vision_validation
```python
{"name": "report_vision_validation", "input_schema": {"properties": {
    "verdict": {"type": "string", "enum": ["PASS","NEEDS_REVISION"]},
    "dimensions": {"type": "object", "properties": {
        "outcome_grounded": {"type": "string", "enum": ["STRONG","ADEQUATE","WEAK","CRITICAL"]},
        "adoption_realistic": {"type": "string", "enum": ["STRONG","ADEQUATE","WEAK","CRITICAL"]},
        "causally_sound": {"type": "string", "enum": ["STRONG","ADEQUATE","WEAK","CRITICAL"]},
        "failure_aware": {"type": "string", "enum": ["STRONG","ADEQUATE","WEAK","CRITICAL"]},
    }},
    "strengths": {"type": "array", "items": {"type": "string"}},
    "issues": {"type": "array", "items": {"type": "object", "properties": {
        "id": {"type": "string"},
        "severity": {"type": "string", "enum": ["hard", "soft"]},
        "category": {"type": "string", "enum": [
            "impossible", "contradictory", "no_problem", "all_activity", "no_mechanism",
            "weak_evidence", "adoption_risk", "gameable_metric", "unaddressed_failure", "missing_mechanism"
        ]},
        "description": {"type": "string"},
        "evidence": {"type": "string"},
        "suggested_revision": {"type": "string"},
    }, "required": ["id", "severity", "category", "description", "evidence"]}},
    "kill_criteria": {"type": "array", "items": {"type": "string"}},
    "reason": {"type": "string"},
}, "required": ["verdict", "reason", "issues", "strengths"]}}
```

### report_strategy_change
```python
{"name": "report_strategy_change", "input_schema": {"properties": {
    "pattern": {"type": "string", "enum": ["plateau","churn","efficiency_collapse",
                "category_clustering","budget_divergence","file_hotspot"]},
    "cause": {"type": "string"},
    "evidence": {"type": "array", "items": {"type": "string"}},
    "action": {"type": "string", "enum": ["STRATEGY_CHANGE","ESCALATE","CONTINUE"]},
    "changes": {"type": "object"},
    "rationale": {"type": "string"},
    "re_evaluate_after": {"type": "integer", "minimum": 3},
}, "required": ["pattern", "cause", "evidence", "action", "rationale", "re_evaluate_after"]}}
```

### report_epic_decomposition
```python
{"name": "report_epic_decomposition", "input_schema": {"properties": {
    "epic_count": {"type": "integer", "minimum": 2, "maximum": 5},
    "epics": {"type": "array", "items": {"type": "object", "properties": {
        "epic_id": {"type": "string"},
        "title": {"type": "string"},
        "value_statement": {"type": "string"},
        "deliverables": {"type": "array", "items": {"type": "string"}},
        "completion_criteria": {"type": "array", "items": {"type": "string"}},
        "depends_on": {"type": "array", "items": {"type": "string"}},
        "detail_level": {"type": "string", "enum": ["full", "moderate", "sketch"]},
        "key_risks": {"type": "array", "items": {"type": "string"}},
        "task_sketch": {"type": "array", "items": {"type": "string"}},
        "estimated_task_count": {"type": "integer"},
    }, "required": ["epic_id", "title", "value_statement", "deliverables", "completion_criteria"]}},
    "vision_too_large": {"type": "boolean"},
    "rationale": {"type": "string"},
}, "required": ["epic_count", "epics", "vision_too_large", "rationale"]}}
```

### report_epic_summary
```python
{"name": "report_epic_summary", "input_schema": {"properties": {
    "epic_id": {"type": "string"},
    "summary": {"type": "object", "properties": {
        "delivered": {"type": "array", "items": {"type": "string"}},
        "vision_progress": {"type": "string"},
        "adjustments": {"type": "array", "items": {"type": "string"}},
        "next_epic": {"type": "object", "properties": {
            "title": {"type": "string"},
            "value_statement": {"type": "string"},
            "key_deliverables": {"type": "array", "items": {"type": "string"}},
            "risks": {"type": "array", "items": {"type": "string"}},
        }},
        "confidence": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
        "confidence_rationale": {"type": "string"},
    }},
    "vrc_snapshot": {"type": "object", "properties": {
        "value_score": {"type": "number"},
        "deliverables_verified": {"type": "integer"},
        "deliverables_total": {"type": "integer"},
        "gaps": {"type": "array"},
    }},
}, "required": ["epic_id", "summary"]}}
```
