# Loop V3 Design: Lessons from Sprint 2

**Date**: 2026-02-13
**Context**: Sprint 2 (agentic-core) implemented reasonably well but failed at testing and required significant manual debugging to deliver working software. This document captures root causes and the design for a loop that delivers truly usable software.

---

## Root Cause Analysis

### Problem 1: Tests are prose, not code

The biggest issue. The beta test plan is markdown prose like *"Navigate to localhost:3000, click Sign in with Google, complete consent screen..."*. Every test "run" spawns a fresh `claude -p` sub-agent that interprets prose and figures out how to test from scratch. This is inherently non-reproducible — the same prose test produces different results on different runs because the LLM decides differently each time.

**Impact**: Tests that should deterministically pass/fail become coin flips. The loop wastes iterations on phantom failures and misses real ones.

### Problem 2: Error evidence is thrown away

In `run_single_test()` (lib/tests.sh), the sub-agent output is parsed for keywords like `RESULT: PASS` and everything else is discarded. Then `run_fix_agent()` gets called with zero knowledge of what actually failed — no stack trace, no error message, no HTTP status code. The fix agent is flying blind.

**Impact**: Fix agents attempt random fixes because they don't know what's actually broken. Multiple attempts often try the same wrong fix independently.

### Problem 3: Each sub-agent starts cold

Every `claude -p` invocation is a brand new session. The fix agent doesn't know:
- What the test agent observed
- What previous fix attempts tried
- What the actual error was
- What files were already investigated

After 5 attempts on the same test, you may have 5 agents each independently trying the same wrong fix.

**Impact**: Fix attempts don't learn from each other. The loop burns through MAX_TEST_FIX_ATTEMPTS with no convergence.

### Problem 4: No hard service gate

`start_required_services || true` swallows failures. Tests run even when the backend is down. If 15 out of 20 tests require `localhost:8000` and it's not responding, the loop burns 15 iterations discovering this one-at-a-time, creating fix tasks for each, when the root cause is a single service being down.

**Impact**: Massive iteration waste. What should be "fix backend, re-run all" becomes 15 separate fix cycles.

### Problem 5: No failure grouping

If auth is broken, every test that requires auth fails independently. The loop creates `FIX-BT-004`, `FIX-BT-005`, `FIX-BT-006`... each with a separate fix agent. None of them know the others exist or that they share a root cause.

**Impact**: Duplicated work, conflicting fixes, wasted context windows.

### Problem 6: The 120-second timeout is insufficient

`timeout 120 claude -p` gives the sub-agent 2 minutes to understand the project, find relevant code, run a test, and report. For anything non-trivial, this is insufficient, leading to timeouts classified as `BLOCKED_FIXABLE`.

**Impact**: Legitimate tests get marked blocked due to timeout, not because they actually fail.

---

## V3 Design

### Principle: Deterministic where possible, LLM only where necessary

V2 uses the LLM for everything: writing tests, running tests, interpreting results, fixing code. V3 should use the LLM only for tasks that require reasoning (writing tests, fixing code) and use deterministic tooling for everything else (running tests, checking health, parsing results).

---

### Change 1: Generate executable test scripts

**Before (v2):** Beta test plan = markdown prose, interpreted by LLM each run.

**After (v3):** The test plan phase generates actual test scripts. LLM writes the tests once, bash/pytest/playwright runs them deterministically.

```
.loop/tests/
  tier0_health/
    test_backend_health.sh     # curl localhost:8000/health → expect 200 + {"status":"ok"}
    test_frontend_loads.sh     # curl localhost:3000 → expect 200 + HTML
    test_postgres.sh           # pg_isready or docker-compose check
    test_redis.sh              # redis-cli ping
  tier1_smoke/
    test_dev_login.sh          # curl POST /auth/dev-login → expect token
    test_auth_me.sh            # curl with JWT → expect user object
    test_create_conversation.sh
  tier2_features/
    test_websocket_chat.py     # websocket connect + message exchange
    test_gmail_tools.py        # tool_call flow with real Google API
    test_calendar_tools.py
  tier3_integration/
    test_memory_recall.py      # multi-conversation memory persistence
    test_email_send_confirm.py # LongRunningFunctionTool confirmation flow
  tier4_e2e/
    app.spec.ts                # existing Playwright tests
```

Each test script:
- Has a shebang and is independently executable
- Exits 0 on pass, non-zero on fail
- Writes structured output to stdout (what was tested, what was expected, what was observed)
- Has a `# TIER: N` and `# REQUIRES: backend,redis` header for dependency tracking

**Test generation prompt** produces actual scripts, not prose. One LLM call per tier, reviewed before execution.

#### Test script template

```bash
#!/bin/bash
# TEST: BT-002 - Health endpoint responds
# TIER: 0
# REQUIRES: backend
# TIMEOUT: 10

set -euo pipefail

RESPONSE=$(curl -sf http://localhost:8000/health 2>&1) || {
    echo "FAIL: Backend health endpoint unreachable"
    echo "EVIDENCE: curl exit code $?"
    exit 1
}

STATUS=$(echo "$RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null) || {
    echo "FAIL: Response is not valid JSON"
    echo "EVIDENCE: $RESPONSE"
    exit 1
}

if [[ "$STATUS" == "ok" ]]; then
    echo "PASS: Health endpoint returned {\"status\": \"ok\"}"
    exit 0
else
    echo "FAIL: Expected status='ok', got status='$STATUS'"
    echo "EVIDENCE: $RESPONSE"
    exit 1
fi
```

---

### Change 2: Capture and propagate error context

When a test fails, capture the full output and build cumulative context:

```bash
# Run test, capture everything
output=$(bash "$test_script" 2>&1)
exit_code=$?

if [[ $exit_code -ne 0 ]]; then
    # Store failure evidence
    mkdir -p .loop/failures
    {
        echo "## Failure at $(date -Iseconds)"
        echo "Test: $test_id"
        echo "Script: $test_script"
        echo "Exit code: $exit_code"
        echo ""
        echo "### Output"
        echo '```'
        echo "$output"
        echo '```'
    } > ".loop/failures/${test_id}_latest.log"

    # Append to cumulative attempt history
    {
        echo ""
        echo "---"
        echo "## Attempt $attempt_num ($(date -Iseconds))"
        echo "### Test Output"
        echo '```'
        echo "$output"
        echo '```'
    } >> ".loop/failures/${test_id}_history.md"
fi
```

The fix agent prompt then includes:

```markdown
## Current Error
$(cat .loop/failures/${test_id}_latest.log)

## Previous Attempts (if any)
$(cat .loop/failures/${test_id}_history.md)

## Rules
- Read the FULL error output before making changes
- Do NOT repeat a fix that was already attempted (see history above)
- After applying your fix, explain what you changed and why
```

After the fix agent runs, append its actions to the history:

```markdown
### Fix Applied (Attempt $attempt_num)
$fix_agent_output_summary
```

This creates a debugging narrative that accumulates knowledge across attempts.

---

### Change 3: Hard service gates with health probes

Before ANY testing, run a blocking service readiness check. No LLM involved — just curl and exit codes.

```bash
# HARD GATE - no testing proceeds until ALL required services respond
check_services() {
    local all_healthy=true

    for service in "${REQUIRED_SERVICES[@]}"; do
        local url="${SERVICE_HEALTH_URLS[$service]}"
        local max_wait=30

        if ! wait_for_service "$url" "$max_wait"; then
            echo "BLOCKED: $service not healthy at $url after ${max_wait}s"
            all_healthy=false
        fi
    done

    $all_healthy
}

wait_for_service() {
    local url=$1 max_wait=$2
    for i in $(seq 1 "$max_wait"); do
        if curl -sf "$url" > /dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

# In the main loop:
if ! check_services; then
    run_service_fix_agent  # ONE agent to fix ALL unhealthy services
    continue               # Re-check before testing
fi
```

Services are defined in `loop-config.sh`:

```bash
REQUIRED_SERVICES=(backend frontend postgres redis)
declare -A SERVICE_HEALTH_URLS=(
    [backend]="http://localhost:8000/health"
    [frontend]="http://localhost:3000"
    [postgres]="localhost:5432"  # use pg_isready
    [redis]="localhost:6379"     # use redis-cli ping
)
```

---

### Change 4: Failure triage before fixing

When tests fail, don't immediately create per-test fix tasks. First, triage to find root causes.

```
Phase: TRIAGE
├── Run ALL tests for current tier (fast, parallel where possible)
├── Collect all failures
├── Group by root cause signal:
│   ├── "5 tests failed: all curl to :8000 got connection refused"
│   │   → ROOT CAUSE: backend not running
│   ├── "3 tests failed: all return HTTP 401"
│   │   → ROOT CAUSE: auth broken
│   ├── "2 tests failed: websocket connection reset"
│   │   → ROOT CAUSE: websocket handler issue
│   └── "1 test failed: wrong response body"
│   │   → ISOLATED BUG: specific endpoint logic
├── Fix root causes first (one fix unblocks many tests)
├── Re-run ALL tests in tier after each root-cause fix
└── Then fix isolated bugs
```

Implementation: after running a tier, if multiple tests fail, pass ALL failure logs to a single triage agent:

```markdown
# Triage: Tier 1 Failures

## Failed Tests
### test_dev_login.sh
$(cat .loop/failures/BT-003_latest.log)

### test_auth_me.sh
$(cat .loop/failures/BT-005_latest.log)

### test_create_conversation.sh
$(cat .loop/failures/BT-007_latest.log)

## Task
1. Identify shared root causes across these failures
2. Group tests by root cause
3. Output a prioritized fix list (fix the root cause that unblocks the most tests first)

Output format:
ROOT_CAUSE_1: [description]
AFFECTED_TESTS: BT-003, BT-005, BT-007
FIX: [what to change]

ROOT_CAUSE_2: [description]
...
```

---

### Change 5: Tiered testing strategy

Run tests in tiers. Each tier gates the next — no point running integration tests if basic API calls return 500.

```
Tier 0: Service Health (5 sec, deterministic)
  - curl health endpoints, check docker containers
  - HARD GATE: must all pass

Tier 1: Smoke Tests (30 sec, deterministic)
  - Basic API calls: dev-login, auth/me, create conversation
  - Basic page loads: frontend renders HTML
  - HARD GATE: must all pass (these are prerequisites for everything else)

Tier 2: Feature Tests (2 min, mostly deterministic)
  - API functionality: CRUD operations, WebSocket chat
  - Tool execution: agent tool calls work
  - SOFT GATE: triage failures, fix, re-run tier 1+2

Tier 3: Integration Tests (5 min, may need real credentials)
  - Multi-service flows: Gmail send, Calendar create
  - Memory persistence across conversations
  - SOFT GATE: triage failures, fix, re-run tier 2+3

Tier 4: E2E Tests (5 min, Playwright)
  - Full browser-based user flows
  - Existing app.spec.ts tests
  - SOFT GATE: triage failures, fix, re-run tier 3+4
```

The outer loop becomes:

```bash
for tier in 0 1 2 3 4; do
    while true; do
        failures=$(run_tier "$tier")
        if [[ ${#failures[@]} -eq 0 ]]; then
            break  # Tier passed, move to next
        fi

        triage_and_fix "$tier" "${failures[@]}"

        # Re-run prerequisite tiers to catch regressions
        if [[ $tier -gt 1 ]]; then
            rerun_tier $((tier - 1))
        fi

        ((attempts++))
        if [[ $attempts -ge $max_tier_attempts ]]; then
            mark_tier_blocked "$tier"
            break
        fi
    done
done
```

---

### Change 6: Tight inner fix loop

Instead of going through the expensive outer loop (re-check services, re-plan, re-enter testing phase) for each test fix, use a tight inner loop:

```bash
fix_test() {
    local test_id=$1 test_script=$2 max_attempts=5

    for attempt in $(seq 1 $max_attempts); do
        # Run test
        output=$(bash "$test_script" 2>&1)
        if [[ $? -eq 0 ]]; then
            echo "PASS after $attempt attempt(s)"
            return 0
        fi

        # Record failure
        record_failure "$test_id" "$attempt" "$output"

        # Run fix agent with full context
        run_fix_agent "$test_id" \
            --error-log ".loop/failures/${test_id}_latest.log" \
            --history ".loop/failures/${test_id}_history.md" \
            --attempt "$attempt"

        # Record what was fixed
        record_fix "$test_id" "$attempt"

        # Immediate re-test (next iteration of this loop)
    done

    echo "BLOCKED after $max_attempts attempts"
    return 1
}
```

This is dramatically faster than the v2 approach where each fix attempt goes through the full outer loop.

---

### Change 7: Fix agent gets structured context

The fix agent prompt should be structured, not freeform:

```markdown
# Fix Test: ${test_id}

## Test Script
$(cat $test_script)

## Current Failure (attempt ${attempt}/${max_attempts})
$(cat .loop/failures/${test_id}_latest.log)

## Attempt History
$(cat .loop/failures/${test_id}_history.md)

## Project Structure
Backend: backend/app/ (FastAPI, Python 3.14)
Frontend: frontend/src/ (Next.js 16, React 19)
Agent: backend/app/agent/ (Google ADK)

## Instructions
1. Read the test script to understand what's being verified
2. Read the error output to understand what went wrong
3. Check the attempt history — do NOT repeat a previously failed fix
4. Find the source code responsible for the failure
5. Apply the minimal fix
6. Explain what you changed and why

## Output Format
FIX_APPLIED: [one-line description]
FILES_CHANGED: [list of files]
REASONING: [why this should fix the error]
```

---

### Change 8: Snapshot-based regression detection

Instead of re-running all tests via LLM sub-agents (expensive), use the deterministic test scripts:

```bash
run_regression_check() {
    local tier=$1
    local results_file=".loop/regression_$(date +%s).log"

    # Run all test scripts for this tier (fast, no LLM)
    for script in .loop/tests/tier${tier}_*/*.sh; do
        test_id=$(basename "$script" .sh)
        if output=$(timeout 30 bash "$script" 2>&1); then
            echo "PASS $test_id" >> "$results_file"
        else
            echo "FAIL $test_id" >> "$results_file"
            echo "$output" >> ".loop/failures/${test_id}_latest.log"
        fi
    done

    # Compare with last known good
    diff ".loop/last_green.log" "$results_file" || {
        echo "REGRESSIONS DETECTED"
        return 1
    }
}
```

Running 20 bash scripts with curl takes seconds, not the 20+ minutes of spawning 20 LLM sub-agents.

---

### Change 9: Use real test frameworks

Where the project already has test infrastructure, use it:

**Backend (pytest)**:
```bash
# Generate pytest tests during test plan phase
# Run with structured output
cd backend && uv run pytest tests/ -x --tb=short -q 2>&1
```

**Frontend (Playwright)**:
```bash
# Already in place for E2E
cd frontend && npx playwright test --reporter=json 2>&1
```

**API tests (custom scripts)**:
```bash
# For tests that don't fit into pytest/playwright
bash .loop/tests/tier1_smoke/test_dev_login.sh
```

Parse structured output (pytest JSON, Playwright JSON reporter) for exact failure locations and assertion messages.

---

### Change 10: Pre-flight validation before testing

Before generating or running ANY tests, validate the environment deterministically:

```bash
preflight_check() {
    local errors=0

    # Check required env vars
    for var in DATABASE_URL REDIS_URL GEMINI_API_KEY SECRET_KEY; do
        if [[ -z "${!var:-}" ]]; then
            echo "MISSING: $var"
            ((errors++))
        fi
    done

    # Check required files
    for file in backend/app/main.py frontend/package.json; do
        if [[ ! -f "$file" ]]; then
            echo "MISSING FILE: $file"
            ((errors++))
        fi
    done

    # Check required ports are available (or services are running)
    for port in 8000 3000 5432 6379; do
        if ! check_port "$port"; then
            echo "PORT NOT LISTENING: $port"
            ((errors++))
        fi
    done

    return $errors
}
```

This catches environment issues in seconds, before burning 30 minutes of LLM calls.

---

## Migration Path: V2 → V3

V3 doesn't require a full rewrite. The changes can be layered incrementally:

### Phase 1: Quick wins (keep v2 structure)
1. Add hard service health gate (bash-only, no LLM) before testing phase
2. Capture and propagate error output between test→fix agents
3. Add attempt history file per test
4. Increase sub-agent timeout to 300s

### Phase 2: Test generation (replace prose with scripts)
5. New prompt: `generate-test-scripts.md` — produces executable .sh/.py files
6. New test runner: `run_tier.sh` — executes scripts, collects results
7. Replace `run_single_test` sub-agent with direct script execution
8. Keep `run_fix_agent` but feed it actual error output

### Phase 3: Triage and tiering
9. Implement tiered test execution
10. Add failure triage agent (groups failures by root cause)
11. Tight inner fix loop per test
12. Deterministic regression checks (re-run scripts, not sub-agents)

### Phase 4: Framework integration
13. Generate pytest tests for backend API
14. Generate Playwright tests for frontend flows
15. Parse structured test output (JSON reporters)
16. Remove all prose-based test interpretation

---

## Key Metrics to Track

To measure if V3 is actually better than V2:

| Metric | V2 (Sprint 2) | V3 Target |
|--------|---------------|-----------|
| Iterations to first passing test | ~10 | 1-2 |
| LLM calls per test run | 1 (sub-agent) | 0 (script) |
| Time to detect "backend is down" | ~15 iterations | 5 seconds |
| Fix agent success rate | ~20% (blind) | ~60% (with error context) |
| Regression check time | 20+ min (LLM) | 30 sec (scripts) |
| Manual debugging after loop | Hours | Minutes (ideally zero) |
| Total loop time for sprint | Unbounded | Bounded by tier structure |

---

## Anti-Patterns to Avoid

### Don't: Use LLM to check deterministic things
If the answer is "does curl return 200", use curl, not an LLM.

### Don't: Spawn fresh agents for related problems
If 5 tests fail for the same reason, that's 1 fix, not 5 agents.

### Don't: Discard error output
The actual error message is the most valuable signal. Always capture and propagate it.

### Don't: Test without services
Running tests against a dead backend wastes everyone's time. Gate on health first.

### Don't: Retry without learning
If attempt 1 failed with error X, attempt 2 must know about error X and try something different.

### Don't: Mix test generation and test execution
LLM writes tests (once). Scripts run tests (many times). These are separate concerns.
