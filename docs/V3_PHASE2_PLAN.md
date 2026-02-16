# Loop V3: Phase 2 Plan — +VRC + Course Correction + Exit Gate

**Date**: 2026-02-15
**Prerequisite**: Phase 1 complete and tested
**Architecture**: V3_ARCHITECTURE.md
**Requirements**: V3_PRD.md (R17-R21, R31)

---

## Scope

### What Phase 2 Adds
- **VRC heartbeat** running every iteration (quick/full modes)
- **Course correction** — Opus-driven restructuring when stuck
- **Plan health check** — mid-loop task quality sweep
- **Exit gate** — fresh-context final verification (inside the loop)
- **Budget tracking** — VRC adapts, budget warnings, partial delivery
- **Quick Coherence Check** — automated structural integrity + interaction coherence analysis (Dimensions 1-2)

### What Changes from Phase 1
- `do_course_correct` stub → real Opus-driven restructuring
- `do_exit_gate` stub → fresh-context VRC + regression + critical eval
- Value loop gains VRC heartbeat after every action
- Value loop gains plan health check after course correction
- Delivery report enhanced with VRC score

### What Remains Stubbed (Phase 3)
- `do_critical_eval` — no-op (called within exit gate but not standalone)
- `do_research` — marks as attempted
- `maybe_run_strategy_reasoner` — no-op (process monitor)
- `refine_vision` — auto-PASS
- `classify_vision_complexity` — always returns "single_run"
- `decompose_into_epics` — no-op
- `epic_feedback_checkpoint` — no-op
- `do_full_coherence_eval` — no-op (quick coherence is implemented)

---

## 1. VRC — The Heartbeat

### 1.1 run_vrc

```python
def run_vrc(config: LoopConfig, state: LoopState, claude: Claude,
            force_full: bool = False) -> VRCSnapshot:
    """
    Vision Reality Check. Runs every iteration.
    Full VRC (Opus) every 5th + first 3 + after CC/critical eval + exit gate.
    Quick VRC (Haiku) all other iterations.
    """
    is_full_vrc = force_full or (state.iteration % 5 == 0) or (state.iteration <= 3)

    # Budget > 80%: force quick VRC to save tokens
    budget_pct = (state.total_tokens_used / config.token_budget * 100) if config.token_budget else 0
    if budget_pct >= 80 and not force_full:
        is_full_vrc = False

    if is_full_vrc:
        session = claude.session(AgentRole.REASONER,
            system_extra="You are evaluating progress toward VISION delivery. "
            "This is a FULL VRC — thoroughly assess value delivery quality."
        )
    else:
        session = claude.session(AgentRole.CLASSIFIER)  # Haiku — cheap

    prompt = load_prompt("vrc").format(
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        IS_FULL_VRC="FULL" if is_full_vrc else "QUICK",
        ITERATION=state.iteration,
        VISION=config.vision_file.read_text(),
        PLAN=render_plan_markdown(state),
        TASK_SUMMARY=build_task_summary(state),
        PREVIOUS_VRC=format_latest_vrc(state),
    )

    vrc_count_before = len(state.vrc_history)
    response = session.send(prompt)

    # Fallback if agent didn't call report_vrc
    if len(state.vrc_history) == vrc_count_before:
        done = len([t for t in state.tasks.values() if t.status == "done"])
        total = len(state.tasks) or 1
        snapshot = VRCSnapshot(
            iteration=state.iteration,
            timestamp=datetime.now().isoformat(),
            deliverables_total=total,
            deliverables_verified=done,
            deliverables_blocked=len([t for t in state.tasks.values() if t.status == "blocked"]),
            value_score=done / total,
            gaps=[], recommendation="CONTINUE",
            summary=f"Fallback VRC: {done}/{total} tasks done",
        )
        state.vrc_history.append(snapshot)

    return state.vrc_history[-1]
```

### 1.2 VRC Helper Functions

```python
def build_task_summary(state: LoopState) -> str:
    """Brief task status for VRC and other agents."""
    lines = []
    done = len([t for t in state.tasks.values() if t.status == "done"])
    total = len(state.tasks)
    blocked = len([t for t in state.tasks.values() if t.status == "blocked"])
    lines.append(f"Tasks: {done}/{total} complete, {blocked} blocked")

    passed = len([v for v in state.verifications.values() if v.status == "passed"])
    failed = len([v for v in state.verifications.values() if v.status == "failed"])
    lines.append(f"QC checks: {passed}/{len(state.verifications)} passing, {failed} failing")

    recent = state.progress_log[-5:]
    if recent:
        lines.append("Recent actions:")
        for entry in recent:
            lines.append(f"  [{entry['iteration']}] {entry['action']}: {entry['result']}")

    return "\n".join(lines)


def format_latest_vrc(state: LoopState) -> str:
    """Format the most recent VRC snapshot for context."""
    if not state.vrc_history:
        return "No previous VRC."
    vrc = state.vrc_history[-1]
    return (
        f"Iteration {vrc.iteration}: {vrc.value_score:.0%} value | "
        f"{vrc.deliverables_verified}/{vrc.deliverables_total} verified | "
        f"{vrc.recommendation}\n"
        f"Summary: {vrc.summary}\n"
        f"Gaps: {len(vrc.gaps)}"
    )
```

### 1.3 VRC Frequency

| Situation | VRC Type | Model |
|-----------|----------|-------|
| First 3 iterations | Full | Opus |
| Every 5th iteration | Full | Opus |
| After critical eval or course correction | Full (forced) | Opus |
| Exit gate | Full (forced) | Opus |
| Budget > 80% | Quick only | Haiku |
| All other iterations | Quick | Haiku |

---

## 2. Course Correction

Replaces Phase 1 stub. Opus diagnoses why the loop is stuck and restructures.

```python
def do_course_correct(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    session = claude.session(AgentRole.REASONER,
        system_extra="You are diagnosing WHY the value loop is stuck. "
        "Analyze attempts, identify root cause, recommend correction."
    )

    prompt = load_prompt("course_correct").format(
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        VISION=config.vision_file.read_text(),
        PRD=config.prd_file.read_text(),
        PLAN=render_plan_markdown(state),
        TASK_SUMMARY=build_task_summary(state),
        VRC_HISTORY=format_vrc_history(state),
        GIT_CHECKPOINTS=format_git_checkpoints(state),
        STUCK_REASON=format_stuck_reason(state),
    )

    state.agent_results.pop("course_correction", None)
    response = session.send(prompt)

    correction = state.agent_results.get("course_correction")
    if not correction:
        return False

    match correction["action"]:
        case "restructure":
            state.iterations_without_progress = 0
            state.invalidate_tests()
            render_plan_snapshot(config, state)
            git_commit(config, state, f"telic-loop({config.sprint}): Course correction — restructured")
            return True
        case "descope":
            render_plan_snapshot(config, state)
            git_commit(config, state, f"telic-loop({config.sprint}): Descoped items")
            return True
        case "new_tasks":
            render_plan_snapshot(config, state)
            git_commit(config, state, f"telic-loop({config.sprint}): CC — added new tasks")
            return True
        case "rollback":
            label = correction.get("rollback_to_checkpoint", "")
            if not label:
                print("  ROLLBACK: No checkpoint label provided")
                return False
            # Find checkpoint by label
            checkpoint = next((cp for cp in state.git.checkpoints if cp.label == label), None)
            if not checkpoint:
                print(f"  ROLLBACK: Checkpoint '{label}' not found")
                return False
            # Enforce max rollbacks per sprint
            if len(state.git.rollbacks) >= config.max_rollbacks_per_sprint:
                print(f"  ROLLBACK: Max rollbacks ({config.max_rollbacks_per_sprint}) exhausted — forcing descope")
                return False
            # Execute rollback (see Architecture § Git Operations for full spec)
            execute_rollback(config, state, checkpoint, correction["reason"])
            # Check service health after rollback (services may be orphaned)
            if state.context.services:
                check_and_fix_services(config, state)
            render_plan_snapshot(config, state)
            return True
        case "regenerate_tests":
            state.invalidate_tests()
            return True
        case "escalate":
            print(f"\n  ESCALATION: {correction['reason']}")
            # Set pause so the decision engine picks up INTERACTIVE_PAUSE
            state.pause = PauseState(
                reason=f"Escalation: {correction['reason']}",
                instructions=correction["reason"],
                requested_at=datetime.now().isoformat(),
            )
            return False

    return False


def format_vrc_history(state: LoopState) -> str:
    """Format recent VRC history for agent context."""
    if not state.vrc_history:
        return "No VRC history yet."
    lines = []
    for vrc in state.vrc_history[-10:]:
        lines.append(
            f"[Iter {vrc.iteration}] {vrc.value_score:.0%} value | "
            f"{vrc.deliverables_verified}/{vrc.deliverables_total} | "
            f"{vrc.recommendation}: {vrc.summary}"
        )
    return "\n".join(lines)


def format_git_checkpoints(state: LoopState) -> str:
    """Format git checkpoints for course correction agent context."""
    if not state.git.checkpoints:
        return "No checkpoints yet."
    lines = []
    for cp in state.git.checkpoints:
        lines.append(
            f"[{cp.label}] {cp.timestamp} | "
            f"hash: {cp.commit_hash[:8]} | "
            f"{len(cp.tasks_completed)} tasks done | "
            f"{len(cp.verifications_passing)} verifications passing | "
            f"value: {cp.value_score:.0%}"
        )
    return "\n".join(lines)


def format_stuck_reason(state: LoopState) -> str:
    """Summarize why the loop is stuck based on state."""
    lines = [f"{state.iterations_without_progress} iterations without progress."]

    failing = [v for v in state.verifications.values() if v.status == "failed"]
    if failing:
        lines.append(f"Failing verifications ({len(failing)}):")
        for v in failing[:5]:
            lines.append(f"  - {v.verification_id}: {v.last_error[:200] if v.last_error else 'unknown'} "
                         f"({v.attempts} attempts)")

    blocked = [t for t in state.tasks.values() if t.status == "blocked"]
    if blocked:
        lines.append(f"Blocked tasks ({len(blocked)}):")
        for t in blocked[:5]:
            lines.append(f"  - {t.task_id}: {t.blocked_reason}")

    recent = state.progress_log[-10:]
    if recent:
        lines.append("Recent progress log:")
        for entry in recent:
            lines.append(f"  [{entry['iteration']}] {entry['action']}: {entry['result']}")

    return "\n".join(lines)
```

---

## 3. Plan Health Check

Layer 2 quality sweep for mid-loop task mutations. Runs after course correction (always) or when enough mid-loop tasks accumulate.

```python
def maybe_run_plan_health_check(config, state, claude, force=False):
    should_run = (
        force
        or state.mid_loop_tasks_since_health_check >= config.plan_health_after_n_tasks
    )
    if not should_run:
        return

    mid_loop_tasks = [
        t for t in state.tasks.values()
        if t.source != "plan" and not t.health_checked
    ]
    if not mid_loop_tasks:
        state.mid_loop_tasks_since_health_check = 0
        return

    print(f"\n  PLAN HEALTH CHECK — reviewing {len(mid_loop_tasks)} mid-loop tasks")

    session = claude.session(AgentRole.REASONER,
        system_extra="You are a plan quality reviewer. Check new tasks "
        "against existing plan for DRY violations, contradictions, "
        "SOLID breaches, dependency issues, and scope drift."
    )

    delta_summary = "\n".join(
        f"  [{t.task_id}] (source: {t.source}) {t.description}\n"
        f"    value: {t.value}\n    acceptance: {t.acceptance}\n    deps: {t.dependencies}"
        for t in mid_loop_tasks
    )
    existing_summary = "\n".join(
        f"  [{t.task_id}] ({t.status}) {t.description}"
        for t in state.tasks.values()
        if t.source == "plan" and t.status != "descoped"
    )

    prompt = load_prompt("plan_health_check").format(
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        PRD=config.prd_file.read_text(),
        PLAN=render_plan_markdown(state),
        EXISTING_TASKS=existing_summary,
        NEW_TASKS=delta_summary,
    )
    session.send(prompt)

    for t in mid_loop_tasks:
        t.health_checked = True
    state.mid_loop_tasks_since_health_check = 0
```

---

## 4. Exit Gate

Replaces Phase 1 stub. Fresh-context verification: full regression + full VRC + final critical eval. This is inside the loop — if it fails, gaps become tasks.

```python
def do_exit_gate(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    state.exit_gate_attempts += 1
    print(f"\n  EXIT GATE (attempt #{state.exit_gate_attempts})")

    # Safety valve
    if state.exit_gate_attempts > config.max_exit_gate_attempts:
        print(f"  Max attempts ({config.max_exit_gate_attempts}) reached — partial report")
        return True

    # 1. Full regression sweep
    print("  Running full regression sweep...")
    all_checks = [v for v in state.verifications.values() if v.script_path]
    results = asyncio.run(run_tests_parallel(all_checks, config.regression_timeout * 2))

    final_passes = sum(1 for _, (code, _, _) in results.items() if code == 0)
    final_fails = sum(1 for _, (code, _, _) in results.items() if code != 0)
    print(f"  QC results: {final_passes} passed, {final_fails} failed")

    if final_fails > 0:
        print(f"  EXIT GATE FAILED — {final_fails} QC checks failing")
        for v_id, (code, stdout, stderr) in results.items():
            if code != 0:
                state.verifications[v_id].status = "failed"
        return False

    # 2. Fresh-context VRC (Opus, forced full)
    print("  Running fresh-context VRC...")
    fresh_vrc = run_vrc(config, state, claude, force_full=True)

    if fresh_vrc.recommendation != "SHIP_READY":
        print(f"  EXIT GATE FAILED — VRC says {fresh_vrc.recommendation}")
        print(f"  Gaps found: {len(fresh_vrc.gaps)}")
        for gap in fresh_vrc.gaps:
            if gap.get("suggested_task"):
                state.add_task(TaskState(
                    task_id=f"EG-{state.exit_gate_attempts}-{gap['id']}",
                    source="exit_gate",
                    description=gap["suggested_task"],
                    value=gap["description"],
                    created_at=datetime.now().isoformat(),
                ))
        return False

    # 3. Final critical evaluation
    # Phase 3 replaces stub with real Evaluator agent.
    # Phase 2: run do_critical_eval which is still a stub (no-op).
    print("  Running final critical evaluation...")
    do_critical_eval(config, state, claude)

    new_tasks = [t for t in state.tasks.values()
                 if t.source == "critical_eval" and t.status == "pending"]
    if new_tasks:
        print(f"  EXIT GATE FAILED — critical eval found {len(new_tasks)} issues")
        return False

    print("  EXIT GATE PASSED — value verified")
    git_commit(config, state, f"telic-loop({config.sprint}): Exit gate passed — value verified")
    return True
```

---

## 5. Value Loop Updates

Replace the Phase 1 value loop with the full version. Key additions marked with `# NEW`:

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
        Action.CRITICAL_EVAL:     do_critical_eval,      # Phase 3 replaces stub
        Action.COURSE_CORRECT:    do_course_correct,     # NEW: real implementation
        Action.SERVICE_FIX:       do_service_fix,
        Action.RESEARCH:          do_research,            # Phase 3 replaces stub
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

        # Exit gate terminates the loop
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

        # Phase 3: Process monitor (stubbed)
        # maybe_run_strategy_reasoner(state, config, claude)

        # NEW: Plan health check after course correction
        if action == Action.COURSE_CORRECT and progress:
            maybe_run_plan_health_check(config, state, claude, force=True)
        else:
            maybe_run_plan_health_check(config, state, claude)

        # NEW: Quick coherence check — automated, interval-based
        if state.pause is None and action != Action.EXIT_GATE:
            quick_coherence_check(config, state)

        # NEW: VRC heartbeat — runs every iteration
        force_full_vrc = action in (Action.CRITICAL_EVAL, Action.COURSE_CORRECT)
        if state.pause is None and action != Action.EXIT_GATE:
            vrc = run_vrc(config, state, claude, force_full=force_full_vrc)
            print(f"  VRC #{len(state.vrc_history)}: {vrc.value_score:.0%} value | "
                  f"{vrc.deliverables_verified}/{vrc.deliverables_total} | "
                  f"→ {vrc.recommendation}")

        state.save(config.state_file)

    print("\n  MAX ITERATIONS REACHED — generating partial delivery report")
    generate_delivery_report(config, state)
```

---

## 6. Budget Tracking Integration

Budget tracking leverages existing `state.total_tokens_used` (accumulated by ClaudeSession in Phase 1).

**Budget-aware behaviors added in Phase 2:**

```python
# In run_value_loop, before action dispatch:
budget_pct = (state.total_tokens_used / config.token_budget * 100) if config.token_budget else 0
if budget_pct >= 95:
    print(f"  BUDGET CRITICAL: {budget_pct:.0f}% consumed — completing current work only")
    # Only allow FIX, RUN_QC, and EXIT_GATE actions at 95%+
    action = decide_next_action(config, state)
    if action not in (Action.FIX, Action.RUN_QC, Action.EXIT_GATE,
                      Action.INTERACTIVE_PAUSE):
        action = Action.EXIT_GATE  # Force exit gate attempt
elif budget_pct >= 80:
    print(f"  BUDGET WARNING: {budget_pct:.0f}% consumed — economizing")
    # VRC adapts: force quick mode only (handled in run_vrc via budget check)
```

**Enhanced delivery report:**

```python
def generate_delivery_report(config, state):
    vrc = state.latest_vrc
    passed = len([v for v in state.verifications.values() if v.status == "passed"])
    lines = [
        f"# Delivery Report: {config.sprint}", "",
        "## Summary",
        f"- Value score: {vrc.value_score:.0%}" if vrc else "- Value score: N/A",
        f"- Tasks completed: {len([t for t in state.tasks.values() if t.status == 'done'])}/{len(state.tasks)}",
        f"- QC checks: {passed}/{len(state.verifications)} passing",
        f"- Iterations: {state.iteration}",
        f"- Exit gate attempts: {state.exit_gate_attempts}",
        f"- Tokens used: {state.total_tokens_used:,}", "",
        "## Deliverables",
    ]
    for t in state.tasks.values():
        status = {"done": "DELIVERED", "descoped": "DESCOPED", "blocked": "BLOCKED"}.get(t.status, t.status)
        lines.append(f"- [{status}] {t.task_id}: {t.description}")
        if t.status == "descoped":
            lines.append(f"  Reason: {t.blocked_reason}")
    (config.sprint_dir / "DELIVERY_REPORT.md").write_text("\n".join(lines))
    git_commit(config, state, f"telic-loop({config.sprint}): Delivery complete" +
               (f" — {vrc.value_score:.0%} value" if vrc else ""))
```

---

## 7. Quick Coherence Check (Dimensions 1-2)

Automated structural analysis — no LLM cost for quick mode.

```python
def quick_coherence_check(config: LoopConfig, state: LoopState) -> CoherenceReport | None:
    """
    Quick coherence check: Dimensions 1 (Structural Integrity) and 2 (Interaction Coherence).
    Automated analysis — no LLM invocation needed.
    Runs every coherence_quick_interval tasks.
    """
    state.tasks_since_last_coherence += 1
    if state.tasks_since_last_coherence < config.coherence_quick_interval:
        return None

    state.tasks_since_last_coherence = 0
    timestamp = datetime.now().isoformat()

    # Dimension 1: Structural Integrity (automated)
    structural = assess_structural_integrity(config)

    # Dimension 2: Interaction Coherence (automated)
    interaction = assess_interaction_coherence(config, state)

    # Determine overall status
    statuses = [structural["status"], interaction["status"]]
    if "CRITICAL" in statuses:
        overall = "CRITICAL"
    elif "WARNING" in statuses:
        overall = "WARNING"
    else:
        overall = "HEALTHY"

    report = CoherenceReport(
        iteration=state.iteration,
        mode="quick",
        timestamp=timestamp,
        dimensions={
            "structural_integrity": structural,
            "interaction_coherence": interaction,
        },
        overall=overall,
    )
    state.coherence_history.append(report)

    if overall == "CRITICAL":
        print(f"  COHERENCE CRITICAL — structural issues detected")
        # Flag forces course correction on next decision cycle
        state.coherence_critical_pending = True

    return report


def assess_structural_integrity(config: LoopConfig) -> dict:
    """
    Analyze project structure for dependency issues and module health.
    Uses file system analysis and import parsing — no LLM.
    """
    findings = []
    sprint_dir = config.sprint_dir

    # Check for circular imports (Python files)
    py_files = list(sprint_dir.rglob("*.py"))
    import_graph = {}
    for f in py_files:
        try:
            content = f.read_text(errors="ignore")
            imports = [line.split()[1].split(".")[0]
                       for line in content.split("\n")
                       if line.startswith("import ") or line.startswith("from ")]
            import_graph[f.stem] = imports
        except Exception:
            continue

    # Simple cycle detection
    for module, imports in import_graph.items():
        for imp in imports:
            if imp in import_graph and module in import_graph.get(imp, []):
                findings.append(f"Circular import: {module} <-> {imp}")

    # Check for God modules (files > 500 lines)
    for f in py_files:
        try:
            lines = len(f.read_text(errors="ignore").split("\n"))
            if lines > 500:
                findings.append(f"Large module ({lines} lines): {f.name}")
        except Exception:
            continue

    status = "WARNING" if findings else "HEALTHY"
    return {"status": status, "findings": findings, "trend": "stable"}


def assess_interaction_coherence(config: LoopConfig, state: LoopState) -> dict:
    """
    Check cross-cutting concern consistency using pattern matching.
    Uses file system analysis — no LLM.
    """
    findings = []
    sprint_dir = config.sprint_dir

    py_files = list(sprint_dir.rglob("*.py"))

    # Check for inconsistent error handling patterns
    bare_excepts = 0
    specific_excepts = 0
    for f in py_files:
        try:
            content = f.read_text(errors="ignore")
            bare_excepts += content.count("except:")
            bare_excepts += content.count("except Exception:")
            specific_excepts += content.count("except ") - content.count("except:") - content.count("except Exception:")
        except Exception:
            continue

    if bare_excepts > specific_excepts and bare_excepts > 3:
        findings.append(f"Inconsistent error handling: {bare_excepts} bare/generic excepts vs {specific_excepts} specific")

    # Check task churn (tasks oscillating between states)
    churn_tasks = [t for t in state.tasks.values() if t.retry_count >= 3]
    if churn_tasks:
        findings.append(f"{len(churn_tasks)} tasks with 3+ retries — potential interaction issue")

    status = "WARNING" if findings else "HEALTHY"
    if any("churn" in f for f in findings):
        status = "CRITICAL"
    return {"status": status, "findings": findings, "trend": "stable"}
```

---

## 8. Migration Checklist (Phase 2)

### VRC
- [ ] Implement `phases/vrc.py` — run_vrc, build_task_summary, format_latest_vrc
- [ ] Rewrite prompt: `vrc.md` (full + quick modes, structured tool output)
- [ ] Add report_vrc structured tool schema + handle_vrc handler
- [ ] Wire VRC heartbeat into value loop (after action, before save)

### Course Correction
- [ ] Implement `phases/course_correct.py` — do_course_correct (replace stub)
- [ ] Create prompt: `course_correct.md`
- [ ] Add report_course_correction structured tool schema + handler

### Plan Health Check
- [ ] Implement `phases/plan_health.py` — maybe_run_plan_health_check
- [ ] Create prompt: `plan_health_check.md`
- [ ] Wire plan health into value loop (after CC, threshold-based)

### Exit Gate
- [ ] Implement `phases/exit_gate.py` — do_exit_gate (replace stub)
- [ ] Create prompt: `exit_gate.md`
- [ ] Wire exit gate into value loop (replaces simple completion)

### Budget
- [ ] Add budget-aware behaviors in value loop
- [ ] Enhance generate_delivery_report with VRC score + exit gate stats

### Quick Coherence
- [ ] Implement `phases/coherence.py` — quick_coherence_check, assess_structural_integrity, assess_interaction_coherence
- [ ] Wire quick coherence into value loop (after VRC, interval-based)
- [ ] Add CoherenceReport and coherence_history to state
- [ ] Add Phase 3 stubs: do_full_coherence_eval → no-op (decision engine P8b wired in Phase 1)
- [ ] Verify Phase 1 stubs still correct: classify_vision_complexity → "single_run", decompose_into_epics → no-op
- [ ] Add Phase 3 stub: epic_feedback_checkpoint → no-op

### Integration
- [ ] Test VRC heartbeat end-to-end (verify vrc_history grows)
- [ ] Test course correction trigger (force stuck state)
- [ ] Test exit gate flow (pass and fail scenarios)
- [ ] Test budget exhaustion (low token_budget)
- [ ] Test quick coherence triggers (verify interval-based firing)

---

## Appendix: Phase 2 Structured Tool Schemas

### report_vrc
```python
{"name": "report_vrc", "input_schema": {"properties": {
    "value_score": {"type": "number", "minimum": 0, "maximum": 1},
    "deliverables_verified": {"type": "integer"},
    "deliverables_total": {"type": "integer"},
    "deliverables_blocked": {"type": "integer", "default": 0},
    "gaps": {"type": "array", "items": {"type": "object", "properties": {
        "id": {"type": "string"}, "description": {"type": "string"},
        "severity": {"type": "string", "enum": ["critical","blocking","degraded","polish"]},
        "suggested_task": {"type": "string"},
    }}},
    "recommendation": {"type": "string", "enum": ["CONTINUE","COURSE_CORRECT","DESCOPE","SHIP_READY"]},
    "summary": {"type": "string"},
}, "required": ["value_score", "deliverables_verified", "deliverables_total",
                "recommendation", "summary"]}}
```

### report_course_correction
```python
{"name": "report_course_correction", "input_schema": {"properties": {
    "action": {"type": "string", "enum": ["restructure","descope","new_tasks","rollback","regenerate_tests","escalate"]},
    "reason": {"type": "string"},
    "rollback_to_checkpoint": {"type": "string", "description": "(rollback only) checkpoint label to revert to"},
    "tasks_to_restructure": {"type": "string", "description": "(rollback only) how reverted tasks should be re-approached"},
}, "required": ["action", "reason"]}}
```

### report_coherence
```python
{"name": "report_coherence", "input_schema": {"properties": {
    "mode": {"type": "string", "enum": ["quick", "full"]},
    "dimensions": {"type": "object", "additionalProperties": {"type": "object", "properties": {
        "status": {"type": "string", "enum": ["HEALTHY", "WARNING", "CRITICAL"]},
        "findings": {"type": "array", "items": {"type": "string"}},
        "trend": {"type": "string", "enum": ["improving", "stable", "degrading"]},
    }}},
    "overall": {"type": "string", "enum": ["HEALTHY", "WARNING", "CRITICAL"]},
    "top_findings": {"type": "array", "items": {"type": "object", "properties": {
        "dimension": {"type": "string"}, "severity": {"type": "string"},
        "description": {"type": "string"}, "affected_files": {"type": "array", "items": {"type": "string"}},
        "suggested_action": {"type": "string"}, "leverage_level": {"type": "integer"},
    }}},
    "comparison_to_previous": {"type": "string"},
}, "required": ["mode", "dimensions", "overall"]}}
```
