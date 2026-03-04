# V3 Post-Mortem: Complexity Trap

**Date:** 2026-03-03
**Author:** Human + Claude (analysis session)
**Scope:** 16 e2e test runs, Feb 16 - Mar 3, 2026

## Executive Summary

Telic Loop V3 began as an elegant vision: a decision-driven, deliverable-agnostic value delivery algorithm. Over 16 test runs and hundreds of commits, it grew into a 9,610-line, 28-module system with 34 prompt templates — and the results got worse, not better. The last 4 of 6 runs were killed manually. The same sprint that completed successfully on Feb 17 (recipe-manager: 39 iterations, 1.03M tokens, 3/3 epics) failed catastrophically on Mar 3 (recipe-mgr-v2: 45 iterations, 785k tokens, 0/3 epics completed).

The system is in a complexity trap: each failure leads to a new subsystem, each subsystem creates new failure modes, and the interaction effects are beyond what either human or AI can reliably reason about.

---

## 1. The Vision vs. Reality

### What the Vision Promised

From `docs/V3_VISION.md`:

> "The loop is not a code generator. It is not a software engineering tool. It is a **closed-loop value delivery system**."

The core algorithm was supposed to be:

```
while not value_delivered:
    decision = decide_next_action(state)    # deterministic, no LLM
    execute(decision)
    verify()
    if stuck: course_correct()
```

**8 core concepts:** Vision, PRD, Task, QC, Critical Eval, VRC, Course Correct, Exit Gate.

**Key promises:**
1. Self-configuring — human provides Vision + PRD, loop figures out everything else
2. Decision-driven, not phase-driven — state determines action, not rigid sequences
3. Deliverable-agnostic — same algorithm for web apps, CLIs, documents, data
4. Minimal human intervention — "no babysitting, near-zero post-loop cleanup"
5. Separate agents for separate concerns — builder never grades own work
6. Honest about failure — "delivers value or honestly reports why it can't"

### What We Actually Built

**28 Python files. 9,610 lines of code. 34 prompt templates (5,614 lines). 11 action types. 18+ gates. 40+ interacting subsystems.**

| Vision Promise | Reality |
|---|---|
| Self-configuring | 1,293-line `discovery.py` that still misses Node.js, misclassifies project types |
| Decision-driven | 260-line decision engine surrounded by 4,241 lines of phase handlers with their own internal state machines |
| Deliverable-agnostic | Hardcoded to web apps: Playwright MCP, port checking, uvicorn health URLs. Zero non-software runs ever attempted |
| Minimal human intervention | 4 of last 6 runs required manual kills |
| Separate agents | 7+ agent roles, each requiring Opus-level context, burning 15-40k tokens per invocation |
| Honest about failure | `no_progress_count` stays at 0 while fix/service_fix oscillates for 13 iterations because SERVICE_FIX reports "progress" |

### The Subsystem Inventory

The vision described 8 concepts. We built 40+ subsystems:

**Pre-loop (before any work happens):**
- Vision validation (5-pass analysis, Opus)
- Complexity classification (single_run vs multi_epic)
- Epic decomposition (2-5 value blocks, Opus)
- Context discovery (1,293 lines, Opus)
- PRD critique (Opus)
- Service bootstrap (greenfield scaffold)
- 7 quality gates: CRAAP, CLARITY, VALIDATE, CONNECT, BREAK, PRUNE, TIDY (all Opus)
- Blocker resolution
- Preflight check
- Plan generation (Opus)
- VRC initialization

**Value loop:**
- Decision engine (P0-P9 priorities)
- Task execution with snapshot/rollback
- QC generation + parallel script execution
- Fix cycle with attempt tracking
- Service health monitoring
- Research with web search
- Course correction with strategy selection
- Critical evaluation (browser + non-browser)
- VRC heartbeat (quick/full, gap task creation)
- Coherence evaluation (7 dimensions)
- Process monitor (3 levels, strategy reasoner)
- Plan health checks
- Code quality scanner (debug artifacts, dead code, long functions, duplicates, monoliths, PRD conformance)
- Exit gate (4-step verification)
- Epic boundary evaluation
- Epic task tagging

**Cross-cutting:**
- Docker integration
- Documentation generation
- Rate limit handling
- Platform error detection (Windows/MSYS)
- Crash logging and auto-restart

---

## 2. The Evidence: All 16 Runs

| # | Sprint | Date | Iters | Tokens | Epics | Result |
|---|--------|------|-------|--------|-------|--------|
| 1 | todo-app | Feb 16 | 6 | 134k | 1 | PASS |
| 2 | temp-calc | Feb 16 | 3 | 75k | 1 | PASS |
| 3 | smart-dash | Feb 17 | 8 | 349k | 1 | PASS |
| 4 | kanban | Feb 17 | 7 | 231k | 1 | PASS |
| 5 | time-tracker | Feb 17 | 14 | 327k | 1 | PASS |
| 6 | recipe-manager | Feb 17-18 | 39 | 1.03M | 3/3 | PASS |
| 7 | beep2b | Feb 18-19 | 63 | 1.09M | 3/3 | PASS |
| 8 | beep2b-v2 | Feb 19-20 | 54 | 1.19M | 1 | PASS |
| 9 | stockr | Feb 21 | 63 | 1.03M | 1 | PASS |
| 10 | beep2b-v3 | Feb 20-21 | 157 | 1.67M | 3/3 | **KILLED** |
| 11 | epic-test | Feb 22 | 10 | 231k | 2/2 | PASS |
| 12 | linkvault | Feb 23-24 | 42 | 818k | 2/2 | **KILLED** |
| 13 | pagecraft | Feb 25-26 | 159 | 3.83M | 3/3 | **KILLED** |
| 14 | fixcheck | Feb 27 | 23 | 1.07M | 1 | PASS |
| 15 | qctest | Feb 28-Mar 1 | 35 | 398k | 2 | PASS |
| 16 | recipe-mgr-v2 | Mar 3 | 45 | 785k | 0/3 | **KILLED** |

### The Trend

**Early runs (1-6):** Small, focused, successful. The system worked because it was simple.

**Middle runs (7-9):** Larger, mostly successful but token-hungry. Bug fixes started accumulating.

**Late runs (10-16):** Increasingly unreliable. 4 of 7 killed manually. The same sprint (recipe-manager) that succeeded on Feb 17 failed on Mar 3.

### The Damning Comparison

| Metric | recipe-manager (Feb 17) | recipe-mgr-v2 (Mar 3) |
|--------|------------------------|----------------------|
| Identical PRD | Yes | Yes |
| Iterations | 39 (complete) | 45 (Epic 1 only, killed) |
| Tokens | 1.03M (3 epics) | 785k (0 epics complete) |
| Code quality tasks | ~3 | ~13 (cascading) |
| Critical evals | At least 1 | 0 |
| Outcome | 3/3 epics, 100% value | Stuck in fix/service_fix loop |

More code. Worse results.

---

## 3. Failure Modes Discovered

### 3.1 Code Quality Task Cascade

**Files:** `code_quality.py` (778 lines)

The code quality scanner runs after each task and creates SPLIT-FN, REFACTOR, DEDUP, CLEANUP, and STRUCTURE tasks for any file exceeding its thresholds. In recipe-mgr-v2:

1. Builder creates `recipes.js` (687 lines)
2. Scanner creates REFACTOR-recipes.js task
3. Refactoring splits into `recipes-main.js`, `recipes-detail.js`, `recipes-original-backup.js`
4. Scanner finds long functions in the NEW files, creates more SPLIT-FN tasks
5. Scanner finds `recipes-original-backup.js` and creates a REFACTOR task for the BACKUP file
6. PRD conformance check flags `recipes.js` as "missing" (it was renamed)
7. 14 iterations consumed by cascading cleanup

**Root cause:** Each scan operates on the current filesystem without memory of what previous scans already addressed. Refactoring creates new files that trigger new scans.

### 3.2 Fix/SERVICE_FIX Oscillation

**Files:** `decision.py` (P1 + P4), `execute.py`, `qc.py`

When the FIX agent modifies application code to fix a failing test, it can break the running server:

1. FIX modifies `routes/recipes.py` → Python syntax error or import break
2. Server crashes (uvicorn exits)
3. Decision engine: P1 SERVICE_FIX fires (services unhealthy)
4. SERVICE_FIX restarts the server → reports "progress"
5. Decision engine: P4 FIX fires (tests still failing)
6. FIX modifies code again → breaks server again
7. Goto 2

This ran for **13 consecutive iterations** in recipe-mgr-v2 (iterations 30-42). The `no_progress_count` stayed at 0 the entire time because SERVICE_FIX reports "progress" even though no actual progress toward fixing the tests was made.

**Root cause:** SERVICE_FIX's "progress" result masks the stuck state from the decision engine's stuck detection.

### 3.3 Research Flag Reset Loop

**Files:** `decision.py` (P4 exhaustion path), `state.py`

The P4 exhaustion path is: FIX (N attempts) → RESEARCH → COURSE_CORRECT → block tests. But:

1. FIX exhausts attempts (att >= max_fix_attempts)
2. RESEARCH fires, analyzes the problem, creates remediation tasks
3. Something (likely a subsequent FIX or task execution) modifies the verification scripts
4. `research_attempted_for_current_failures` resets to False (failure set changed)
5. The exhaustion path restarts from scratch
6. Goto 1

This creates a meta-loop where the system never reaches the "block unfixable tests" termination condition.

### 3.4 Process Monitor Override

**Files:** `process_monitor.py` (377 lines)

The process monitor's "Strategy Reasoner" (Opus) can override configuration defaults. In recipe-mgr-v2, it set `max_fix_attempts` from 3 to 5, extending the fix/service_fix death spiral by 2 additional attempts (each attempt = ~2 iterations due to the oscillation pattern = ~4 extra wasted iterations).

The strategy changes have never demonstrably improved a run outcome across all 16 tests.

### 3.5 VRC Gap Task Conflicts

The VRC (Vision Reality Check) creates "gap tasks" when it detects missing functionality. These tasks compete with code quality tasks, feature tasks, and fix-generated tasks, creating priority conflicts and increasing the pending task count in ways the original plan didn't account for.

### 3.6 Preloop Token Overhead

The preloop phase consistently consumes 150-200k tokens before any work begins:
- Vision validation: ~20k
- Context discovery: ~25k
- PRD critique: ~15k
- 7 quality gates: ~50k total
- Plan generation: ~25k
- Blocker resolution + preflight: ~15k

For a sprint that might complete in 300k total tokens of actual work, this is a 40-60% overhead tax.

---

## 4. Root Cause Analysis

### The Accretive Complexity Trap

Every e2e failure led to a new subsystem:

| Failure | Response | Lines Added | New Failure Modes Created |
|---------|----------|-------------|--------------------------|
| Tests fail blindly | Fix cycle with attempt tracking | ~200 | Fix/service_fix oscillation |
| Loop gets stuck | Course correction + research | ~280 | Research flag reset loop |
| Regressions compound | Snapshot/rollback in fix | ~150 | Rollback state sync bugs |
| Wrong model for job | Process monitor + strategy | ~377 | Override of working defaults |
| Code quality issues | Code quality scanner | ~778 | Cascading task creation |
| No UX evaluation | Critical eval + Playwright | ~206 | Screenshot location bugs |
| Windows incompatibility | Platform detection layer | ~100 | Incomplete pattern coverage |
| Large sprints | Epic decomposition + tagging | ~494 | Stale epic references, scoping bugs |
| Value drift | VRC heartbeat + gap tasks | ~199 | Task conflicts, suppression bugs |
| Structural issues | Coherence eval (7 dimensions) | ~250 | Expensive, rarely actionable |

Each response was locally correct. The refactoring scanner DOES find real issues. The process monitor CAN detect problems. The coherence eval DOES check structural integrity. But the interaction effects between all these subsystems are beyond what either human or AI can reliably predict or test.

### The Fundamental Tension

> The loop needs to be smart enough to recover from its own mistakes, but every recovery mechanism is itself a new source of mistakes.

This is an inherent property of closed-loop autonomous systems in complex domains. More sophisticated error handling leads to more sophisticated errors. The system is in the same trap V2 was:

**V2:** "It retries the same fixes blindly."
**V3:** It retries the same fixes in more sophisticated ways — with research phases, course corrections, process monitors, and strategy reasoners — but the fundamental dynamic is identical.

---

## 5. What Works vs. What Doesn't

### Works Well (Keep)

| Component | Evidence |
|-----------|----------|
| Decision engine (core P0-P9) | Clean, deterministic, correct when inputs are sane |
| Vision + PRD as inputs | Human intent captured well, PRD critique adds value |
| Context discovery (concept) | Self-configuration from codebase is the right idea |
| Separate builder/QC agents | Builder-grades-own-homework problem genuinely solved |
| Git safety net | Branching, per-task commits, checkpoints — proven reliable |
| Basic execute → verify → fix cycle | Early runs prove this works for ~5-15 task sprints |
| Critical evaluation (concept) | Browser-based UX eval is genuinely valuable when it runs |
| Exit gate inside the loop | Correct architecture — gaps become tasks, not dead ends |

### Doesn't Earn Its Keep (Remove)

| Component | Lines | Problem |
|-----------|-------|---------|
| Code quality scanner | 778 | Creates cascading tasks, net negative on run outcomes |
| Process monitor | 377 | Strategy changes have never helped, overrides cause harm |
| Coherence eval | 250 | Expensive, findings never actionable beyond what critical eval catches |
| 7 quality gates | ~1,700 (prompts) | 30+ min preloop tax, rubber-stamp 90% of the time |
| Plan health checks | 75 | Runs mid-loop, has never changed outcome |
| VRC gap tasks | ~50 | Task creation from VRC causes conflicts; VRC should score, not create work |
| Docker integration | ~150 | Never used successfully in any run |

**Total removable: ~2,500 lines of code + ~2,000 lines of prompts (~30% of system)**

### Needs Fixing (If Kept)

| Issue | Fix |
|-------|-----|
| SERVICE_FIX masks stuck state | SERVICE_FIX should not report "progress" — use a neutral result |
| Research flag resets on test changes | Track by verification ID, not by failure set hash |
| Discovery misses tools | Simpler: just check PATH for common tools, don't overthink it |
| Epic task tagging fragile | Explicit epic assignment at plan time, not post-hoc by ID prefix |

---

## 6. Recommendation: Path Forward

### Option A: Radical Pruning (Recommended First Step)

Strip back to the ~5,000-line system that successfully delivered recipe-manager. Remove the subsystems listed above. Run the same test sprints. Measure whether the simplified system delivers reliably.

**Target state:**
```
preloop:  validate vision → discover context → critique PRD → generate plan (ONE quality gate)
loop:     decide → execute → verify → fix → critical eval → exit gate
recovery: course correct, research, interactive pause
```

**Success criteria:** recipe-manager completes in <= 45 iterations, <= 1.2M tokens, 3/3 epics. No manual intervention required.

### Option B: Human-in-the-Loop Pivot (If A Fails)

If the simplified system still fails, the problem is the autonomous loop premise itself. Pivot to:

1. Excellent planning (preloop works well — keep it)
2. Reliable single-task execution with verification
3. **Stop and ask** when anything goes wrong instead of auto-recovering
4. Human as course corrector instead of Opus calls

This would be a ~3,000-line system. It plays to LLM strengths (generating code from clear specs) instead of their weakness (diagnosing and recovering from complex failure states).

### What Not to Do

**Do not add more subsystems.** The evidence is unambiguous: more code has made things worse, not better. The next instinct after reading this report will be "but what if we added a subsystem to detect cascading tasks?" or "what if we added a meta-monitor for the process monitor?" That instinct is the trap.

---

## 7. Key Lessons

1. **Simplicity is a feature, not a starting point.** The early runs succeeded because of the system's simplicity, not despite it.

2. **Accretive fixes have compound costs.** Each subsystem is O(1) to add but O(n) in interaction effects with existing subsystems.

3. **"Progress" must mean actual progress.** Any action that reports "progress" while the system's actual state hasn't improved toward the goal is a lie that poisons the decision engine.

4. **Recovery mechanisms need termination guarantees.** Every auto-recovery path must have a provable upper bound on iterations before it either succeeds or gives up. Infinite loops in recovery are worse than no recovery.

5. **Test the system on the same inputs over time.** We should have been re-running recipe-manager after every major change. The regression would have been caught months ago.

6. **The vision was right about one thing above all:** "The loop delivers value, not just working code." Right now, the loop doesn't reliably deliver either.
