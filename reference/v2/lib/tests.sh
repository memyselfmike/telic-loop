#!/bin/bash
# Loop V2 Test Utilities - Test parsing, execution, and regression checking
#
# Dependencies: lib/ui.sh, lib/prompts.sh
# Requires: BETA_TEST_PLAN, PLAN_FILE, REGRESSION_LOG, SPRINT, SPRINT_DIR
# Uses: REGRESSION_CHECK_INTERVAL, SPOT_CHECK_PROBABILITY, SPOT_CHECK_COUNT from config.sh

# Track fixes for regression check timing
FIXES_SINCE_REGRESSION_CHECK=0

# Track significant changes that might require gate re-verification
# Significant = new SVC-*, INT-*, ARCH-* tasks (not just REG-* or FIX-*)
SIGNIFICANT_TASKS_ADDED=0
SIGNIFICANT_TASK_THRESHOLD=${SIGNIFICANT_TASK_THRESHOLD:-5}

# Track test fix attempts to prevent infinite loops on the same test
declare -A TEST_FIX_ATTEMPTS
MAX_TEST_FIX_ATTEMPTS=${MAX_TEST_FIX_ATTEMPTS:-3}

# Check if significant structural tasks were added (not just fixes)
check_for_significant_changes() {
    local tasks_before="$1"
    local tasks_after="$2"

    if [[ "$tasks_after" -gt "$tasks_before" ]]; then
        local new_tasks=$((tasks_after - tasks_before))

        # Check if any are significant (SVC, INT, ARCH, etc.)
        local significant
        significant=$(grep -cE "^- \[ \] \*\*(SVC|INT|ARCH|PREP)-" "$PLAN_FILE" 2>/dev/null) || significant=0

        if [[ "$significant" -gt "$SIGNIFICANT_TASKS_ADDED" ]]; then
            local new_significant=$((significant - SIGNIFICANT_TASKS_ADDED))
            SIGNIFICANT_TASKS_ADDED="$significant"

            if [[ "$SIGNIFICANT_TASKS_ADDED" -ge "$SIGNIFICANT_TASK_THRESHOLD" ]]; then
                print_status "warn" "Significant structural changes detected ($SIGNIFICANT_TASKS_ADDED tasks)"
                print_status "info" "Quality gates may need re-verification"
                return 0  # Signal that gates should be re-checked
            fi
        fi
    fi
    return 1  # No significant change
}

# Get next unchecked test from BETA_TEST_PLAN
# Skips tests that have exceeded max fix attempts
get_next_test() {
    local all_pending
    all_pending=$(grep -n "^- \[ \] \*\*[A-Z]*-[0-9]*\*\*:" "$BETA_TEST_PLAN" 2>/dev/null)

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        local test_id=$(echo "$line" | sed -n 's/.*\*\*\([A-Z]*-[0-9]*\)\*\*.*/\1/p')

        # Skip tests with too many failed fix attempts
        if should_skip_test "$test_id"; then
            continue
        fi

        echo "$line"
        return 0
    done <<< "$all_pending"

    # If we get here, check if ALL tests are skipped (stuck)
    local total_pending=$(echo "$all_pending" | grepcount .)
    if [[ "$total_pending" -gt 0 ]]; then
        print_status "warn" "All pending tests have exceeded max fix attempts ($MAX_TEST_FIX_ATTEMPTS)"
        print_status "info" "Marking stuck tests as blocked to allow loop to proceed"

        # Mark all stuck tests as blocked
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            local test_id=$(echo "$line" | sed -n 's/.*\*\*\([A-Z]*-[0-9]*\)\*\*.*/\1/p')
            if should_skip_test "$test_id"; then
                mark_test_blocked "$test_id"
                print_status "warn" "Marked $test_id as blocked (exceeded $MAX_TEST_FIX_ATTEMPTS fix attempts)"
            fi
        done <<< "$all_pending"
    fi

    # Return empty (no more tests)
    echo ""
}

# Extract test ID from line
get_test_id() {
    echo "$1" | sed -n 's/.*\*\*\([A-Z]*-[0-9]*\)\*\*.*/\1/p'
}

# Count test status
count_beta_tests() {
    local passed=$(grepcount "^- \[x\] \*\*" "$BETA_TEST_PLAN")
    local blocked=$(grepcount "^- \[B\] \*\*" "$BETA_TEST_PLAN")
    local pending=$(grepcount "^- \[ \] \*\*" "$BETA_TEST_PLAN")
    echo "$passed passed, $blocked blocked, $pending pending"
}

# Mark test passed
mark_test_passed() {
    local test_id="$1"
    sed -i "s/^- \[ \] \*\*${test_id}\*\*/- [x] **${test_id}**/" "$BETA_TEST_PLAN"
}

# Mark test blocked
mark_test_blocked() {
    local test_id="$1"
    sed -i "s/^- \[ \] \*\*${test_id}\*\*/- [B] **${test_id}**/" "$BETA_TEST_PLAN"
}

# Track and check test fix attempts
increment_test_attempts() {
    local test_id="$1"
    local current=${TEST_FIX_ATTEMPTS[$test_id]:-0}
    ((current++))
    TEST_FIX_ATTEMPTS[$test_id]=$current
    echo $current
}

get_test_attempts() {
    local test_id="$1"
    echo ${TEST_FIX_ATTEMPTS[$test_id]:-0}
}

reset_test_attempts() {
    local test_id="$1"
    TEST_FIX_ATTEMPTS[$test_id]=0
}

# Check if we should skip this test (too many failed fix attempts)
should_skip_test() {
    local test_id="$1"
    local attempts=$(get_test_attempts "$test_id")
    [[ $attempts -ge $MAX_TEST_FIX_ATTEMPTS ]]
}

# Reset test to pending (for regression detection)
reset_test_to_pending() {
    local test_id="$1"
    sed -i "s/^- \[x\] \*\*${test_id}\*\*/- [ ] **${test_id}**/" "$BETA_TEST_PLAN"
    print_status "warn" "Reset $test_id to pending (regression detected)"
}

# Get all passing tests
get_passing_tests() {
    grep -o "\*\*[A-Z]*-[0-9]*\*\*" "$BETA_TEST_PLAN" | while read test_marker; do
        local test_id=$(echo "$test_marker" | tr -d '*')
        if grep -q "^- \[x\] \*\*${test_id}\*\*" "$BETA_TEST_PLAN" 2>/dev/null; then
            echo "$test_id"
        fi
    done
}

# Extract test block (test definition + steps + expected)
extract_test_block() {
    local line_num="$1"
    local end_line=$((line_num + 25))
    sed -n "${line_num},${end_line}p" "$BETA_TEST_PLAN" | awk '/^- \[/ {if(NR>1) exit} /^###/ {exit} /^---/ {exit} {print}'
}

# Run a single test via sub-agent
run_single_test() {
    local test_id="$1"
    local test_block="$2"

    print_status "info" "Running test: $test_id"

    # ── E2E PATH: Run the actual Playwright test ────────────────────
    # Tests annotated with *(E2E: "test name")* have a corresponding
    # Playwright test. Instead of spawning a claude -p sub-agent (which
    # can't use a browser), run the Playwright test directly.
    # E2E_TEST_DIR is set in sprint loop-config.sh.
    #
    # Detect E2E annotation: *(E2E: "test name")* or *(E2E: "name1" + "name2")*
    local e2e_test_name=""
    if echo "$test_block" | grep -q '\*(E2E:' 2>/dev/null; then
        e2e_test_name=$(echo "$test_block" | grep '\*(E2E:' | sed -n 's/.*\*(E2E: "\([^"]*\)".*/\1/p' | head -1) || true
    fi

    if [[ -n "$e2e_test_name" ]] && [[ -n "${E2E_TEST_DIR:-}" ]]; then
        print_status "info" "$test_id running Playwright: \"$e2e_test_name\""

        local pw_output
        if pw_output=$(cd "$E2E_TEST_DIR" && npx playwright test -g "$e2e_test_name" --reporter=line 2>&1); then
            print_status "ok" "$test_id Playwright PASSED: \"$e2e_test_name\""
            echo "PASS"
            return 0
        else
            print_status "warn" "$test_id Playwright FAILED: \"$e2e_test_name\""
            # Show last few lines of output for debugging
            echo "$pw_output" | tail -10 >&2
            echo "FAIL"
            return 0
        fi
    fi

    # ── STANDARD PATH: Sub-agent verification ─────────────────────
    # Create minimal prompt for this ONE test with blocker classification
    # TEST_RUNNER_PREAMBLE can be set in sprint loop-config.sh to provide
    # project-specific guidance on how to verify tests (e.g., API endpoints,
    # CLI commands to use instead of browser actions)
    local preamble="${TEST_RUNNER_PREAMBLE:-}"

    local prompt="# Run Single Test: $test_id

You are a test runner. Run this ONE test and report PASS, FAIL, or BLOCKED.

${preamble:+## Project Context
$preamble

}## Test Case
$test_block

## Instructions

1. Read the test case above
2. Execute the Check command if provided
3. Verify the Expected result
4. Report result in this EXACT format:

\`\`\`
RESULT: [PASS|FAIL|BLOCKED]
EVIDENCE: [What you observed]
ACTION: [If FAIL/BLOCKED, what needs to happen]
\`\`\`

## Rules
- Do NOT implement fixes - just report the result
- If a dependency is missing (API key, service down), report BLOCKED
- If the check fails, report FAIL
- Be concise - this is context-limited

## CRITICAL: Blocker Classification

If you report BLOCKED, you MUST classify WHY:

**Step 1: Is the FEATURE that enables user action implemented?**

| If blocked because... | Feature Exists? | Report as |
|-----------------------|-----------------|-----------|
| Needs login/auth | NO - no login code | RESULT: BLOCKED_FIXABLE |
| Needs login/auth | YES - login exists | RESULT: BLOCKED_EXTERNAL |
| Needs OAuth | NO - no OAuth code | RESULT: BLOCKED_FIXABLE |
| Needs OAuth | YES - OAuth exists | RESULT: BLOCKED_EXTERNAL |
| Missing third-party API key | N/A - always external | RESULT: BLOCKED_EXTERNAL |
| Service not running | N/A - always fixable | RESULT: BLOCKED_FIXABLE |
| Missing code/route/wiring | N/A - always fixable | RESULT: FAIL (not blocked) |

**Key insight**: If the app doesn't have the feature yet, implementing it is the fix.
Only mark EXTERNAL if the feature EXISTS but needs human action.

Run the test now."

    # Run sub-agent with timeout (--allowedTools enables tool access in -p mode)
    local output
    if output=$(timeout 120 claude -p "$prompt" --allowedTools "Bash,Read,Edit,Write,Glob,Grep" --dangerously-skip-permissions 2>&1); then
        if echo "$output" | grep -q "RESULT: PASS"; then
            echo "PASS"
        elif echo "$output" | grep -q "RESULT: BLOCKED_EXTERNAL"; then
            echo "BLOCKED_EXTERNAL"
        elif echo "$output" | grep -q "RESULT: BLOCKED_FIXABLE"; then
            echo "BLOCKED_FIXABLE"
        elif echo "$output" | grep -q "RESULT: BLOCKED"; then
            # Legacy format - try to classify based on content
            if echo "$output" | grep -qiE "api.key|credential|oauth|token|login|auth"; then
                echo "BLOCKED_EXTERNAL"
            else
                echo "BLOCKED_FIXABLE"
            fi
        else
            echo "FAIL"
        fi
    else
        echo "BLOCKED_FIXABLE"  # Timeout likely means service issue, not credential
    fi
}

# Run developer fix agent
run_fix_agent() {
    local test_id="$1"
    local test_block="$2"

    print_status "info" "Spawning developer to fix $test_id..."

    # Look for related tasks in the implementation plan
    local related_tasks=""
    if [[ -f "$PLAN_FILE" ]]; then
        # Search for tasks mentioning this test_id or related patterns
        related_tasks=$(grep -A20 "^\- \[ \] \*\*.*$test_id\|INT-\|ARCH-\|FIX-" "$PLAN_FILE" 2>/dev/null | head -60)
    fi

    local preamble="${TEST_RUNNER_PREAMBLE:-}"

    local prompt="# Fix Failing Test: $test_id

You are a developer. Implement the fix to make this test pass.

${preamble:+## Project Context
$preamble

}## Failed Test
$test_block

## Related Tasks from Implementation Plan
Check if any of these tasks provide fix instructions:

$related_tasks

## Process

1. **Read the test** - understand what's being tested
2. **Check related tasks** - if there's an INT-* or FIX-* task with instructions, follow them
3. **Find the file** - locate the source file that needs fixing
4. **Implement the fix** - write actual code, not stubs
5. **Verify** - ensure the change makes sense

## Rules

- **WRITE CODE** - Use Edit/Write tools to actually make changes
- **NO STUBS** - Implement real functionality
- **MINIMAL CHANGES** - Only change what's needed to fix the issue
- **CHECK PLAN FIRST** - If an INT-* task has specific instructions, follow them exactly

If blocked by missing CREDENTIALS (API keys, secrets), output: BLOCKED: [reason]
Otherwise, implement the fix."

    timeout 300 claude -p "$prompt" --allowedTools "Bash,Read,Edit,Write,Glob,Grep" --dangerously-skip-permissions 2>&1
}

# Run regression check on all passing tests
run_regression_check() {
    local trigger="$1"  # "interval", "completion", or "manual"

    print_regression_header "$trigger"

    local passing_tests=$(get_passing_tests)
    local total_passing
    total_passing=$(echo "$passing_tests" | grep -c . 2>/dev/null) || total_passing=0
    local regressions=0
    local regressed_tests=""

    if [[ "$total_passing" -eq 0 ]]; then
        print_status "info" "No passing tests to verify"
        return 0
    fi

    print_status "info" "Re-verifying $total_passing previously passing tests..."

    # Log regression check start
    echo "" >> "$REGRESSION_LOG"
    echo "## Regression Check - $(date -Iseconds)" >> "$REGRESSION_LOG"
    echo "Trigger: $trigger" >> "$REGRESSION_LOG"
    echo "Tests to verify: $total_passing" >> "$REGRESSION_LOG"
    echo "" >> "$REGRESSION_LOG"

    for test_id in $passing_tests; do
        # Get test block for this test
        local test_line=$(grep -n "^- \[x\] \*\*${test_id}\*\*" "$BETA_TEST_PLAN" 2>/dev/null | head -1)
        if [[ -z "$test_line" ]]; then
            continue
        fi

        local line_num=$(echo "$test_line" | cut -d: -f1)
        local test_block=$(extract_test_block "$line_num")

        # Run the test
        local result=$(run_single_test "$test_id" "$test_block")

        if [[ "$result" == "PASS" ]]; then
            echo -e "  ${GREEN}✓${NC} $test_id still passes"
            echo "- [x] $test_id: STILL_PASSING" >> "$REGRESSION_LOG"
        else
            echo -e "  ${RED}✗${NC} $test_id REGRESSION - was passing, now $result"
            ((regressions++))
            regressed_tests="$regressed_tests $test_id"
            echo "- [ ] $test_id: **REGRESSION** (was PASS, now $result)" >> "$REGRESSION_LOG"

            # Reset to pending
            reset_test_to_pending "$test_id"

            # Create regression fix task
            echo "" >> "$PLAN_FILE"
            echo "- [ ] **REG-$test_id**: Fix regression in $test_id" >> "$PLAN_FILE"
            echo "  - **Issue**: Test was passing, now failing after recent changes" >> "$PLAN_FILE"
            echo "  - **Priority**: CRITICAL - must fix before completion" >> "$PLAN_FILE"
        fi
    done

    echo ""
    echo "Regressions found: $regressions" >> "$REGRESSION_LOG"

    if [[ "$regressions" -gt 0 ]]; then
        print_regression_failure "$regressions" "$regressed_tests"
        return 1  # Indicate regressions found
    else
        print_status "ok" "All $total_passing tests still passing - no regressions"
        return 0
    fi
}

# Check if regression check is due
should_run_regression_check() {
    [[ $FIXES_SINCE_REGRESSION_CHECK -ge $REGRESSION_CHECK_INTERVAL ]]
}

# Random spot check - adds unpredictability to regression detection
should_run_spot_check() {
    local random=$((RANDOM % 100))
    [[ $random -lt $SPOT_CHECK_PROBABILITY ]]
}

run_random_spot_check() {
    local passing_tests=$(get_passing_tests)
    local total_passing=$(echo "$passing_tests" | grepcount .)

    if [[ "$total_passing" -eq 0 ]]; then
        return 0  # No tests to spot check
    fi

    print_spot_check_header "$SPOT_CHECK_COUNT"

    # Convert to array and shuffle
    local tests_array=($passing_tests)
    local num_tests=${#tests_array[@]}

    # Pick random tests to check (up to SPOT_CHECK_COUNT)
    local check_count=$SPOT_CHECK_COUNT
    if [[ $num_tests -lt $check_count ]]; then
        check_count=$num_tests
    fi

    local regressions=0
    local checked=0

    # Use a simple shuffle by picking random indices
    local checked_indices=()
    while [[ $checked -lt $check_count ]]; do
        local rand_idx=$((RANDOM % num_tests))

        # Skip if already checked this index
        local already_checked=false
        for idx in "${checked_indices[@]}"; do
            if [[ $idx -eq $rand_idx ]]; then
                already_checked=true
                break
            fi
        done
        if $already_checked; then
            continue
        fi

        checked_indices+=($rand_idx)
        local test_id="${tests_array[$rand_idx]}"
        ((checked++))

        # Get test block
        local test_line=$(grep -n "^- \[x\] \*\*${test_id}\*\*" "$BETA_TEST_PLAN" 2>/dev/null | head -1)
        if [[ -z "$test_line" ]]; then
            continue
        fi

        local line_num=$(echo "$test_line" | cut -d: -f1)
        local test_block=$(extract_test_block "$line_num")

        print_status "info" "Spot checking: $test_id"

        # Run the test
        local result=$(run_single_test "$test_id" "$test_block")

        if [[ "$result" == "PASS" ]]; then
            echo -e "  ${GREEN}✓${NC} $test_id still passes"
        else
            echo -e "  ${RED}✗${NC} $test_id REGRESSION detected!"
            ((regressions++))

            # Reset to pending
            reset_test_to_pending "$test_id"

            # Log it
            echo "" >> "$REGRESSION_LOG"
            echo "## Spot Check Regression - $(date -Iseconds)" >> "$REGRESSION_LOG"
            echo "- [ ] $test_id: **REGRESSION** (spot check found failure)" >> "$REGRESSION_LOG"

            # Create regression fix task
            echo "" >> "$PLAN_FILE"
            echo "- [ ] **REG-$test_id**: Fix regression in $test_id (found by spot check)" >> "$PLAN_FILE"
            echo "  - **Issue**: Test was passing, spot check found it failing" >> "$PLAN_FILE"
            echo "  - **Priority**: CRITICAL - must fix before completion" >> "$PLAN_FILE"
        fi
    done

    echo ""
    if [[ $regressions -gt 0 ]]; then
        print_status "warn" "Spot check found $regressions regression(s) - tests reset to pending"
        return 1
    else
        print_status "ok" "Spot check passed - $checked tests verified"
        return 0
    fi
}
