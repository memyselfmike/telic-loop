# Loop V2 - Exact Flow Documentation

**Purpose**: Trace the exact execution path of the loop, every decision point, every branch, every sub-agent call. Use this to identify where things go wrong.

---

## File Map

```
loop-v2/
├── loop.sh                    # Entry point + outer closed loop
├── lib/
│   ├── _init.sh               # Bootstrap (sets LOOP_ROOT)
│   ├── config.sh              # Colors, ports, thresholds, grepcount()
│   ├── state.sh               # LOOP_STATE.md read/write, gate tracking
│   ├── ui.sh                  # Print functions (banners, status, headers)
│   ├── docs.sh                # check_docs_exist()
│   ├── prompts.sh             # run_prompt() - runs claude -p with retry
│   ├── metrics.sh             # verify_blockers(), has_uncomplete_tasks(), count_*()
│   ├── git.sh                 # auto_commit(), ensure_gitignore()
│   ├── branch.sh              # setup_sprint_branch()
│   ├── services.sh            # Legacy npm service startup + service health checks
│   ├── services-v2.sh         # Docker/services.yaml service management
│   └── tests.sh               # Test execution, fix agents, regression checks
├── phases/
│   ├── planning.sh            # VRC, quality gates, test plan generation
│   ├── service-check.sh       # Service readiness verification
│   ├── testing.sh             # Single test iteration + stuck detection
│   └── completion.sh          # Final regression sweep + exit codes
├── prompts/                   # 22 markdown prompt templates (see §Prompts)
└── docs/
    ├── DESIGN.md
    ├── V3_DESIGN.md
    └── V2_FLOW.md             # This file
```

---

## Entry Point: `loop.sh <sprint> [max-iterations]`

```
./loop-v2/loop.sh 2-agentic-core
```

### Bootstrap (lines 30-53)

```
source lib/_init.sh      → sets LOOP_ROOT
source lib/config.sh     → colors, ports, thresholds
source lib/state.sh      → load_state, save_state, gate_passed, mark_gate_passed
source lib/ui.sh         → print_status, print_phase, etc.
source lib/docs.sh       → check_docs_exist
source lib/prompts.sh    → run_prompt (claude -p wrapper)
source lib/metrics.sh    → verify_blockers, count helpers
source lib/git.sh        → auto_commit, ensure_gitignore
source lib/branch.sh     → setup_sprint_branch
source lib/services.sh   → start_required_services (also sources services-v2.sh)
source lib/tests.sh      → test execution, fix agents, regression

source phases/planning.sh
source phases/service-check.sh
source phases/testing.sh
source phases/completion.sh
```

### Argument Parsing (lines 58-72)

```
SPRINT = $1                    # e.g. "2-agentic-core"
MAX_ITERATIONS = $2 or 0       # 0 = unlimited
```

### Sprint Configuration (lines 78-127)

```
SPRINT_DIR = "docs/sprints/$SPRINT"

Files configured:
  VISION_FILE      = $SPRINT_DIR/VISION.md
  PRD_FILE         = $SPRINT_DIR/PRD.md
  ARCH_FILE        = $SPRINT_DIR/ARCHITECTURE.md
  PLAN_FILE        = $SPRINT_DIR/IMPLEMENTATION_PLAN.md
  VALUE_CHECKLIST  = $SPRINT_DIR/VALUE_CHECKLIST.md
  BLOCKERS_FILE    = $SPRINT_DIR/BLOCKERS.md
  STATE_FILE       = $SPRINT_DIR/LOOP_STATE.md
  BETA_TEST_PLAN   = $SPRINT_DIR/BETA_TEST_PLAN_v1.md
  REGRESSION_LOG   = $SPRINT_DIR/REGRESSION_LOG.md

If $SPRINT_DIR/loop-config.sh exists → source it (overrides ports, thresholds, TEST_RUNNER_PREAMBLE)
```

### State Recovery (lines 198-214)

```
load_state() → reads LOOP_STATE.md → sets STATE_PHASE, STATE_ITERATION, STATE_GATES_PASSED
ITERATION = STATE_ITERATION or 0
LOOP_ITERATION = 0
MAX_LOOP_ITERATIONS = 100 (safety)

Stuck detection vars:
  LAST_PROGRESS_HASH = ""
  NO_PROGRESS_COUNT = 0
  MAX_NO_PROGRESS = 3 (or from loop-config)
  IMPL_NO_PROGRESS_COUNT = 0
  MAX_IMPL_NO_PROGRESS = 3
```

---

## Phase 0: Verify Approved Documents (one-time)

```
loop.sh:260-270

IF state phase is "" or "0":
  check_docs_exist()
    → VISION.md exists?    REQUIRED (exit 1 if missing)
    → PRD.md exists?       REQUIRED (exit 1 if missing)
    → ARCHITECTURE.md?     OPTIONAL (warn only)
  save_state("0", iteration)
```

### Branch Setup (one-time)

```
loop.sh:276-279

setup_sprint_branch()
  → IF on protected branch (main/master/develop):
      stash uncommitted changes
  → IF already on loop-v2/{sprint}-* branch:
      use it
  → ELIF existing loop-v2/{sprint}-* branch found:
      switch to it (resume)
  → ELSE:
      create new branch: loop-v2/{sprint}-{YYYYMMDD-HHMMSS}

ensure_gitignore()
  → adds .env, *.pem, *.key, etc. if not present
```

---

## THE CLOSED LOOP (lines 294-658)

```
while true:
    LOOP_ITERATION++

    ┌─────────────────────────────────────────────────────────┐
    │ Safety: LOOP_ITERATION > 100 → exit 1 (infinite loop)  │
    └─────────────────────────────────────────────────────────┘
```

### STEP 1: Start Services

```
loop.sh:317

start_required_services() || true     ◄── FAILURES SWALLOWED

  detect_orchestration()
    → "docker-compose"  → start_docker_compose()
    → "sprint-services" → start_sprint_services() (from services.yaml)
    → "npm"             → legacy: start_backend() + start_frontend()
    → other             → fallback heuristics

  For each service (backend, frontend, browser):
    IF already running (curl health check) → skip
    ELSE try to start:
      nohup [start command] > /tmp/loop-{service}.log 2>&1 &
      wait up to 30s for health check
      IF still not running → diagnose_and_fix_service()
        → check for EADDRINUSE (kill old process, retry)
        → check for MODULE_NOT_FOUND (npm install, retry)
        → check for missing script (create impl task)
        → ELSE spawn fix-service agent (LLM call)
        → max 3 retries per service
```

### STEP 1.5: Verify Blockers

```
loop.sh:327

verify_blockers()
  → IF VALUE_CHECKLIST has any "BLOCKED" items:
      run_prompt("verify-blockers")           ◄── LLM CALL
      compare checklist hash before/after
      IF changed → "some blockers resolved"
```

### STEP 2: Planning (if needed)

```
loop.sh:333-339

needs_planning()?
  → true IF: PLAN_FILE doesn't exist OR "planning" gate not passed

IF needs_planning:
  run_planning_phase()                        (see §Planning Phase below)
  run_preflight_phase()                       (see §Preflight below)
  continue  ←── restart outer loop
```

#### Planning Phase Detail (`phases/planning.sh`)

```
run_planning_phase():

  1. VRC-1 (if gate "vrc1" not passed):
     run_prompt("vrc")                        ◄── LLM CALL
     mark_gate_passed("vrc1")

  2. IF PLAN_FILE doesn't exist OR "planning" gate not passed:

     a. IF no PLAN_FILE:
        run_prompt("plan")                    ◄── LLM CALL → creates IMPLEMENTATION_PLAN.md
        auto_commit()

     b. Blocker validation:
        run_prompt("verify-blockers")         ◄── LLM CALL
        IF BUILD-* tasks created → commit

     c. Quality gates (each with auto-remediation, max 3 retries):
        ┌──────────────────────────────────────────────────────┐
        │ For each gate: CRAAP → CLARITY → VALIDATE → CONNECT → TIDY │
        │                                                      │
        │   IF gate already passed → skip                      │
        │   WHILE retry < 3:                                   │
        │     hash PLAN_FILE + VALUE_CHECKLIST before          │
        │     run_prompt("{gate}")             ◄── LLM CALL    │
        │     hash after                                       │
        │     IF no changes → gate PASSED, break               │
        │     ELSE → "issues found, re-running..."             │
        │   After 3 retries → mark passed anyway (warn)        │
        └──────────────────────────────────────────────────────┘

     d. mark_gate_passed("planning")
        auto_commit()

     e. VRC-2 (if gate "vrc2" not passed):
        Same remediation loop as quality gates:
        run_prompt("vrc")                     ◄── LLM CALL (up to 3x)
        mark_gate_passed("vrc2")
```

#### Preflight Phase

```
run_preflight_phase():
  IF gate "preflight" not passed:
    run_prompt("preflight")                   ◄── LLM CALL
    mark_gate_passed("preflight")
    auto_commit()
```

### STEP 3: Service Readiness Check

```
loop.sh:346-370

IF gate "service_readiness" NOT passed:
  run_service_check_phase()                   (see detail below)

  IF new tasks were created → invalidate_planning() → continue (restart loop)

ELSE (gate already passed):
  run_service_check_phase() to verify services still running
  IF services stopped → invalidate gate → continue (restart loop)
```

#### Service Check Phase Detail (`phases/service-check.sh`)

```
run_service_check_phase():
  SERVICE_CHECK_ATTEMPTS++ (max 3)

  run_service_readiness_check():
    curl backend health  → RUNNING or NOT_RUNNING
    curl frontend        → RUNNING or NOT_RUNNING
    curl browser CDP     → RUNNING or NOT_RUNNING (if vision requires browser)
    → builds SERVICES_NEED_FIX[] array

  IF services need fix:
    Classify as greenfield (no code exists) vs brownfield (code exists, broken)

    For each broken service:
      create_service_startup_task()            → appends SVC-* task to PLAN_FILE

    run_prompt("service-readiness")            ◄── LLM CALL
    auto_commit()

    IF brownfield services:
      run_prompt("implement")                  ◄── LLM CALL (fix startup)
      auto_commit()
      start_required_services() again

  Decision:
    IF all_services_running() → mark gate passed
    ELIF attempts >= 3        → mark passed anyway (proceed with broken services)
    ELSE                      → "will retry" (next outer loop iteration)
```

### STEP 4: Implementation Phase

```
loop.sh:386-490

Count pending tasks:
  pending_build = grep "- [ ] **BUILD-"  in PLAN_FILE
  pending_int   = grep "- [ ] **INT-"    in PLAN_FILE
  pending_task  = grep "- [ ] **Task"    in PLAN_FILE
  total_pending = build + int + task

IF total_pending > 0:

  Identify next task (priority: BUILD > INT > Task):
    next_task = first matching grep

  User-action check:
    IF task context contains "user must|manual|configure.*credentials":
      Mark task as [U] (user-action required)
      continue (restart loop, skip this task)

  run_prompt("implement")                     ◄── LLM CALL (the big one)

  Progress check:
    tasks_before vs tasks_after
    IF completed > 0:
      auto_commit()
      reset IMPL_NO_PROGRESS_COUNT
    ELIF new tasks created:
      reset IMPL_NO_PROGRESS_COUNT
    ELSE (no progress):
      IF same task as last time:
        IMPL_NO_PROGRESS_COUNT++
        IF >= 3:
          Mark task as [B] blocked
          auto_commit()
          "Proceeding to testing phase"
          (fall through, don't continue)
      ELSE:
        IMPL_NO_PROGRESS_COUNT = 1 (new task, reset)

  IF IMPL_NO_PROGRESS_COUNT < 3:
    continue  ←── restart outer loop (keep implementing)

ELSE:
  "All implementation tasks complete" (fall through to testing)
```

### STEP 5: Generate Test Plan

```
loop.sh:498-501

IF BETA_TEST_PLAN doesn't exist OR gate "test_plan_generated" not passed:
  generate_test_plan():
    run_prompt("beta-plan")                   ◄── LLM CALL → creates BETA_TEST_PLAN_v1.md
    Count BT-*, INT-*, VAL-*, UX-* tests
    mark_gate_passed("test_plan_generated")
    auto_commit()
```

### STEP 6: Run Tests (one at a time)

```
loop.sh:509-560

IF has_pending_tests():

  tasks_before = count unchecked in PLAN_FILE

  run_single_test_iteration()                 (see §Test Iteration below)

  tasks_after check:
    IF new tasks created:
      IF significant structural changes (>= 5 SVC/INT/ARCH tasks):
        invalidate_quality_gates()
      IF every 10th iteration:
        run_prompt("vrc")                     ◄── LLM CALL (periodic check)

  Stuck detection:
    compute_progress_hash() = "{passed}-{blocked}-{tasks_done}"
    IF same hash as last iteration:
      NO_PROGRESS_COUNT++
      IF >= MAX_NO_PROGRESS:
        run_value_discovery()                 (see §Value Discovery below)
        continue (restart loop)
    ELSE:
      NO_PROGRESS_COUNT = 0

  continue  ←── restart outer loop (keep testing)
```

#### Single Test Iteration Detail (`phases/testing.sh`)

```
run_single_test_iteration():
  ITERATION++
  IF ITERATION > MAX_ITERATIONS → return 1 (stop)

  progress_before = count (passed + blocked)

  get_next_test():
    grep for "- [ ] **XX-NNN**:" in BETA_TEST_PLAN
    skip tests with attempts >= MAX_TEST_FIX_ATTEMPTS
    IF all pending tests are at max attempts → mark them all [B] blocked

  IF no next test → return 0 (all done)

  Extract: line_num, test_id, test_block (test + next 25 lines)

  ┌─────────────────────────────────────────────────────────────┐
  │ run_single_test(test_id, test_block)      ◄── LLM CALL     │
  │                                                             │
  │ TWO PATHS:                                                  │
  │                                                             │
  │ A) E2E path (test_block contains "*(E2E: "test name")*"):  │
  │    cd $E2E_TEST_DIR && npx playwright test -g "test name"   │
  │    exit 0 → "PASS"                                          │
  │    exit !0 → "FAIL"                                         │
  │                                                             │
  │ B) Standard path (sub-agent):                               │
  │    Build prompt:                                             │
  │      "You are a test runner. Run this ONE test..."           │
  │      + TEST_RUNNER_PREAMBLE (from loop-config.sh)           │
  │      + test_block content                                   │
  │      + blocker classification table                         │
  │                                                             │
  │    timeout 120 claude -p "$prompt"                           │
  │      --allowedTools "Bash,Read,Edit,Write,Glob,Grep"        │
  │      --dangerously-skip-permissions                         │
  │                                                             │
  │    Parse output for keywords:                               │
  │      "RESULT: PASS"             → "PASS"                    │
  │      "RESULT: BLOCKED_EXTERNAL" → "BLOCKED_EXTERNAL"        │
  │      "RESULT: BLOCKED_FIXABLE"  → "BLOCKED_FIXABLE"         │
  │      "RESULT: BLOCKED"          → classify by content       │
  │      anything else / timeout    → "FAIL" or "BLOCKED_FIXABLE│
  │                                                             │
  │    ALL OTHER OUTPUT IS DISCARDED  ◄── KEY PROBLEM           │
  └─────────────────────────────────────────────────────────────┘

  Result handling:

  PASS:
    mark_test_passed(test_id) → sed [x] in BETA_TEST_PLAN
    reset_test_attempts(test_id)
    CONSECUTIVE_BLOCKED = 0
    auto_commit()

  BLOCKED_EXTERNAL:
    attempts = increment_test_attempts(test_id)
    IF attempts < MAX_TEST_FIX_ATTEMPTS:
      Add FEAT-{test_id} task to PLAN_FILE (if not exists)
      run_fix_agent(test_id, test_block)      ◄── LLM CALL (see below)
      Re-test immediately:
        run_single_test(test_id, test_block)  ◄── LLM CALL
        IF PASS → mark passed, commit
    ELSE:
      mark_test_blocked(test_id) → sed [B] in BETA_TEST_PLAN
      CONSECUTIVE_BLOCKED++
      IF >= MAX_CONSECUTIVE_BLOCKED → return 1 (stop testing)

  BLOCKED_FIXABLE:
    attempts = increment_test_attempts(test_id)
    IF attempts >= MAX_TEST_FIX_ATTEMPTS:
      mark_test_blocked(test_id)
    ELSE:
      Add ARCH-{test_id} task to PLAN_FILE
      run_fix_agent(test_id, test_block)      ◄── LLM CALL
      Re-test immediately:
        run_single_test(test_id, test_block)  ◄── LLM CALL
        IF PASS → mark passed, commit, track for regression
        IF BLOCKED_EXTERNAL → mark blocked (reclassified)
        ELSE → "still failing" (will retry next iteration)

  FAIL:
    attempts = increment_test_attempts(test_id)
    IF attempts >= MAX_TEST_FIX_ATTEMPTS:
      mark_test_blocked(test_id)
    ELSE:
      Add FIX-{test_id} task to PLAN_FILE
      run_fix_agent(test_id, test_block)      ◄── LLM CALL
      Re-test immediately:
        run_single_test(test_id, test_block)  ◄── LLM CALL
        IF PASS → mark passed, commit, track for regression
        ELSE → "still failing" (will retry next iteration)

  After result handling:

  Regression check (if FIXES_SINCE_REGRESSION_CHECK >= REGRESSION_CHECK_INTERVAL):
    run_regression_check("interval")          (see §Regression below)

  Spot check (30% chance):
    run_random_spot_check()                   (see §Spot Check below)

  Stuck detection:
    handle_stuck_loop(progress_before)
    IF progress_after == progress_before:
      CONSECUTIVE_NO_PROGRESS++
      IF >= MAX_NO_PROGRESS:
        Force-block the current stuck test
        CONSECUTIVE_NO_PROGRESS = 0
```

#### Fix Agent Detail (`lib/tests.sh:279-328`)

```
run_fix_agent(test_id, test_block):

  Look up related tasks in PLAN_FILE:
    grep for FIX-*, INT-*, ARCH-* near test_id (first 60 lines)

  Build prompt:
    "You are a developer. Implement the fix..."
    + TEST_RUNNER_PREAMBLE
    + test_block
    + related_tasks from PLAN_FILE

  timeout 300 claude -p "$prompt"
    --allowedTools "Bash,Read,Edit,Write,Glob,Grep"
    --dangerously-skip-permissions

  NOTE: Fix agent gets NO error output from the failed test.
  NOTE: Fix agent gets NO history of previous attempts.
  NOTE: Output is not captured or stored.
```

#### Regression Check (`lib/tests.sh:331-399`)

```
run_regression_check(trigger):
  For each test marked [x] in BETA_TEST_PLAN:
    Extract test block
    run_single_test(test_id, test_block)      ◄── LLM CALL (per test!)
    IF still PASS → log "still passing"
    IF not PASS:
      reset_test_to_pending(test_id) → sed back to [ ]
      Create REG-{test_id} task in PLAN_FILE
      regressions++

  Return: 0 if no regressions, 1 if regressions found
```

#### Spot Check (`lib/tests.sh:412-500`)

```
run_random_spot_check():
  Pick SPOT_CHECK_COUNT (default 2) random passing tests
  For each:
    run_single_test(test_id, test_block)      ◄── LLM CALL
    IF not PASS → reset to pending, create REG-* task
```

#### Value Discovery (`loop.sh:225-247`)

```
run_value_discovery():
  run_prompt("verify-blockers")               ◄── LLM CALL
  run_prompt("discover-value")                ◄── LLM CALL
  NO_PROGRESS_COUNT = 0
  invalidate_planning()
```

### STEP 7: All Tests Complete - Blocked Check

```
loop.sh:568-582

IF more blocked than passed tests:
  run_value_discovery()
  IF new pending tests or tasks → continue (restart loop)
```

### STEP 8: Final VRC

```
loop.sh:588-648

run_prompt("vrc")                             ◄── LLM CALL

IF vision NOT delivered:
  IF pending tasks > 0 → continue (restart loop)
  IF blocked tasks > 0:
    IF BUILD-* tasks exist → run_prompt("implement"), continue
    ELSE → break (exit loop, partial success)
  IF no tasks at all:
    run_prompt("discover")                    ◄── LLM CALL
    IF new tasks → invalidate_planning(), continue
    ELSE → break (exit loop, error)

IF vision IS delivered:
  break (exit loop, success!)
```

---

## Post-Loop: Final Verification

```
loop.sh:664-681

run_final_regression_sweep():
  IF passing tests > 0:
    run_regression_check("completion")        ◄── LLM CALL (all tests!)
    IF regressions found:
      IF pending tests → save state, exec $0 (re-run loop!)
  ELSE → "no tests to verify"

run_completion_phase():
  Count: passed, blocked, pending

  IF pending == 0 AND blocked == 0:
    FULL SUCCESS → exit 0, delete STATE_FILE
  ELIF pending == 0:
    PARTIAL SUCCESS → exit 2
  ELSE:
    INCOMPLETE → exit 1
```

---

## Prompt Execution Engine (`lib/prompts.sh`)

Every `run_prompt("name")` call does:

```
1. Load prompt file: loop-v2/prompts/{name}.md
2. Substitute variables: {SPRINT} → sprint name, {SPRINT_DIR} → sprint dir
3. Execute with retry (max 3 attempts, exponential backoff 5s/10s/20s):

   claude -p "$(cat prompt_file)" \
     --allowedTools "Bash,Read,Edit,Write,Glob,Grep" \
     --dangerously-skip-permissions

4. Return exit code (0 = success, 1 = all retries failed)
```

---

## State Machine

```
Gates (tracked in LOOP_STATE.md):

  vrc1 → craap → clarity → validate → connect → tidy → planning → vrc2
    → preflight → service_readiness → test_plan_generated

Gate operations:
  gate_passed("name")        → check if "name," in STATE_GATES_PASSED string
  mark_gate_passed("name")   → append "name," to STATE_GATES_PASSED
  invalidate_gate("name")    → remove "name," from string
  invalidate_quality_gates() → remove craap,clarity,validate,connect,tidy
  invalidate_all_planning()  → remove all planning-related gates
  reset_all_gates()          → clear everything
```

---

## All LLM Calls (in execution order)

Each `◄── LLM CALL` below is a separate `claude -p` invocation (new session, no memory).

| # | Where | Prompt | Purpose | Timeout |
|---|-------|--------|---------|---------|
| 1 | Planning | `vrc` | VRC-1: Is vision clear? | default |
| 2 | Planning | `plan` | Generate IMPLEMENTATION_PLAN.md | default |
| 3 | Planning | `verify-blockers` | Reclassify blockers | default |
| 4-8 | Planning | `craap`, `clarity`, `validate`, `connect`, `tidy` | Quality gates (each up to 3x) | default |
| 9 | Planning | `vrc` | VRC-2: Does plan deliver vision? (up to 3x) | default |
| 10 | Planning | `preflight` | Environment check | default |
| 11 | Service | `service-readiness` | Analyze service issues | default |
| 12 | Service | `implement` | Fix service startup | default |
| 13 | Blocker | `verify-blockers` | Check if blockers resolved | default |
| 14 | Implement | `implement` | Build next task | default |
| 15 | Test gen | `beta-plan` | Generate BETA_TEST_PLAN_v1.md | default |
| 16 | Testing | inline prompt | Test runner (per test) | 120s |
| 17 | Testing | inline prompt | Fix agent (per failed test) | 300s |
| 18 | Testing | inline prompt | Re-test after fix | 120s |
| 19 | Regression | inline prompt | Re-verify each passing test | 120s |
| 20 | Spot check | inline prompt | Random re-verify 1-2 tests | 120s |
| 21 | Stuck | `verify-blockers` + `discover-value` | Value discovery | default |
| 22 | Periodic | `vrc` | Every 10th test iteration | default |
| 23 | Final | `vrc` | Final vision reality check | default |
| 24 | Final | `discover` | Find gaps if vision not delivered | default |
| 25 | Completion | inline prompt | Final regression (all tests) | 120s |

**"default" timeout** = 120s from the `claude -p` process itself (no explicit timeout wrapper).

---

## Key Thresholds & Config

| Variable | Default | Sprint 2 Override | Effect |
|----------|---------|-------------------|--------|
| `MAX_LOOP_ITERATIONS` | 100 | — | Outer loop safety limit |
| `MAX_ITERATIONS` | 0 (unlimited) | — | Test iteration limit |
| `MAX_GATE_RETRIES` | 3 | — | Quality gate remediation loops |
| `MAX_TEST_FIX_ATTEMPTS` | 3 | 5 | Per-test fix attempts before blocking |
| `MAX_NO_PROGRESS` | 3 | 10 | Outer stuck detection threshold |
| `MAX_IMPL_NO_PROGRESS` | 3 | — | Implementation stuck threshold |
| `MAX_CONSECUTIVE_BLOCKED` | 5 | — | Stop testing after N consecutive blocks |
| `MAX_SERVICE_CHECK_ATTEMPTS` | 3 | — | Service fix attempts |
| `MAX_TOTAL_SERVICE_FAILURES` | 10 | — | Total service failures before giving up |
| `REGRESSION_CHECK_INTERVAL` | 5 | — | Run full regression every N fixes |
| `SPOT_CHECK_PROBABILITY` | 30 | — | % chance per iteration |
| `SPOT_CHECK_COUNT` | 2 | — | Random tests to spot check |
| `SIGNIFICANT_TASK_THRESHOLD` | 5 | — | Structural tasks before gate invalidation |
| `LOOP_SERVICE_TIMEOUT` | 60 | — | Seconds to wait for service health |

---

## Data Flow Between Agents

```
┌─────────────┐     (nothing)      ┌─────────────┐
│ Test Runner  │ ────────────────►  │  Fix Agent   │
│ (120s)       │   keyword only:    │  (300s)      │
│              │   PASS/FAIL/       │              │
│ Sees:        │   BLOCKED          │ Sees:        │
│ - test block │                    │ - test block │
│ - preamble   │  Error output,     │ - preamble   │
│              │  stack traces,     │ - related    │
│ Produces:    │  HTTP responses    │   tasks from │
│ - RESULT: X  │  ALL DISCARDED     │   PLAN_FILE  │
│ - EVIDENCE   │                    │              │
│   (discarded)│                    │ Does NOT see:│
│              │                    │ - error output│
│              │                    │ - what test  │
│              │                    │   observed   │
│              │                    │ - prev fixes │
└─────────────┘                    └─────────────┘

Each agent is a fresh claude -p session.
No context is shared between agents.
No error output is propagated.
No attempt history is maintained.
```

---

## Execution Trace: Typical Test Cycle

```
Outer loop iteration 15:
  STEP 1: start_required_services → backend up, frontend up
  STEP 1.5: verify_blockers → no changes
  STEP 2: needs_planning? → NO (gate passed)
  STEP 3: service_readiness gate passed, services still running
  STEP 4: no pending BUILD/INT/Task → skip implementation
  STEP 5: test plan exists, gate passed
  STEP 6: has_pending_tests? → YES (BT-007 pending)

    run_single_test_iteration():
      ITERATION = 16
      next_test = "BT-007"
      test_block = (25 lines from BETA_TEST_PLAN)

      run_single_test("BT-007", block):
        No E2E annotation → standard path
        Spawn: claude -p "Run Single Test: BT-007 ..." (120s timeout)
        Agent reads test, runs curl, gets 401 Unauthorized
        Agent outputs: "RESULT: FAIL\nEVIDENCE: Got 401, expected 200"
        Parse: "FAIL"
        The "EVIDENCE: Got 401" line → DISCARDED

      Result = "FAIL":
        attempts = 1 (first attempt)
        Add FIX-BT-007 to PLAN_FILE
        run_fix_agent("BT-007", block):
          Spawn: claude -p "Fix Failing Test: BT-007 ..." (300s timeout)
          Agent has NO IDEA the error was "401 Unauthorized"
          Agent reads test block, guesses what might be wrong
          Agent makes some change (maybe wrong)

        Re-test: run_single_test("BT-007", block):
          Spawn: claude -p "Run Single Test: BT-007 ..." (120s timeout)
          Still gets 401 → "RESULT: FAIL"
          "still failing after fix (attempt 1/5)"

    No regression check due (FIXES_SINCE_REGRESSION_CHECK < 5)
    Spot check: 30% chance → skip this time
    handle_stuck_loop: progress unchanged → CONSECUTIVE_NO_PROGRESS = 1

  Stuck detection (outer): same hash → NO_PROGRESS_COUNT = 1
  continue → restart loop

  ... this repeats 4 more times, each time a NEW fix agent starts cold ...
  ... attempt 5: mark BT-007 as [B] blocked ...
```

---

## Known Issue Points

### 1. Error evidence discarded (tests.sh:257-275)
The test runner output is scanned for `RESULT: PASS/FAIL/BLOCKED` keywords. All other output (actual errors, HTTP responses, stack traces) is thrown away. The fix agent never sees what went wrong.

### 2. Failures swallowed at service start (loop.sh:317)
`start_required_services() || true` means service startup failures don't prevent testing. Tests then fail predictably because services are down.

### 3. Fix agent has no context (tests.sh:279-328)
The fix agent prompt includes the test block and related tasks from PLAN_FILE, but NOT:
- The actual error output from the test run
- What previous fix attempts changed
- Whether the test timed out vs returned an error

### 4. No failure grouping (testing.sh:57-210)
Each test is processed independently. If 5 tests fail because auth is broken, 5 separate fix agents attempt 5 independent fixes.

### 5. Regression checks are expensive (tests.sh:331-399)
Each regression check re-runs ALL passing tests via LLM sub-agents (120s timeout each). With 15 passing tests, that's potentially 30 minutes of LLM calls just to verify nothing broke.

### 6. Double stuck detection (testing.sh:251-284 + loop.sh:541-556)
Both the testing phase AND the outer loop have independent stuck detection. They can interfere: the inner one force-blocks a test while the outer one triggers value discovery simultaneously.

### 7. State stored as string matching (state.sh:39-42)
`gate_passed()` uses `[[ "$STATE_GATES_PASSED" == *"$gate"* ]]` which means gate "vrc" matches "vrc1" and "vrc2" as well. In practice this hasn't caused issues because "vrc" alone is never used as a gate name, but it's fragile.

### 8. Recursive exec on final regression failure (loop.sh:675)
If the final regression sweep finds issues, the loop `exec`s itself. This loses all in-memory state (TEST_FIX_ATTEMPTS, SERVICE_FIX_ATTEMPTS, etc.) and resets attempt counters.
