# Loop V3: Product Requirements Document

**Date**: 2026-02-15
**Vision**: V3_VISION.md
**Architecture**: V3_ARCHITECTURE.md

---

## Problem Statement

### Why V3?

Loop V2 delivers technical output but not reliably usable outcomes. Key failures:

| V2 Problem | V3 Solution |
|------------|-------------|
| Builder grades its own work | Separate Builder, QC, and Evaluator agents |
| Post-loop verification is a dead end | Exit gate is inside the loop — failures become tasks |
| No course correction | Opus diagnoses stuck states and restructures |
| Web app assumptions hardcoded | Technology-agnostic — discovered from context |
| Agents edit markdown plan files | Structured tools + JSON state |
| No external knowledge when stale | Research agent searches web for current docs |
| Human blockers kill the loop | Interactive Pause: instruct, wait, verify, resume |
| No experience evaluation | Critical Evaluator uses deliverable as real user |
| Fixed test tiers | Dynamic verification from discovered strategy |

### Who Is This For?

A non-technical user who has a Vision (what they want) and a PRD (what to build). They don't know how to build it, debug it, or verify it. The loop does all of that autonomously and delivers a working outcome.

---

## Phasing Strategy

The system is built incrementally in 3 phases. Each phase is usable on its own.

### Phase 1: Builder + QC + Decision Engine (MVP)

**Can deliver**: Simple projects where the plan is straightforward and doesn't need mid-loop correction.

- Pre-loop: input validation, context discovery, PRD critique, plan generation, quality gates, blocker resolution, preflight
- Value loop: execute → QC → fix → interactive pause
- Exit condition: all tasks done + all QC passes (simple completion check)
- **Not included**: VRC heartbeat, course correction, exit gate, critical evaluation, research, process monitor, vision validation

### Phase 2: +VRC + Course Correction + Exit Gate

**Can deliver**: Complex projects requiring mid-loop adaptation and value verification.

- Adds: VRC heartbeat every iteration, course correction, plan health check, exit gate, budget tracking
- Exit condition: Exit gate passes (fresh-context VRC + full regression + critical eval)
- **Not included**: Critical evaluation, external research, process monitor, vision validation

### Phase 3: +Critical Eval + Research + Process Monitor + Vision Validation

**Can deliver**: The full V3 system as specified in the Vision.

- Adds: Critical evaluation (Evaluator agent), external research, process monitor (3-layer), vision validation (5-pass), full task mutation guardrails

---

## Functional Requirements

### Pre-Loop

#### R1: Input Validation (Phase 1)
Verify VISION.md and PRD.md exist in sprint directory. Missing files produce clear error message and exit code 1.
**Done when**: Loop exits cleanly with actionable error if inputs are missing.

#### R2: Context Discovery (Phase 1)
Opus examines Vision + PRD + codebase + environment and produces a SprintContext with deliverable_type, project_type, codebase_state, environment, services, verification_strategy, and value_proofs. Unresolved questions surfaced for interactive pause.
**Done when**: SprintContext is populated and saved to state. Discovery agent uses `report_discovery` tool.

#### R3: PRD Critique (Phase 1)
Opus aggressively challenges PRD feasibility. Verdict: APPROVE, AMEND, DESCOPE, or REJECT. AMEND includes specific amendments. REJECT triggers interactive refinement (Phase 3): loop researches feasible alternatives, presents to human, human revises PRD, re-critiques until achievable. Phase 1 stub warns on REJECT but proceeds.
**Done when**: PRD is either approved, amended, or refined to achievable scope. Critique agent uses `report_critique` tool.

#### R4: Plan Generation (Phase 1)
Opus generates tasks via `manage_task` tool calls. Each task has task_id, description, value, acceptance criteria, dependencies, phase, and files_expected.
**Done when**: `state.tasks` is populated. All tasks have required fields. Dependency graph is valid.

#### R5: Quality Gates (Phase 1)
Plan passes CRAAP, CLARITY, VALIDATE, CONNECT, BREAK, PRUNE, TIDY gates. Each gate uses `manage_task` to remediate issues found.
**Done when**: All 7 gates pass in sequence. Each gate's passage recorded in `state.gates_passed`.

#### R6: Blocker Resolution (Phase 1)
All blocked tasks are either unblocked or descoped. No task remains blocked unless it has a HUMAN_ACTION prefix (deferred to interactive pause).
**Done when**: Zero tasks with status "blocked" (except human-action blockers).

#### R7: Preflight Check (Phase 1)
Environment requirements from SprintContext verified: tools exist, env vars set, services reachable.
**Done when**: All checks pass. Failures produce actionable error messages with resolution steps.

#### R8: Vision Refinement (Phase 3)
5-pass validation (extraction, force analysis, causal audit, pre-mortem, synthesis) challenges Vision before any work starts. Issues classified as HARD (impossible/contradictory — must resolve) or SOFT (risky — can acknowledge). Interactive refinement loop: loop researches alternatives for HARD issues, presents findings with recommendations, human revises VISION.md, loop re-analyzes. Iterates until consensus — never exits silently. HARD issues cannot be overridden; SOFT issues can be acknowledged.
**Done when**: All HARD issues resolved and SOFT issues acknowledged (or no issues). Uses `report_vision_validation` tool. PRD critique follows same interactive model on REJECT.

#### R28: Vision Complexity Classification (Phase 3)
After Vision Validation, classify vision as `single_run` (simple, <15 tasks, ≤3 deliverables) or `multi_epic` (complex, requires decomposition). Classification is deterministic from vision characteristics.
**Done when**: `state.vision_complexity` is set. Simple visions skip epic decomposition entirely.

#### R29: Epic Decomposition (Phase 3)
For `multi_epic` visions, decompose into 2-5 epics. Each epic delivers independently demonstrable value (horizontal slicing, not vertical). Epic 1 is fully detailed; later epics are sketched. Uses `report_epic_decomposition` tool.
**Done when**: `state.epics` populated with ordered epics. Each has value_statement, deliverables, completion_criteria.

#### R30: Epic Feedback Checkpoint (Phase 3)
After each epic's exit gate passes, generate a curated summary and present to human with Proceed/Adjust/Stop options. Auto-proceed on configurable timeout (default 30 minutes). Human response (or timeout) recorded in `Epic.feedback_response`.
**Done when**: Summary generated and presented. Response (or timeout) logged. Next epic begins or loop exits based on response.

### Value Loop — Execution

#### R9: Task Execution — Builder Agent (Phase 1)
Builder agent (Sonnet, multi-turn) executes a task, signals completion via `report_task_complete` with files_created, files_modified. Regression runs after execution. Max `retry_count` enforced if agent fails to call completion tool.
**Done when**: Task transitions from "pending" to "done" with completion metadata populated.

#### R10: Task Selection (Phase 1)
`pick_next_task()` selects the highest-priority pending task whose dependencies are all met. Priority: highest-dependency tasks first (unblock others), then by phase order.
**Done when**: Tasks execute in a valid dependency order.

#### R11: Regression (Phase 1)
After every task execution, all previously-passing QC checks re-run. Regressions are flagged immediately.
**Done when**: Any regression is detected within 1 iteration of the breaking change.

### Value Loop — Quality Control

#### R12: QC Generation (Phase 1)
QC agent generates verification scripts from discovered verification_strategy, not hardcoded tiers. Scripts are executable (subprocess) and return pass/fail.
**Done when**: VerificationState entries exist with script_path. Scripts are runnable.

#### R13: QC Execution (Phase 1)
QC scripts run in subprocess with timeout. Results update VerificationState. Parallel execution supported.
**Done when**: All QC checks have been run. Status is "passed" or "failed" per check.

#### R14: Triage + Fix (Phase 1)
Failed QC checks triaged by root cause (Haiku). Fix agent (Sonnet) gets full error history, attempt history, and optionally research context. Orchestrator re-runs QC after fix to verify — builder never self-grades.
**Done when**: Fix agent attempts repair. Orchestrator verifies by re-running the failing QC check.

#### R15: Service Health Check (Phase 1)
For software deliverables with services, check all services before executing. Fix broken services before proceeding.
**Done when**: `all_services_healthy()` returns True before task execution (software only).

### Value Loop — Human Interaction

#### R16: Interactive Pause (Phase 1)
Human-only blockers trigger a pause with step-by-step instructions. Verification command checks completion. Timeout and max retries enforced.
**Done when**: Loop pauses with clear instructions. Resumes after verification passes. Times out gracefully.

### Value Loop — Adaptation

#### R17: VRC Heartbeat (Phase 2)
VRC runs every iteration. Quick mode (Haiku — metrics only) on most iterations; full mode (Opus — examines deliverable) every Nth. Results stored in vrc_history. Gaps can create tasks via `manage_task`.
**Done when**: VRC runs every iteration. vrc_history grows monotonically. Recommendations influence decision engine.

#### R18: Course Correction (Phase 2)
When stuck or VRC says COURSE_CORRECT, Opus restructures plan, descopes features, or adds new tasks. Max course corrections enforced.
**Done when**: Opus agent diagnoses stuck state and restructures. Uses `report_course_correction` and `manage_task`.

#### R19: Plan Health Check (Phase 2)
After N mid-loop tasks created or after course correction, Opus sweeps new tasks for DRY violations, contradictions, missing dependencies, scope drift. Uses `manage_task` to fix issues.
**Done when**: `maybe_run_plan_health_check()` triggers appropriately. New tasks are validated.

#### R20: Exit Gate (Phase 2)
Fresh-context verification: full regression + full VRC (Opus, forced full) + final critical eval. If any fails, gaps become tasks and loop continues. Max attempts enforced with partial delivery.
**Done when**: Exit gate is inside the loop. Failures create tasks. Max attempts → partial report.

#### R21: Budget Tracking (Phase 2)
`state.total_tokens_used` tracked accurately via ClaudeSession. VRC frequency adapts at 80% budget. Warn at 80%, wrap-up at 95%, partial delivery at 100%.
**Done when**: Token budget is enforced. Budget exhaustion produces partial delivery report.

### Value Loop — Intelligence

#### R22: Critical Evaluation (Phase 3)
Evaluator agent (Opus, read-only tools) uses deliverable as real user every N tasks. Findings categorized by severity (critical/blocking/degraded/polish). Critical/blocking findings auto-create tasks via `manage_task`.
**Done when**: Evaluator runs periodically. Findings create tasks. Uses `report_eval_finding`.

#### R23: External Research (Phase 3)
When fix attempts exhausted, research agent (Opus + web_search + web_fetch) finds current documentation, known issues, workarounds. Research brief injected into fix agent context. Staleness tracking prevents repeat research.
**Done when**: Research fires after fix exhaustion. Findings stored in research_briefs. Uses `report_research`.

#### R24: Process Monitor (Phase 3)
Layer 0 (metric collectors) runs every iteration at zero cost. Layer 1 (trigger evaluation) checks thresholds at zero cost. Layer 2 (Strategy Reasoner, Opus) fires only on RED trigger (~2-4 per sprint).
**Done when**: Metrics collected every iteration. RED trigger invokes Opus. Strategy changes update execution parameters.

#### R31: Quick Coherence Check (Phase 2)
Automated structural analysis (Dimensions 1-2: Structural Integrity + Interaction Coherence) runs every N tasks. Checks dependency health, cross-cutting concern consistency, and interaction safety. No LLM cost for quick mode.
**Done when**: Quick coherence runs at configured interval. CRITICAL findings trigger Course Correction. Uses `report_coherence` tool.

#### R32: Full Coherence Evaluation (Phase 3)
All 7 dimensions (Structural Integrity, Interaction Coherence, Conceptual Integrity, Behavioral Consistency, Informational Flow, Resilience, Evolutionary Capacity) evaluated at epic boundaries and pre-exit-gate. Uses Opus for semantic analysis.
**Done when**: Full evaluation runs at epic boundaries. Findings feed into Course Correction. Trends tracked in `coherence_history`.

### Infrastructure

#### R25: Decision Engine (Phase 1)
`decide_next_action()` implements all priority levels deterministically from state. No LLM involved. Phase 1 implements priorities 0-7,9; Phase 2 adds priorities 2(full),8b(coherence eval),8,9(exit gate); Phase 3 adds priority 8(critical eval).
**Done when**: Decision is deterministic, correct, and matches priority table in Architecture Reference.

#### R26: State Persistence (Phase 1)
LoopState serializes to `.loop_state.json` and deserializes correctly. Sets round-trip through JSON (set → sorted list → set). Loop can resume from any saved state.
**Done when**: Save + load round-trips preserve all state. Loop resumes correctly from checkpoint.

#### R27: Rendered Views (Phase 1)
`render.py` generates IMPLEMENTATION_PLAN.md, VALUE_CHECKLIST.md, DELIVERY_REPORT.md from state. Pure functions, no state mutation. Agents read these for context but never write to them.
**Done when**: Rendered markdown is correct and up-to-date. No agent writes to rendered files.

---

## Non-Functional Requirements

### NF1: Platform Compatibility
Must run on Windows (primary development environment), Linux, and macOS. Use `pathlib` for paths. Use `subprocess.run(shell=False)` with list args where possible. Detect platform in preflight.

### NF2: Cost Efficiency
Token budget tracking via `state.total_tokens_used`. VRC frequency adapts (quick/full modes). Process Monitor overhead < 5% (~$3-6 per sprint at 2-4 Opus invocations). Budget ceiling: 80% efficiency mode, 95% wrap-up, 100% partial delivery.

### NF3: Resumability
Loop can stop and resume from saved state at any point. State file (`.loop_state.json`) is the complete execution record. No external dependencies for state.

### NF4: Context Window Management
No single agent session should approach context window limits. Track token count per session. Summarize or restart sessions at 80% capacity.

### NF5: Authentication
Anthropic SDK auto-detects auth from environment (`ANTHROPIC_API_KEY` or `~/.anthropic/config`). First API call surfaces auth issues immediately. No explicit key validation code needed.

### NF6: Dependencies
Minimal: `anthropic>=0.40.0`, `requests>=2.31.0`. No ML libraries, no database, no additional infrastructure.

---

## E2E Test Scenarios

### E2E-1: Simple Greenfield Project
**Setup**: Vision describes a simple Flask app with one page. PRD has 3 requirements.
**Expected**: Pre-loop discovers "software/web_app/greenfield", generates plan with ~5 tasks. Builder implements. QC generates tests. All pass. Exit condition reached. Delivery report shows 100% value.
**Validates**: R1-R7, R9-R15, R25-R27.

### E2E-2: Brownfield Feature Addition
**Setup**: Existing codebase with tests. Vision adds one feature.
**Expected**: Pre-loop discovers "software/web_app/brownfield", finds existing tests. Plan integrates with existing code. Regression catches any breakage. Feature delivered without breaking existing functionality.
**Validates**: R2, R9, R11, R12.

### E2E-3: Human Blocker Mid-Loop
**Setup**: Vision requires OAuth. No OAuth credentials configured.
**Expected**: Context Discovery surfaces missing credentials. Interactive Pause fires with step-by-step OAuth setup instructions. Loop pauses. After human provides credentials, verification command confirms. Loop resumes.
**Validates**: R2, R16.

### E2E-4: Stuck State Recovery
**Setup**: A task consistently fails QC after max_fix_attempts.
**Expected**: Decision engine triggers RESEARCH (if not already attempted). If research doesn't help, triggers COURSE_CORRECT. Opus restructures or descopes. Loop recovers.
**Validates**: R14, R18, R23, R25.

### E2E-5: Budget Exhaustion
**Setup**: Token budget set to a low value.
**Expected**: At 80%, VRC adapts frequency. At 95%, loop wraps up current work. At 100%, partial delivery report generated with what was completed.
**Validates**: R21, R27.

### E2E-6: Multi-Epic Complex Vision
**Setup**: Vision describes a complex system with 4+ independently valuable deliverables (e.g., "build a project management tool with user auth, kanban boards, time tracking, and reporting").
**Expected**: Vision Validation passes. Complexity Classification → `multi_epic`. Epic Decomposition produces 3-4 epics with horizontal value slicing. Epic 1 delivers core functionality end-to-end. After Epic 1 exit gate, human receives curated summary. Auto-proceed on timeout starts Epic 2. Each epic builds on the previous.
**Validates**: R8, R28, R29, R30.

### E2E-7: Coherence Degradation Detection
**Setup**: Project with 5+ features. Deliberately inconsistent error handling patterns across features.
**Expected**: Quick Coherence (Phase 2) flags cross-cutting concern inconsistency as WARNING or CRITICAL. Full Coherence (Phase 3) identifies specific dimensions affected. Course Correction addresses the finding.
**Validates**: R31, R32.

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Vision is flawed (right execution, wrong outcome) | Entire sprint wasted | 5-pass Vision Validation (Phase 3) |
| Opus cost for continuous VRC | High token spend | Quick/full VRC mode split (Phase 2) |
| Critical evaluator makes destructive changes | Data loss | Evaluator agent gets read-only tools |
| Interactive pause never resumes (human forgets) | Loop stuck | Timeout + max retries + abort/descope |
| Exit gate loops forever (keeps finding issues) | Never exits | Max exit gate attempts → partial report |
| Course correction loops (keeps restructuring) | Never converges | Max corrections per sprint |
| Mid-loop tasks bypass quality gates | DRY violations, drift | Layer 1: deterministic guardrails. Layer 2: Opus health sweep |
| Decision engine picks wrong action | Wasted iterations | Deterministic priority order; VRC catches drift |
| Context window overflow in long sessions | Agent loses context | Token tracking, session restart at 80% |
| PRD critique too aggressive (rejects good PRDs) | Blocks valid work | AMEND option; user can override |
| Regression suite grows too slow | Bottleneck | Timeout budget, parallel execution |
| Technology-agnostic = too generic | Loses useful defaults | Context Discovery derives smart defaults |
| Research returns irrelevant results | Wrong fix direction | Opus reviews relevance; discard low-confidence |
| Web search unavailable or rate-limited | Research can't proceed | Graceful fallback; research is advisory, not blocking |
| Process Monitor overhead | Costs more than saves | Layers 0-1 free; Layer 2 fires 2-4 times (~$3-6) |
| Token budget exhausted mid-delivery | Incomplete value | Budget tracking; VRC adapts; warn at 80% |
| Windows platform compatibility | chmod unavailable, shell syntax | pathlib, subprocess.run(shell=False) |
| Auth misconfiguration | First API call fails | Claude class surfaces auth errors immediately |
| Epic decomposition too granular | Too many small epics = overhead | Max 5 epics; merge 1-2 task epics with adjacent |
| Human never responds to epic checkpoint | Could block indefinitely | Auto-proceed on timeout (configurable, default 30 min) |
| Coherence eval too expensive | Token cost at every interval | Quick mode is automated (no LLM); Full mode only at boundaries |
| Coherence findings conflict with VRC | Mixed signals about system health | Coherence = structural health, VRC = value delivery — complementary |
| Vision wrongly classified as single_run | Missed epic boundaries | Classification is conservative — any complexity signal → multi_epic |

---

## Success Metrics

| Metric | V2 Baseline | V3 Target |
|--------|-------------|-----------|
| Manual debugging after loop | Hours | Zero |
| Time to detect broken service | ~15 iterations | 1 iteration (pre-check) |
| Fix agent success rate | ~20% (blind) | ~70% (with context + regression) |
| Regression detection | End of sprint (if at all) | After every task |
| Experience evaluation | Never (tests only) | Every 3 tasks (separate Evaluator agent) |
| Builder self-grading | Always (builder runs own tests) | Never (QC agent + Evaluator are separate) |
| Human blockers mid-loop | Loop dies or skips | Interactive Pause (instruct, verify, resume) |
| Final verification fails | Dead end (post-loop) | Exit gate inside loop — gaps become tasks |
| PRD feasibility check | Never | Before first line of code |
| VRC frequency | 2 per sprint | Every iteration |
| Course correction capability | None (human intervenes) | Automatic (Opus diagnoses + restructures) |
| Knowledge-limited fixes | Always (training data only) | Research agent acquires current knowledge |
| Technology lock-in | Web app only | Any project type |
| Human feedback during execution | None (fire and forget) | Between-epic checkpoints with auto-proceed |
| System-level coherence | Not checked | Quick + Full coherence evaluation |
| Complex vision handling | Single monolithic run | Epic decomposition with staged delivery |
