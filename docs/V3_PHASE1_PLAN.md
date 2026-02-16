# Loop V3: Phase 1 Plan — Builder + QC + Decision Engine (MVP)

**Date**: 2026-02-15
**Architecture**: V3_ARCHITECTURE.md (data model, agent roles, tools, decision priorities)
**Requirements**: V3_PRD.md (R1-R16, R25-R27)

---

## Scope

### What Phase 1 Delivers
- **Pre-loop**: Input validation, context discovery, PRD critique, plan generation, quality gates, blocker resolution, preflight
- **Value loop**: Execute → QC → Fix → Interactive Pause, with continuous regression
- **Infrastructure**: State persistence, rendered views, task mutation guardrails, tool dispatch
- **Exit condition**: All tasks done + all QC passing (simple completion)

### What Phase 1 Does NOT Include
- VRC heartbeat (Phase 2) — stubbed, returns CONTINUE
- Course correction (Phase 2) — stubbed, logs and continues
- Exit gate (Phase 2) — stubbed, always passes
- Critical evaluation (Phase 3) — stubbed, no-op
- External research (Phase 3) — stubbed, marks as attempted
- Process monitor (Phase 3) — stubbed, no-op
- Vision validation (Phase 3) — stubbed, auto-PASS
- Full coherence eval (Phase 3) — stubbed, no-op (quick coherence added in Phase 2)

Phase 2/3 handlers are stubs from day 1. The decision engine implements the FULL priority table (see Architecture Reference). Only the handlers evolve across phases.

---

## 1. Common Pattern: Agent Sessions

All agent interactions follow the same pattern:

```python
def invoke_agent(claude, role, prompt_name, format_kwargs, task_source="agent"):
    """
    Standard agent invocation:
    1. Create session with role (determines model + thinking + tools)
    2. Load and format prompt template
    3. Send message — agent executes tools in multi-turn loop
    4. Results captured via structured tool handlers → state mutations
    """
    session = claude.session(role, system_extra=ROLE_PREAMBLES.get(role, ""))
    prompt = load_prompt(prompt_name).format(**format_kwargs)
    response = session.send(prompt, task_source=task_source)
    return response
```

Structured tools (manage_task, report_discovery, etc.) update `LoopState` directly via handlers. The orchestrator reads results from `state.agent_results[key]` or from state mutations.

---

## 2. ClaudeSession Implementation

```python
STREAMING_THRESHOLD = 21333
# Context window limits per model (input tokens — conservative 80% threshold)
CONTEXT_LIMITS = {
    "claude-opus-4-6": 200_000,
    "claude-sonnet-4-5-20250929": 200_000,
    "claude-haiku-4-5-20251001": 200_000,
}
CONTEXT_WARN_PCT = 0.80  # warn and summarize at 80% of context window

class ClaudeSession:
    def __init__(self, client, model, system, max_turns=30,
                 thinking_effort=None, max_tokens=16384,
                 tools=None, state=None, betas=None):
        self.client = client
        self.model = model
        self.system = system
        self.messages = []
        self.max_turns = max_turns
        self.thinking_effort = thinking_effort
        self.max_tokens = max_tokens
        self.tools = tools or []
        self.state = state
        self.betas = betas
        self.use_streaming = max_tokens > STREAMING_THRESHOLD
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.context_limit = CONTEXT_LIMITS.get(model, 200_000)

    def send(self, user_message: str, task_source: str = "agent") -> str:
        """Send message, execute tools in loop, return final text."""
        self.messages.append({"role": "user", "content": user_message})

        for turn in range(self.max_turns):
            # Context window guard (NF4): if approaching limit, truncate early messages
            if self.total_input_tokens > self.context_limit * CONTEXT_WARN_PCT:
                self._truncate_context()

            kwargs = dict(
                model=self.model, max_tokens=self.max_tokens,
                system=self.system, messages=self.messages, tools=self.tools,
            )
            if self.betas:
                kwargs["betas"] = self.betas
            if self.thinking_effort:
                kwargs["thinking"] = {"type": "adaptive"}
                kwargs["output_config"] = {"effort": self.thinking_effort}

            api = self.client.beta.messages if self.betas else self.client.messages
            response = self._api_call_with_retry(api, kwargs)

            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens
            if self.state:
                self.state.total_tokens_used += (
                    response.usage.input_tokens + response.usage.output_tokens
                )

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "pause_turn":
                continue  # server-side tool loop hit limit, re-send as-is

            # Process tool_use blocks BEFORE checking end_turn — ensures final
            # tool calls are executed even when the model ends in the same turn.
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input, self.state,
                                          task_source=task_source)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            if tool_results:
                self.messages.append({"role": "user", "content": tool_results})
            elif response.stop_reason == "end_turn":
                # No tool calls and model is done — return final text
                return self._extract_text(response)

            # If tool calls were processed AND stop_reason is end_turn, continue
            # to let the model see the tool results (it may want to respond).
            # If stop_reason is tool_use, the loop naturally continues.

        raise RuntimeError(f"Agent exceeded max_turns ({self.max_turns})")

    def _send_streaming(self, api=None, **kwargs):
        target = api or self.client.messages
        with target.stream(**kwargs) as stream:
            return stream.get_final_message()

    def _extract_text(self, response):
        return "\n".join(b.text for b in response.content if hasattr(b, "text"))

    def _api_call_with_retry(self, api, kwargs, max_retries=3) -> "Message":
        """
        Wrap API call with retry + exponential backoff.
        Handles rate limits (429), overload (529), timeouts, and transient network errors.
        """
        import time
        from anthropic import APIStatusError, APITimeoutError, APIConnectionError

        for attempt in range(max_retries + 1):
            try:
                if self.use_streaming:
                    return self._send_streaming(api=api, **kwargs)
                else:
                    return api.create(**kwargs)
            except (APITimeoutError, APIConnectionError) as e:
                if attempt == max_retries:
                    raise
                wait = 2 ** attempt  # 1s, 2s, 4s
                print(f"  API transient error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
            except APIStatusError as e:
                if e.status_code in (429, 529) and attempt < max_retries:
                    retry_after = int(e.response.headers.get("retry-after", 2 ** attempt))
                    print(f"  API {e.status_code} (attempt {attempt + 1}/{max_retries + 1})")
                    print(f"  Retrying in {retry_after}s...")
                    time.sleep(retry_after)
                else:
                    raise  # 4xx/5xx that aren't retryable
        raise RuntimeError("Retry loop exited without returning or raising")

    def _truncate_context(self):
        """
        Truncate conversation history when approaching context window limit (NF4).
        Preserves: first user message (original prompt), last 4 exchanges (recent context).
        Replaces middle with a summary marker.
        """
        if len(self.messages) <= 6:
            return  # too few messages to truncate
        # Keep first message (system context) and last 4 message pairs
        preserved_start = self.messages[:1]
        preserved_end = self.messages[-4:]
        removed_count = len(self.messages) - 5
        summary = {"role": "user", "content": f"[{removed_count} earlier messages truncated to stay within context window]"}
        self.messages = preserved_start + [summary] + preserved_end
        print(f"  CONTEXT MANAGEMENT: truncated {removed_count} messages (token usage at {self.total_input_tokens:,})")
```

---

## 3. Pre-Loop

### 3.1 Input Validation

```python
def validate_inputs(config: LoopConfig) -> bool:
    for f in [config.vision_file, config.prd_file]:
        if not f.exists():
            print(f"MISSING: {f}")
            return False
        if f.stat().st_size < 100:
            print(f"WARNING: {f} seems too short ({f.stat().st_size} bytes)")
    return True
```

### 3.2 Vision Refinement (Phase 3 — stub)

```python
def refine_vision(config: LoopConfig, state: LoopState, claude: Claude) -> dict:
    """Phase 3 implements interactive vision refinement. Phase 1: auto-PASS."""
    return {"verdict": "PASS", "reason": "Vision Refinement not yet implemented (Phase 3)"}

def refine_prd(config: LoopConfig, state: LoopState, claude: Claude) -> dict:
    """Phase 3 implements interactive PRD refinement. Phase 1: run critique, auto-approve."""
    session = claude.session(AgentRole.REASONER)
    prompt = load_prompt("prd_critique").format(
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
    )
    session.send(prompt)
    critique = state.agent_results.get("critique", {})
    # Phase 1: if REJECT, warn but proceed (Phase 3 adds interactive negotiation)
    if critique.get("verdict") == "REJECT":
        print(f"  WARNING: PRD critique returned REJECT: {critique.get('reason', '')}")
        print(f"  Phase 3 will add interactive refinement. Proceeding for now.")
        critique["verdict"] = "DESCOPE"
    return critique

def classify_vision_complexity(config: LoopConfig, claude: Claude, state: LoopState) -> str:
    """Phase 3 implements Opus-driven assessment. Phase 1: always single_run."""
    state.vision_complexity = "single_run"
    return "single_run"

def decompose_into_epics(config: LoopConfig, claude: Claude, state: LoopState) -> list:
    """Phase 3 implements value-block decomposition. Phase 1: no-op (only single_run)."""
    return []
```

### 3.3 Pre-Loop Steps

Each step follows the common agent pattern. Specifics:

| Step | Prompt | Role | Tool | State Key |
|------|--------|------|------|-----------|
| Context Discovery | `discover_context.md` | REASONER | `report_discovery` | `state.context` |
| PRD Critique | `prd_critique.md` | REASONER | `report_critique` | `state.agent_results["critique"]` |
| Plan Generation | `plan.md` | REASONER | `manage_task` | `state.tasks` |

**Context Discovery** format kwargs: `SPRINT`, `SPRINT_DIR` (agent reads Vision/PRD from disk)
**PRD Critique** format kwargs: `SPRINT_CONTEXT` (json), `SPRINT`, `SPRINT_DIR` (agent reads Vision/PRD from disk)
**Plan Generation** format kwargs: `SPRINT_CONTEXT` (json), `SPRINT`, `SPRINT_DIR` (agent reads Vision/PRD from disk)

After plan generation, render the snapshot: `config.plan_file.write_text(render_plan_markdown(state))`

### 3.4 Quality Gates

```python
QUALITY_GATES = [
    ("craap",     "craap",            "CRAAP Review"),
    ("clarity",   "clarity",          "CLARITY Protocol"),
    ("validate",  "validate",         "VALIDATE Sprint"),
    ("connect",   "connect",          "CONNECT Review"),
    ("break",     "break",            "BREAK"),
    ("prune",     "prune",            "PRUNE Review"),
    ("tidy",      "tidy",             "TIDY-FIRST"),
    ("blockers",  "verify_blockers",  "Blocker Validation"),
    ("vrc_init",  "vrc",              "Initial VRC"),
    ("preflight", "preflight",        "Preflight Check"),
]

def run_quality_gates(config, state, claude) -> bool:
    for gate_name, prompt_name, display_name in QUALITY_GATES:
        if state.gate_passed(gate_name):
            continue
        result = run_gate_with_remediation(
            gate_name, prompt_name, display_name,
            config, state, claude, max_retries=3,
        )
        render_plan_snapshot(config, state)
        state.save(config.state_file)
        if not result.passed:
            print(f"  GATE FAILED: {display_name}")
            return False
    return True
```

Each gate agent uses `manage_task` to remediate issues found. After each gate, re-render the plan markdown from state.

### 3.5 Complete Pre-Loop Flow

```python
def run_preloop(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    print("=" * 60)
    print("  PRE-LOOP: Qualifying the work")
    print("=" * 60)

    # Step 1: Inputs exist
    if not validate_inputs(config):
        return False

    # Step 2: Vision Refinement (Phase 3 — stub auto-passes)
    # In Phase 3, this becomes an interactive refinement loop that
    # negotiates with the human until consensus. Never exits silently.
    if not state.gate_passed("vision_validated"):
        validation = refine_vision(config, state, claude)
        # refine_vision() only returns on consensus (PASS or acknowledged)
        # If user wants to quit, refine_vision() calls sys.exit(0)
        state.pass_gate("vision_validated")
        state.save(config.state_file)

    # Step 2b: Classify vision complexity (Phase 3 — stub returns "single_run")
    if not state.gate_passed("vision_classified"):
        complexity = classify_vision_complexity(config, claude, state)
        print(f"  Vision complexity: {complexity}")
        state.pass_gate("vision_classified")
        state.save(config.state_file)

    # Step 2c: Epic decomposition if multi_epic (Phase 3 — stub no-ops)
    if state.vision_complexity == "multi_epic" and not state.gate_passed("epics_decomposed"):
        epics = decompose_into_epics(config, claude, state)
        print(f"  Decomposed into {len(epics)} epics")
        state.pass_gate("epics_decomposed")
        state.save(config.state_file)

    # Step 3: Context Discovery
    if not state.gate_passed("context_discovered"):
        session = claude.session(AgentRole.REASONER)
        prompt = load_prompt("discover_context").format(
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
        )
        session.send(prompt)
        # report_discovery tool handler populates state.context
        if state.context.unresolved_questions:
            print("  DISCOVERY needs clarification:")
            for q in state.context.unresolved_questions:
                print(f"    ? {q}")
        state.pass_gate("context_discovered")
        state.save(config.state_file)

    # Step 4: PRD Refinement (Phase 3 — stub auto-approves)
    # In Phase 3, REJECT triggers interactive negotiation loop.
    # Loop researches feasible alternatives, human revises, re-critiques.
    if not state.gate_passed("prd_critique"):
        critique = refine_prd(config, state, claude)
        # refine_prd() only returns on achievable verdict (APPROVE/AMEND/DESCOPE)
        # If user wants to quit, refine_prd() calls sys.exit(0)
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
    if not run_quality_gates(config, state, claude):
        return False

    # Step 7: Blocker check
    blocked = [t for t in state.tasks.values()
               if t.status == "blocked"
               and not t.blocked_reason.startswith("HUMAN_ACTION:")]
    if blocked:
        print("BLOCKED: Unresolved pre-conditions")
        for t in blocked:
            print(f"  - {t.task_id}: {t.blocked_reason}")
        return False

    print("\n  PRE-LOOP COMPLETE — entering value delivery loop")
    state.phase = "value_loop"
    state.save(config.state_file)
    return True
```

---

## 4. Decision Engine

The FULL priority table from the Architecture Reference. Phase 2/3 actions route to stub handlers until those phases are implemented.

```python
class Action(Enum):
    EXECUTE = "execute"
    GENERATE_QC = "generate_qc"
    RUN_QC = "run_qc"
    FIX = "fix"
    CRITICAL_EVAL = "critical_eval"
    COURSE_CORRECT = "course_correct"
    RESEARCH = "research"
    INTERACTIVE_PAUSE = "interactive_pause"
    SERVICE_FIX = "service_fix"
    COHERENCE_EVAL = "coherence_eval"
    EXIT_GATE = "exit_gate"


def _scoped_tasks(state: LoopState) -> dict[str, "TaskState"]:
    """Return tasks scoped to the current epic (or all tasks for single_run)."""
    if state.vision_complexity != "multi_epic" or not state.epics:
        return state.tasks
    current_epic_id = state.epics[state.current_epic_index].epic_id if state.current_epic_index < len(state.epics) else ""
    return {tid: t for tid, t in state.tasks.items()
            if not t.epic_id or t.epic_id == current_epic_id}


def decide_next_action(config: LoopConfig, state: LoopState) -> Action:
    """Deterministic decision engine. No LLM. Pure state analysis."""

    # P0: Paused for human action
    if state.pause is not None:
        return Action.INTERACTIVE_PAUSE

    # P1: Services must be running
    if state.context.services and not all_services_healthy(config, state):
        return Action.SERVICE_FIX

    # P2: Stuck → course correct (Phase 2 implements real CC; Phase 1 stub logs)
    # Enforce max_course_corrections — if exhausted, trigger interactive pause for human help
    course_correction_count = len(state.progress_log_count("course_correct"))
    if state.is_stuck(config):
        if course_correction_count >= config.max_course_corrections:
            # Exhausted all course corrections — escalate to human
            if state.pause is None:
                state.pause = PauseState(
                    reason=f"Loop stuck after {config.max_course_corrections} course corrections",
                    instructions="The loop has exhausted its automatic recovery options. "
                                 "Please review the current state and provide guidance.",
                    requested_at=datetime.now().isoformat(),
                )
            return Action.INTERACTIVE_PAUSE
        return Action.COURSE_CORRECT

    # Scope task queries to current epic for multi_epic visions
    scoped = _scoped_tasks(state)
    done_count = len([t for t in scoped.values() if t.status == "done"])
    pending_tasks = [t for t in scoped.values() if t.status == "pending"]

    # P3: Generate QC early (only if not already attempted)
    if (not state.verifications
            and done_count >= config.generate_verifications_after
            and state.gate_passed("plan_generated")
            and not state.gate_passed("verifications_generated")):
        return Action.GENERATE_QC

    # P4: Fix failing QC
    failing = [v for v in state.verifications.values() if v.status == "failed"]
    if failing:
        fixable = [v for v in failing if v.attempts < config.max_fix_attempts]
        if fixable:
            return Action.FIX
        # Exhausted → research (Phase 3 stub), then course correct (Phase 2 stub)
        if not state.research_attempted_for_current_failures:
            return Action.RESEARCH
        return Action.COURSE_CORRECT

    # P5: Human blocked task
    human_blocked = [t for t in state.tasks.values()
                     if t.status == "blocked" and t.blocked_reason.startswith("HUMAN_ACTION:")]
    if human_blocked:
        return Action.INTERACTIVE_PAUSE

    # P6: Pending tasks — only if at least one is ready (dependencies met)
    # Descoped dependencies count as satisfied — the task proceeds without them
    ready = [t for t in pending_tasks
             if all(state.tasks.get(dep, TaskState(task_id="")).status in ("done", "descoped")
                    for dep in (t.dependencies or []))]
    if ready:
        return Action.EXECUTE
    # All pending but none ready — may be blocked or have circular deps
    if pending_tasks:
        return Action.COURSE_CORRECT

    # P7: QC pending
    pending_v = [v for v in state.verifications.values() if v.status == "pending"]
    if pending_v:
        return Action.RUN_QC

    # P8: Critical eval due (Phase 3 stub)
    crit_eval_due = (
        state.tasks_since_last_critical_eval >= config.critical_eval_interval
        or (config.critical_eval_on_all_pass
            and all(v.status == "passed" for v in state.verifications.values()
                    if v.status != "blocked")
            and state.verifications
            and not any(vrc.value_score >= 0.9 for vrc in state.vrc_history))
    )
    if crit_eval_due:
        return Action.CRITICAL_EVAL

    # P8b: Coherence eval due (Phase 3 stub — quick coherence runs inline in Phase 2)
    # Triggered when: (a) quick coherence found CRITICAL, or (b) full eval is due at epic boundary
    if getattr(state, "coherence_critical_pending", False):
        return Action.COHERENCE_EVAL

    # P9: All done + all passing → exit gate (Phase 2 stub always passes)
    # Also allows exit when QC generation failed (no verifications exist but all tasks done)
    all_pass = all(v.status == "passed" for v in state.verifications.values()
                   if v.status != "blocked")
    if not pending_tasks:
        if state.verifications and all_pass:
            return Action.EXIT_GATE
        if not state.verifications and state.gate_passed("verifications_generated"):
            print("  WARNING: No verifications exist (QC generation produced nothing). Exiting with warning.")
            return Action.EXIT_GATE

    return Action.COURSE_CORRECT
```

---

## 5. Value Loop

```python
def run_value_loop(config: LoopConfig, state: LoopState, claude: Claude):
    print("\n" + "=" * 60)
    print("  THE VALUE LOOP")
    print("=" * 60)

    ACTION_HANDLERS = {
        Action.EXECUTE:           do_execute,
        Action.GENERATE_QC:       do_generate_qc,
        Action.RUN_QC:            do_run_qc,
        Action.FIX:               do_fix,
        Action.CRITICAL_EVAL:     do_critical_eval,      # Phase 3 stub
        Action.COURSE_CORRECT:    do_course_correct,     # Phase 2 stub
        Action.SERVICE_FIX:       do_service_fix,
        Action.RESEARCH:          do_research,            # Phase 3 stub
        Action.COHERENCE_EVAL:    do_full_coherence_eval, # Phase 3 stub
        Action.INTERACTIVE_PAUSE: do_interactive_pause,
    }

    for iteration in range(1, config.max_loop_iterations + 1):
        state.iteration = iteration

        # Budget check
        if config.token_budget and state.total_tokens_used > config.token_budget:
            print(f"TOKEN BUDGET EXHAUSTED ({state.total_tokens_used} tokens)")
            break

        action = decide_next_action(config, state)
        print(f"\n── Iteration {iteration} ── Action: {action.value}")

        # Exit gate is special — it can terminate the loop
        if action == Action.EXIT_GATE:
            exit_passed = do_exit_gate(config, state, claude)
            if exit_passed:
                generate_delivery_report(config, state)
                print("\n  VALUE DELIVERED — exit gate passed")
                state.save(config.state_file)
                return
            progress = True
        else:
            progress = ACTION_HANDLERS[action](config, state, claude)

        state.record_progress(action.value, "progress" if progress else "no_progress", progress)

        # Phase 3: Process monitor — stubbed (no-op)
        # Phase 2: Plan health check — stubbed (no-op)
        # Phase 2: VRC heartbeat — stubbed (no-op)

        state.save(config.state_file)

    print("\n  MAX ITERATIONS REACHED — generating partial delivery report")
    generate_delivery_report(config, state)
```

---

## 6. Task Execution + Regression

### 6.1 Pick Next Task

```python
def pick_next_task(state: LoopState) -> TaskState | None:
    pending = [t for t in state.tasks.values() if t.status == "pending"]
    if not pending:
        return None
    # Descoped dependencies count as satisfied — the task proceeds without them
    ready = [t for t in pending
             if all(state.tasks.get(dep, TaskState(task_id="")).status in ("done", "descoped")
                    for dep in (t.dependencies or []))]
    if not ready:
        return None
    priority = {"exit_gate": 0, "critical_eval": 1, "vrc": 2, "course_correction": 3, "plan": 4}
    ready.sort(key=lambda t: priority.get(t.source, 99))
    return ready[0]
```

### 6.2 Execute Task

```python
def do_execute(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    task = pick_next_task(state)
    if not task:
        return False

    task.status = "in_progress"
    try:
        session = claude.session(AgentRole.BUILDER)
        prompt = load_prompt("execute").format(
            TASK=json.dumps(asdict(task), indent=2),
            SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
        )
        session.send(prompt)
    except Exception as e:
        # Builder crashed — don't leave task stuck in "in_progress" (GAP-15)
        print(f"  Builder agent failed: {e}")
        task.status = "pending"
        task.retry_count += 1

    completed = task.status == "done"  # set by report_task_complete handler

    if not completed:
        task.retry_count += 1
        if task.retry_count >= config.max_task_retries:
            task.status = "blocked"
            task.blocked_reason = "Agent failed to complete after max retries"
        elif task.status == "in_progress":  # still in_progress (no tool call and no exception)
            task.status = "pending"
        return False

    state.tasks_since_last_critical_eval += 1
    if task.source != "plan":
        state.mid_loop_tasks_since_health_check += 1
    git_commit(config, state, f"telic-loop({config.sprint}): {task.task_id} - completed")

    if config.regression_after_every_task and state.regression_baseline:
        regressions = run_regression(config, state)
        if regressions:
            print(f"  REGRESSION: {len(regressions)} tests broke after {task.task_id}")
            handle_regressions(regressions, task, config, state, claude)
            return False

    return True
```

### 6.3 Regression

```python
def run_tests_parallel(tests, timeout, max_workers=None):
    """
    Run test scripts in parallel using ThreadPoolExecutor.
    Uses threads+subprocess (not asyncio) to avoid nested event loop issues.
    Returns {test_id: (exit_code, stdout, stderr)}.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import os

    max_workers = max_workers or min(os.cpu_count() or 4, 10)
    results = {}

    def run_one(test):
        try:
            proc = subprocess.run(
                [test.script_path], capture_output=True, text=True,
                timeout=timeout, cwd=str(Path(test.script_path).parent),
            )
            return test.verification_id, (proc.returncode, proc.stdout, proc.stderr)
        except subprocess.TimeoutExpired:
            return test.verification_id, (1, "", "TIMEOUT")

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(run_one, t): t for t in tests}
        for future in as_completed(futures):
            test_id, result = future.result()
            results[test_id] = result

    return results


def run_regression(config: LoopConfig, state: LoopState) -> list[str]:
    tests_to_check = [
        state.verifications[tid] for tid in state.regression_baseline
        if tid in state.verifications and state.verifications[tid].script_path
    ]
    if not tests_to_check:
        return []

    results = run_tests_parallel(tests_to_check, config.regression_timeout)
    regressions = []
    for test_id, (exit_code, stdout, stderr) in results.items():
        if exit_code != 0:
            regressions.append(test_id)
            state.verifications[test_id].status = "failed"
            state.verifications[test_id].failures.append(FailureRecord(
                timestamp=datetime.now().isoformat(),
                attempt=state.verifications[test_id].attempts + 1,
                exit_code=exit_code, stdout=stdout[:2000], stderr=stderr[:2000],
            ))
            state.regression_baseline.discard(test_id)
    return regressions


def handle_regressions(regressions, causal_task, config, state, claude):
    session = claude.session(AgentRole.FIXER)
    for test_id in regressions:
        test = state.verifications[test_id]
        failing_details = [
            {"verification_id": test.verification_id, "last_error": test.last_error,
             "attempt_history": test.attempt_history,
             "script": Path(test.script_path).read_text() if test.script_path else ""}
        ]
        prompt = load_prompt("fix").format(
            SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
            ROOT_CAUSE=json.dumps({"cause": f"Regression caused by {causal_task.task_id}",
                                    "affected_tests": [test_id],
                                    "fix_suggestion": f"Test was passing before {causal_task.task_id}. "
                                                      f"Preserve new functionality while restoring the regression."}),
            FAILING_VERIFICATIONS=json.dumps(failing_details, indent=2),
            RESEARCH_CONTEXT=get_research_context(state),
        )
        session.send(prompt)
        exit_code, stdout, stderr = run_test_script(test, config.regression_timeout // max(len(regressions), 1))
        if exit_code == 0:
            test.status = "passed"
            state.regression_baseline.add(test_id)
```

### 6.4 Service Health

```python
def all_services_healthy(config: LoopConfig, state: LoopState) -> bool:
    for name, service in state.context.services.items():
        if "health_url" in service:
            try:
                r = requests.get(service["health_url"], timeout=5)
                if r.status_code != 200: return False
            except (requests.ConnectionError, requests.Timeout):
                return False
        elif service.get("health_type") == "tcp":
            if not is_port_open("localhost", service.get("port", 0)):
                return False
    return True

def do_service_fix(config, state, claude) -> bool:
    session = claude.session(AgentRole.BUILDER)
    session.send(f"Fix broken services:\n{json.dumps(state.context.services, indent=2)}")
    return all_services_healthy(config, state)
```

---

## 7. QC Agent

### 7.1 Generate QC

```python
def do_generate_qc(config, state, claude) -> bool:
    session = claude.session(AgentRole.QC)
    prompt = load_prompt("generate_verifications").format(
        SPRINT=config.sprint, SPRINT_DIR=str(config.sprint_dir),
        PLAN=config.plan_file.read_text(), PRD=config.prd_file.read_text(),
        VISION=config.vision_file.read_text(),
        VERIFICATION_STRATEGY=json.dumps(state.context.verification_strategy, indent=2),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
    )
    session.send(prompt)

    # Discover generated scripts
    verify_dir = Path(".loop/verifications")
    if verify_dir.exists():
        for category_dir in sorted(verify_dir.iterdir()):
            if not category_dir.is_dir(): continue
            category = category_dir.name
            if category not in state.verification_categories:
                state.verification_categories.append(category)
            for script in sorted(category_dir.iterdir()):
                if script.suffix not in (".sh", ".py"): continue
                v_id = f"{category}/{script.stem}"
                if sys.platform != "win32":
                    script.chmod(0o755)
                state.verifications[v_id] = VerificationState(
                    verification_id=v_id, category=category,
                    script_path=str(script), requires=parse_requires(script),
                )
    state.pass_gate("verifications_generated")
    return bool(state.verifications)
```

### 7.2 Run QC

```python
def do_run_qc(config, state, claude) -> bool:
    progress = False
    for category in state.verification_categories:
        pending = [v for v in state.verifications.values()
                   if v.category == category and v.status == "pending"]
        if not pending: continue
        if not category_deps_met(category, state, config): continue

        results = run_tests_parallel(pending, config.regression_timeout)
        for v_id, (exit_code, stdout, stderr) in results.items():
            v = state.verifications[v_id]
            v.attempts += 1
            if exit_code == 0:
                v.status = "passed"
                state.add_regression_pass(v_id)
                progress = True
            else:
                v.status = "failed"
                v.failures.append(FailureRecord(
                    timestamp=datetime.now().isoformat(), attempt=v.attempts,
                    exit_code=exit_code, stdout=stdout[:2000], stderr=stderr[:2000],
                ))
                state.research_attempted_for_current_failures = False

        if any(v.status == "failed" for v in state.verifications.values()
               if v.category == category):
            break  # don't proceed to next category if this one has failures
    return progress
```

### 7.3 Triage + Fix

```python
def do_fix(config, state, claude) -> bool:
    failing = {v.verification_id: v for v in state.verifications.values()
               if v.status == "failed" and v.attempts < config.max_fix_attempts}
    if not failing: return False

    # Step 1: Triage (Haiku)
    if len(failing) > 1:
        triage_session = claude.session(AgentRole.CLASSIFIER)
        error_summary = "\n".join(f"- {v.verification_id}: {v.last_error[:200]}"
                                  for v in failing.values())
        triage_session.send(load_prompt("triage").format(FAILURES=error_summary))
        root_causes = state.agent_results.get("triage") or []
    else:
        test = next(iter(failing.values()))
        root_causes = [{"cause": test.last_error or "Unknown",
                        "affected_tests": [test.verification_id], "priority": 1}]

    # Step 2: Fix each root cause (Sonnet)
    any_fixed = False
    for rc in sorted(root_causes, key=lambda x: x.get("priority", 99)):
        session = claude.session(AgentRole.FIXER)
        affected = [failing[tid] for tid in rc["affected_tests"] if tid in failing]
        if not affected: continue

        failing_details = [
            {"verification_id": v.verification_id, "last_error": v.last_error,
             "attempt_history": v.attempt_history,
             "script": Path(v.script_path).read_text() if v.script_path else ""}
            for v in affected
        ]
        prompt = load_prompt("fix").format(
            SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
            ROOT_CAUSE=json.dumps({"cause": rc["cause"],
                                    "affected_tests": rc["affected_tests"],
                                    "fix_suggestion": rc.get("fix_suggestion", "")}),
            FAILING_VERIFICATIONS=json.dumps(failing_details, indent=2),
            RESEARCH_CONTEXT=get_research_context(state),
        )
        session.send(prompt)

        # Verify fix by re-running affected tests
        for v in affected:
            v.attempts += 1  # count this fix attempt
            results = run_tests_parallel([v], config.regression_timeout)
            exit_code, stdout, stderr = results.get(v.verification_id, (1, "", ""))
            if exit_code == 0:
                v.status = "passed"
                state.add_regression_pass(v.verification_id)
                any_fixed = True
            else:
                v.failures.append(FailureRecord(
                    timestamp=datetime.now().isoformat(), attempt=v.attempts,
                    exit_code=exit_code, stdout=stdout[:2000], stderr=stderr[:2000],
                    fix_applied=f"Fix for root cause: {rc['cause'][:200]}",
                ))

        # Check for regressions after fix
        if state.regression_baseline:
            regressions = run_regression(config, state)
            if regressions:
                print(f"  Fix caused {len(regressions)} regressions")

    return any_fixed
```

---

## 8. Interactive Pause

```python
def do_interactive_pause(config, state, claude) -> bool:
    if state.pause is not None:
        # Resuming — verify human's action
        if verify_human_action(state.pause.verification, config):
            print("  Human action verified — resuming")
            for task in state.tasks.values():
                if task.status == "blocked" and task.blocked_reason.startswith("HUMAN_ACTION:"):
                    task.status = "pending"
                    task.blocked_reason = ""
            state.pause = None
            return True
        else:
            print(f"  Not yet completed. Instructions: {state.pause.instructions}")
            input("  Press Enter when ready...")
            return False

    # First time — set up pause
    human_blocked = [t for t in state.tasks.values()
                     if t.status == "blocked" and t.blocked_reason.startswith("HUMAN_ACTION:")]
    if not human_blocked: return False

    task = human_blocked[0]
    action_needed = task.blocked_reason.replace("HUMAN_ACTION:", "").strip()

    state.pause = PauseState(
        reason=action_needed, instructions=action_needed,
        verification=task.acceptance or "",
        requested_at=datetime.now().isoformat(),
    )
    print(f"\n  {'=' * 50}")
    print(f"  INTERACTIVE PAUSE — Human action needed")
    print(f"  {'=' * 50}")
    print(f"  {action_needed}")
    state.save(config.state_file)
    input("  Press Enter when done...")
    return False


def verify_human_action(verification: str, config) -> bool:
    """Run verification command. Uses shell=True because verification commands
    are defined by the orchestrator (from task acceptance criteria), not by
    untrusted LLM output. Commands are simple health checks like
    'curl http://localhost:8000/health' or 'python -c "import mylib"'."""
    if not verification: return True
    try:
        result = subprocess.run(
            verification, shell=True, capture_output=True, timeout=30,
            cwd=str(config.sprint_dir),
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
```

---

## 9. Phase 2/3 Stubs

```python
def do_course_correct(config, state, claude) -> bool:
    """Phase 2 implements Opus-driven restructuring. Phase 1: log and abort."""
    print("  STUCK — course correction not yet implemented (Phase 2)")
    print(f"  {state.iterations_without_progress} iterations without progress")
    return False

def do_critical_eval(config, state, claude) -> bool:
    """Phase 3 implements Evaluator agent. Phase 1: no-op."""
    state.tasks_since_last_critical_eval = 0
    return False

def do_research(config, state, claude) -> bool:
    """Phase 3 implements web research. Phase 1: mark as attempted."""
    state.research_attempted_for_current_failures = True
    return False

def do_full_coherence_eval(config, state, claude) -> bool:
    """Phase 3 implements 7-dimension Opus evaluation. Phase 2 has quick (automated). Phase 1: no-op."""
    state.tasks_since_last_coherence = 0
    state.coherence_critical_pending = False
    return False

def do_exit_gate(config, state, claude) -> bool:
    """Phase 2 implements fresh-context verification. Phase 1: always passes."""
    print("  EXIT GATE (Phase 1 — simple pass)")
    return True
```

---

## 9b. Tool Dispatch (Transactional)

```python
import copy

def execute_tool(name: str, input: dict, state: LoopState, task_source: str = "agent") -> str:
    """
    Dispatch structured tool calls with transactional safety.
    Snapshots affected state before mutation; rolls back on handler error.
    """
    HANDLERS = {
        "manage_task":              handle_manage_task,
        "report_task_complete":     handle_task_complete,
        "report_discovery":         handle_discovery,
        "report_critique":          handle_critique,
        "report_triage":            handle_triage,
        "report_vrc":               handle_vrc,
        "report_eval_finding":      handle_eval_finding,
        "report_research":          handle_research,
        "report_vision_validation": handle_vision_validation,
        "report_strategy_change":   handle_strategy_change,
        "report_course_correction": handle_course_correction,
        "report_epic_decomposition": handle_epic_decomposition,
        "report_epic_summary":      handle_epic_summary,
        "report_coherence":         handle_coherence,
        "request_human_action":     handle_human_action,
    }
    handler = HANDLERS.get(name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {name}"})

    # Snapshot mutable state fields that the handler might touch
    snapshot = {
        "tasks": copy.deepcopy(state.tasks),
        "verifications": copy.deepcopy(state.verifications),
        "agent_results": copy.deepcopy(state.agent_results),
    }
    try:
        result = handler(input, state, task_source=task_source)
        return json.dumps({"ok": True, "result": result})
    except Exception as e:
        # Rollback: restore snapshotted fields
        state.tasks = snapshot["tasks"]
        state.verifications = snapshot["verifications"]
        state.agent_results = snapshot["agent_results"]
        return json.dumps({"error": f"Handler failed: {e}", "rolled_back": True})
```

---

## 10. Task Mutation Guardrails

```python
DUPLICATE_SIMILARITY_THRESHOLD = 0.75
MID_LOOP_TASK_CEILING = 15

def validate_task_mutation(action, input, state) -> str | None:
    """Deterministic validation. Returns error message or None."""
    task_id = input.get("task_id", "")

    if action == "add":
        missing = [f for f in ["description", "value", "acceptance"] if not input.get(f)]
        if missing:
            return f"Task {task_id} missing: {', '.join(missing)}"

        new_desc = input["description"].lower()
        for existing in state.tasks.values():
            if existing.status in ("done", "descoped"): continue
            sim = _jaccard_similarity(new_desc, existing.description.lower())
            if sim >= DUPLICATE_SIMILARITY_THRESHOLD:
                return f"Task {task_id} duplicates {existing.task_id} ({sim:.0%} similar)"

        mid_loop = [t for t in state.tasks.values()
                    if t.source != "plan" and t.status not in ("done", "descoped")]
        if len(mid_loop) >= MID_LOOP_TASK_CEILING:
            return f"Mid-loop task ceiling ({MID_LOOP_TASK_CEILING}) reached"

        for dep_id in input.get("dependencies", []):
            if dep_id not in state.tasks:
                return f"Dependency '{dep_id}' doesn't exist"

    elif action == "modify":
        if task_id not in state.tasks:
            return f"Task {task_id} doesn't exist"
        if input.get("field") == "dependencies":
            new_deps = json.loads(input["new_value"]) if isinstance(input.get("new_value"), str) else input.get("new_value", [])
            for dep_id in (new_deps or []):
                if _creates_cycle(task_id, dep_id, state):
                    return f"Circular dependency: {task_id} → {dep_id}"

    elif action == "remove":
        if task_id not in state.tasks:
            return f"Task {task_id} doesn't exist"
        dependents = [t.task_id for t in state.tasks.values()
                      if task_id in (t.dependencies or [])]
        if dependents:
            return f"Cannot remove {task_id} — depended on by {', '.join(dependents)}"

    return None

def _jaccard_similarity(a, b):
    wa, wb = set(a.split()), set(b.split())
    return len(wa & wb) / len(wa | wb) if (wa or wb) else 0.0

def _creates_cycle(task_id, new_dep_id, state):
    visited, stack = set(), [new_dep_id]
    while stack:
        current = stack.pop()
        if current == task_id: return True
        if current in visited: continue
        visited.add(current)
        t = state.tasks.get(current)
        if t and t.dependencies: stack.extend(t.dependencies)
    return False
```

---

## 11. Rendered Views

```python
def render_plan_markdown(state: LoopState) -> str:
    lines = [f"# Implementation Plan (rendered from state)\n",
             f"Generated: {datetime.now().isoformat()}\n"]
    phases = {}
    for t in state.tasks.values():
        phases.setdefault(t.phase or "unphased", []).append(t)
    for phase_name, tasks in phases.items():
        lines.append(f"\n## {phase_name.title()}\n")
        for t in sorted(tasks, key=lambda x: x.task_id):
            check = "x" if t.status == "done" else ("B" if t.status == "blocked" else " ")
            lines.append(f"- [{check}] **{t.task_id}**: {t.description}")
            if t.value: lines.append(f"  - Value: {t.value}")
            if t.acceptance: lines.append(f"  - Acceptance: {t.acceptance}")
            if t.dependencies: lines.append(f"  - Deps: {', '.join(t.dependencies)}")
            lines.append("")
    return "\n".join(lines)

def generate_delivery_report(config, state):
    vrc = state.latest_vrc
    passed = len([v for v in state.verifications.values() if v.status == "passed"])
    lines = [
        f"# Delivery Report: {config.sprint}", "",
        f"- Tasks completed: {len([t for t in state.tasks.values() if t.status == 'done'])}/{len(state.tasks)}",
        f"- QC checks: {passed}/{len(state.verifications)} passing",
        f"- Iterations: {state.iteration}",
        f"- Tokens used: {state.total_tokens_used:,}", "",
        "## Deliverables",
    ]
    for t in state.tasks.values():
        status = {"done": "DELIVERED", "descoped": "DESCOPED", "blocked": "BLOCKED"}.get(t.status, t.status)
        lines.append(f"- [{status}] {t.task_id}: {t.description}")
    (config.sprint_dir / "DELIVERY_REPORT.md").write_text("\n".join(lines))
```

---

## 12. LoopState Methods

```python
# Add these methods to the LoopState dataclass (see Architecture Reference for fields)

def record_progress(self, action, result, made_progress):
    self.progress_log.append({
        "iteration": self.iteration, "action": action,
        "result": result, "timestamp": datetime.now().isoformat(),
    })
    self.iterations_without_progress = 0 if made_progress else self.iterations_without_progress + 1

def is_stuck(self, config): return self.iterations_without_progress >= config.max_no_progress
def progress_log_count(self, action): return [e for e in self.progress_log if e.get("action") == action]

@property
def latest_vrc(self): return self.vrc_history[-1] if self.vrc_history else None

@property
def value_delivered(self):
    vrc = self.latest_vrc
    return vrc is not None and vrc.recommendation == "SHIP_READY"

def add_regression_pass(self, vid): self.regression_baseline.add(vid)
def gate_passed(self, name): return name in self.gates_passed
def pass_gate(self, name): self.gates_passed.add(name)
def add_task(self, task): self.tasks[task.task_id] = task

def invalidate_tests(self):
    self.verifications.clear()
    self.regression_baseline.clear()
    self.gates_passed.discard("verifications_generated")

def save(self, path):
    """Atomic state save: write to .tmp then rename to prevent corruption on crash."""
    data = asdict(self)
    data["gates_passed"] = sorted(data["gates_passed"])
    data["regression_baseline"] = sorted(data["regression_baseline"])
    def _serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, set):
            return sorted(obj)
        raise TypeError(f"Cannot serialize {type(obj).__name__}: {obj!r}")

    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(data, indent=2, default=_serialize))
    tmp_path.replace(path)  # atomic on POSIX; near-atomic on Windows (NTFS)

@classmethod
def load(cls, path):
    from dacite import from_dict, Config
    data = json.loads(path.read_text())
    return from_dict(
        data_class=cls,
        data=data,
        config=Config(
            type_hooks={
                set: lambda x: set(x) if isinstance(x, list) else x,
            },
            cast=[Literal],
            strict=False,
        ),
    )
```

---

## 12.5 Utility Functions

These are referenced throughout the plan and must be implemented:

```python
def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    return (Path(__file__).parent / "prompts" / f"{name}.md").read_text()

def git_commit(config: LoopConfig, state: LoopState, message: str):
    """Create a safe git commit. Never uses 'git add -A'.
    See Architecture Reference § Git Operations for full spec."""
    # Stage modified tracked files
    subprocess.run(["git", "add", "-u"], check=True)

    # Stage new files only from safe directories (derived from context)
    safe_dirs = _get_safe_directories(config, state)
    for d in safe_dirs:
        if Path(d).exists():
            subprocess.run(["git", "add", str(d)], check=True)

    # Scan staged files for sensitive patterns — unstage any matches
    result = subprocess.run(["git", "diff", "--cached", "--name-only"],
                            capture_output=True, text=True)
    staged = result.stdout.strip().splitlines()
    for f in staged:
        if _matches_sensitive_pattern(f, state.git.sensitive_patterns):
            subprocess.run(["git", "reset", "HEAD", f], check=True)
            print(f"  WARNING: Unstaged sensitive file: {f}")

    # Commit (allow empty to handle edge case where all staged files were sensitive)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode != 0:  # there are staged changes
        subprocess.run(["git", "commit", "-m", message], check=True)
        # Update last_commit_hash
        hash_result = subprocess.run(["git", "rev-parse", "HEAD"],
                                     capture_output=True, text=True)
        state.git.last_commit_hash = hash_result.stdout.strip()

def _get_safe_directories(config: LoopConfig, state: LoopState) -> list[str]:
    """Derive safe directories for staging new files from SprintContext."""
    safe = [str(config.sprint_dir)]
    # Add common safe patterns discovered from context
    for d in ["src", "tests", "test", "lib", "docs"]:
        if (config.sprint_dir / d).exists():
            safe.append(str(config.sprint_dir / d))
    return safe

def _matches_sensitive_pattern(filepath: str, patterns: list[str]) -> bool:
    """Check if a file path matches any sensitive pattern."""
    from fnmatch import fnmatch
    name = Path(filepath).name
    return any(fnmatch(name, pat) or fnmatch(filepath, pat) for pat in patterns)

def render_plan_snapshot(config: LoopConfig, state: LoopState):
    """Re-render the plan markdown from structured state."""
    config.plan_file.write_text(render_plan_markdown(state))

def is_port_open(host: str, port: int) -> bool:
    """Check if a TCP port is accepting connections."""
    import socket
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (ConnectionRefusedError, TimeoutError, OSError):
        return False

def parse_requires(script: Path) -> list[str]:
    """Parse '# requires: category1, category2' from verification script header."""
    first_line = script.read_text().split("\n", 1)[0]
    if first_line.startswith("# requires:"):
        return [r.strip() for r in first_line.split(":", 1)[1].split(",")]
    return []

def run_test_script(test: VerificationState, timeout: int) -> tuple[int, str, str]:
    """Run a single test script and return (exit_code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            [test.script_path], capture_output=True, text=True,
            timeout=timeout, cwd=str(Path(test.script_path).parent),
        )
        return (proc.returncode, proc.stdout, proc.stderr)
    except subprocess.TimeoutExpired:
        return (1, "", "TIMEOUT")

def category_deps_met(category: str, state: LoopState, config: LoopConfig) -> bool:
    """Check if a verification category's dependencies are met."""
    for v in state.verifications.values():
        if v.category == category:
            for req in v.requires:
                req_tests = [t for t in state.verifications.values() if t.category == req]
                if not all(t.status == "passed" for t in req_tests):
                    return False
    return True

def get_research_context(state: LoopState) -> str:
    """Get all research briefs for the fix agent's context. Phase 3 populates this."""
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

---

## 13. Entry Point

```python
def _acquire_lock(lock_path: Path):
    """Acquire exclusive file lock to prevent concurrent runs on same sprint."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = open(lock_path, "w")
    if sys.platform == "win32":
        import msvcrt
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            print(f"FATAL: Another loop instance is running on this sprint (lock: {lock_path})")
            sys.exit(1)
    else:
        import fcntl
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print(f"FATAL: Another loop instance is running on this sprint (lock: {lock_path})")
            sys.exit(1)
    return lock_file  # keep reference alive to hold lock


def _ensure_git_repo(config: LoopConfig):
    """Verify we are inside a git repo. Initialize one if not (H5)."""
    result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print("  No git repository found — initializing one")
        subprocess.run(["git", "init"], cwd=str(config.sprint_dir), check=True)

def _recover_interrupted_rollback(config: LoopConfig, state: LoopState):
    """Check for interrupted rollback (WAL recovery)."""
    wal_path = config.state_file.with_suffix(".rollback_wal")
    if wal_path.exists():
        import json as _json
        wal = _json.loads(wal_path.read_text())
        print(f"  WARNING: Recovering from interrupted rollback to {wal['to_label']}")
        # Re-run the git reset to ensure consistent state
        subprocess.run(["git", "reset", "--hard", wal["to_hash"]], check=True)
        subprocess.run(["git", "clean", "-fd"], check=True)
        wal_path.unlink()


def main():
    sprint = sys.argv[1]
    config = LoopConfig(sprint=sprint, sprint_dir=Path(f"sprints/{sprint}"))
    lock = _acquire_lock(config.sprint_dir / ".loop.lock")
    _ensure_git_repo(config)
    state = LoopState.load(config.state_file) if config.state_file.exists() else LoopState(sprint=sprint)
    _recover_interrupted_rollback(config, state)
    claude = Claude(config, state)

    if state.phase == "pre_loop":
        if not run_preloop(config, state, claude):
            print("\nPRE-LOOP FAILED — cannot proceed.")
            sys.exit(1)

    if state.phase == "value_loop":
        # Dispatch based on vision complexity (Phase 3 adds run_epic_loop)
        if state.vision_complexity == "multi_epic" and state.epics:
            run_epic_loop(config, state, claude)
        else:
            run_value_loop(config, state, claude)

    if state.value_delivered:
        sys.exit(0)
    elif state.latest_vrc and state.latest_vrc.value_score > 0.5:
        sys.exit(2)  # partial
    else:
        sys.exit(1)
```

---

## 14. Migration Checklist (Phase 1)

### Foundation
- [ ] Scaffold Python project (`pyproject.toml`, package structure)
- [ ] Implement `config.py` (LoopConfig)
- [ ] Implement `state.py` (LoopState + all sub-dataclasses + save/load)
- [ ] Implement `claude.py` (AgentRole, Claude, ClaudeSession with adaptive thinking + streaming)
- [ ] Implement `tools.py` — execution tools (bash, read, write, edit, glob, grep)
- [ ] Implement `tools.py` — structured tools (manage_task, report_task_complete, report_discovery, report_critique, report_triage, request_human_action)
- [ ] Implement `tools.py` — provider tool declarations + get_tools_for_role()
- [ ] Implement `tools.py` — tool dispatch (execute_tool with transactional rollback) + state mutation handlers
- [ ] Implement `tools.py` — validate_task_mutation guardrails
- [ ] Implement `render.py` (render_plan_markdown, generate_delivery_report)
- [ ] Implement `decision.py` (Action enum + decide_next_action)

### Pre-Loop
- [ ] Implement `phases/preloop.py` — validate_inputs, run_preloop flow
- [ ] Implement context discovery (discover_context → report_discovery handler)
- [ ] Implement PRD critique (critique_prd → report_critique handler)
- [ ] Implement plan generation (via manage_task tool calls)
- [ ] Implement quality gate runner (QUALITY_GATES list + run_quality_gates)
- [ ] Implement blocker resolution + preconditions report

### Prompts
- [ ] Create `system.md` (base system prompt)
- [ ] Create `discover_context.md`
- [ ] Create `prd_critique.md`
- [ ] Create/migrate `plan.md` (add verification_strategy awareness)
- [ ] Create/migrate quality gate prompts: craap, clarity, validate, connect, break, prune, tidy
- [ ] Migrate `verify_blockers.md`, `preflight.md`
- [ ] Create/migrate `execute.md` (Builder agent)
- [ ] Create/migrate `generate_verifications.md` (QC agent)
- [ ] Create/migrate `triage.md`, `fix.md`
- [ ] Create `interactive_pause.md`

### Value Loop
- [ ] Implement `phases/execute.py` — do_execute, pick_next_task, regression
- [ ] Implement `phases/qc.py` — do_generate_qc, do_run_qc, do_fix with triage
- [ ] Implement `phases/pause.py` — do_interactive_pause, verify_human_action
- [ ] Implement service health check (all_services_healthy, do_service_fix)
- [ ] Implement run_value_loop with action dispatch table
- [ ] Add Phase 2/3 stub handlers

### Integration
- [ ] Implement `main.py` entry point
- [ ] Test on a minimal sprint (1-2 tasks)

### Dependencies
```toml
[project]
name = "loop-v3"
requires-python = ">=3.12"
dependencies = ["anthropic>=0.40.0", "requests>=2.31.0", "dacite>=1.8.0"]
```

---

## Appendix: Phase 1 Structured Tool Schemas

### manage_task
```python
{"name": "manage_task", "input_schema": {"properties": {
    "action": {"type": "string", "enum": ["add", "modify", "remove"]},
    "task_id": {"type": "string"},
    "reason": {"type": "string"},
    "description": {"type": "string"}, "value": {"type": "string"},
    "acceptance": {"type": "string"}, "prd_section": {"type": "string"},
    "dependencies": {"type": "array", "items": {"type": "string"}},
    "phase": {"type": "string"}, "files_expected": {"type": "array", "items": {"type": "string"}},
    "field": {"type": "string", "enum": ["description","value","acceptance","dependencies","phase","status","blocked_reason","files_expected"]},
    "new_value": {"type": "string"},
}, "required": ["action", "task_id"]}}
```

### report_task_complete
```python
{"name": "report_task_complete", "input_schema": {"properties": {
    "task_id": {"type": "string"},
    "files_created": {"type": "array", "items": {"type": "string"}},
    "files_modified": {"type": "array", "items": {"type": "string"}},
    "value_verified": {"type": "string"},
    "completion_notes": {"type": "string"},
}, "required": ["task_id", "files_created", "files_modified"]}}
```

### report_discovery
```python
{"name": "report_discovery", "input_schema": {"properties": {
    "deliverable_type": {"type": "string", "enum": ["software","document","data","config","hybrid"]},
    "project_type": {"type": "string"},
    "codebase_state": {"type": "string", "enum": ["greenfield","brownfield","non_code"]},
    "environment": {"type": "object"}, "services": {"type": "object"},
    "verification_strategy": {"type": "object"},
    "value_proofs": {"type": "array", "items": {"type": "string"}},
    "unresolved_questions": {"type": "array", "items": {"type": "string"}},
}, "required": ["deliverable_type", "project_type", "codebase_state", "value_proofs"]}}
```

### report_critique
```python
{"name": "report_critique", "input_schema": {"properties": {
    "verdict": {"type": "string", "enum": ["APPROVE","AMEND","DESCOPE","REJECT"]},
    "reason": {"type": "string"},
    "amendments": {"type": "array", "items": {"type": "string"}},
    "descope_suggestions": {"type": "array", "items": {"type": "string"}},
}, "required": ["verdict", "reason"]}}
```

### report_triage
```python
{"name": "report_triage", "input_schema": {"properties": {
    "root_causes": {"type": "array", "items": {"type": "object", "properties": {
        "cause": {"type": "string"}, "affected_tests": {"type": "array", "items": {"type": "string"}},
        "priority": {"type": "integer"}, "fix_suggestion": {"type": "string"},
    }}},
}, "required": ["root_causes"]}}
```

### request_human_action
```python
{"name": "request_human_action", "input_schema": {"properties": {
    "action": {"type": "string"}, "instructions": {"type": "string"},
    "verification_command": {"type": "string"}, "blocked_task_id": {"type": "string"},
}, "required": ["action", "instructions", "blocked_task_id"]}}
```
