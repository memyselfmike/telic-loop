#!/bin/bash
# Loop V2 Testing Phase - Main test loop
#
# Dependencies: lib/tests.sh, lib/state.sh, lib/ui.sh, lib/prompts.sh, lib/git.sh
# Requires: BETA_TEST_PLAN, ITERATION, MAX_ITERATIONS, MAX_CONSECUTIVE_BLOCKED
#
# DESIGN PRINCIPLE: Progress or stop - never spin forever.
# If we can't make progress after MAX attempts, mark blocked and move on.

# Track consecutive blocked tests (global for persistence across calls)
CONSECUTIVE_BLOCKED=0

# Track consecutive no-progress iterations to detect stuck loops
CONSECUTIVE_NO_PROGRESS=${CONSECUTIVE_NO_PROGRESS:-0}
MAX_NO_PROGRESS=${MAX_NO_PROGRESS:-5}

# Run a SINGLE test iteration and return
# This allows the outer closed loop to make decisions between tests
run_single_test_iteration() {
    ((++ITERATION))

    # Check max iterations
    if [[ $MAX_ITERATIONS -gt 0 && $ITERATION -gt $MAX_ITERATIONS ]]; then
        echo ""
        print_status "warn" "Max iterations reached ($MAX_ITERATIONS)"
        save_state "2" "$ITERATION"
        return 1  # Signal to stop
    fi

    # Track progress before this iteration
    local progress_before=$(check_test_progress)

    # Get test status
    local test_status=$(count_beta_tests)

    print_iteration_header "$ITERATION" "$test_status"

    save_state "2" "$ITERATION"

    # Get next unchecked test
    local next_test=$(get_next_test)

    if [[ -z "$next_test" ]]; then
        print_status "ok" "All tests complete or blocked!"
        return 0
    fi

    # Parse test info
    local line_num=$(echo "$next_test" | cut -d: -f1)
    local test_line=$(echo "$next_test" | cut -d: -f2-)
    local test_id=$(get_test_id "$test_line")
    local test_block=$(extract_test_block "$line_num")

    # Run test
    local result=$(run_single_test "$test_id" "$test_block")

    case "$result" in
        "PASS")
            mark_test_passed "$test_id"
            reset_test_attempts "$test_id"
            print_status "ok" "$test_id PASSED"
            CONSECUTIVE_BLOCKED=0
            auto_commit "loop-v2($SPRINT): $test_id PASSED"
            ;;

        "BLOCKED_EXTERNAL")
            # Track attempts - even external blockers might be missing features
            local attempts=$(increment_test_attempts "$test_id")
            print_status "warn" "$test_id reported BLOCKED_EXTERNAL (attempt $attempts/$MAX_TEST_FIX_ATTEMPTS)"

            if [[ $attempts -lt $MAX_TEST_FIX_ATTEMPTS ]]; then
                # First attempts: Treat as potentially missing feature, try to implement
                print_status "info" "Attempting to implement enabling feature..."

                # Create feature implementation task
                if ! grep -q "FEAT-$test_id" "$PLAN_FILE" 2>/dev/null; then
                    echo "" >> "$PLAN_FILE"
                    echo "- [ ] **FEAT-$test_id**: Implement feature to unblock $test_id" >> "$PLAN_FILE"
                    echo "  - **Context**: Test blocked - feature may need implementation" >> "$PLAN_FILE"
                fi

                # Run targeted fix agent to try creating the feature
                run_fix_agent "$test_id" "$test_block"

                # Re-test
                local retry_result=$(run_single_test "$test_id" "$test_block")
                if [[ "$retry_result" == "PASS" ]]; then
                    mark_test_passed "$test_id"
                    reset_test_attempts "$test_id"
                    CONSECUTIVE_BLOCKED=0
                    print_status "ok" "$test_id: Feature implemented and test PASSED"
                    auto_commit "loop-v2($SPRINT): $test_id unblocked and PASSED"
                elif [[ "$retry_result" != "BLOCKED_EXTERNAL" ]]; then
                    # Changed to a different result - progress
                    CONSECUTIVE_BLOCKED=0
                    print_status "info" "$test_id: Status changed to $retry_result"
                fi
                # If still BLOCKED_EXTERNAL, will retry on next iteration
            else
                # Max attempts reached - truly external, mark blocked
                mark_test_blocked "$test_id"
                reset_test_attempts "$test_id"
                print_status "warn" "$test_id BLOCKED (verified EXTERNAL after $MAX_TEST_FIX_ATTEMPTS attempts)"
                ((++CONSECUTIVE_BLOCKED))
                if [[ $CONSECUTIVE_BLOCKED -ge $MAX_CONSECUTIVE_BLOCKED ]]; then
                    print_status "warn" "Too many consecutive EXTERNAL blockers - human action required"
                    print_status "info" "See $BLOCKERS_FILE for required actions"
                    return 1  # Signal to stop testing
                fi
            fi
            ;;

        "BLOCKED_FIXABLE")
            # ARCHITECTURE GAP - loop can fix this
            CONSECUTIVE_BLOCKED=0

            # Track fix attempts for this test
            local attempts=$(increment_test_attempts "$test_id")
            print_status "warn" "$test_id BLOCKED_FIXABLE (attempt $attempts/$MAX_TEST_FIX_ATTEMPTS)"

            if [[ $attempts -ge $MAX_TEST_FIX_ATTEMPTS ]]; then
                print_status "warn" "$test_id: Max fix attempts reached - marking as blocked"
                mark_test_blocked "$test_id"
                print_status "info" "Test will be skipped. Investigate manually or wait for related implementation."
            else
                print_status "info" "This is an architecture gap, creating fix task..."

                # Add architecture fix task to implementation plan (if not already exists)
                if ! grep -q "ARCH-$test_id" "$PLAN_FILE" 2>/dev/null; then
                    local task_desc="Fix architecture gap for $test_id (service startup or missing wiring)"
                    echo "" >> "$PLAN_FILE"
                    echo "- [ ] **ARCH-$test_id**: $task_desc" >> "$PLAN_FILE"
                    echo "  - **Test**: $test_id" >> "$PLAN_FILE"
                    echo "  - **Issue**: Service or component not auto-starting" >> "$PLAN_FILE"
                    echo "  - **Fix**: Add to application bootstrap or fix wiring" >> "$PLAN_FILE"
                fi

                # Run targeted fix agent with specific context about what to fix
                print_status "info" "Running targeted fix agent for $test_id..."
                run_fix_agent "$test_id" "$test_block"

                # Re-test
                local retry_result=$(run_single_test "$test_id" "$test_block")
                if [[ "$retry_result" == "PASS" ]]; then
                    mark_test_passed "$test_id"
                    reset_test_attempts "$test_id"
                    sed -i "s/^- \[ \] \*\*ARCH-$test_id\*\*/- [x] **ARCH-$test_id**/" "$PLAN_FILE"
                    print_status "ok" "$test_id FIXED (architecture gap resolved) and PASSED"
                    auto_commit "loop-v2($SPRINT): $test_id architecture gap fixed and PASSED"

                    # Track fix for regression check
                    ((++FIXES_SINCE_REGRESSION_CHECK))
                elif [[ "$retry_result" == "BLOCKED_EXTERNAL" ]]; then
                    # Turns out it was external after all
                    mark_test_blocked "$test_id"
                    reset_test_attempts "$test_id"
                    print_status "warn" "$test_id now BLOCKED_EXTERNAL after investigation"
                else
                    # Still failing - will retry on next iteration (attempts already incremented)
                    print_status "warn" "$test_id still failing after architecture fix (attempt $attempts/$MAX_TEST_FIX_ATTEMPTS)"
                fi
            fi
            ;;

        "FAIL")
            CONSECUTIVE_BLOCKED=0

            # Track fix attempts for this test
            local attempts=$(increment_test_attempts "$test_id")
            print_status "error" "$test_id FAILED (attempt $attempts/$MAX_TEST_FIX_ATTEMPTS)"

            if [[ $attempts -ge $MAX_TEST_FIX_ATTEMPTS ]]; then
                print_status "warn" "$test_id: Max fix attempts reached - marking as blocked"
                mark_test_blocked "$test_id"
                print_status "info" "Test will be skipped. Investigate manually or review implementation."
            else
                print_status "info" "Creating implementation task..."

                # Add task to implementation plan (if not already exists)
                if ! grep -q "FIX-$test_id" "$PLAN_FILE" 2>/dev/null; then
                    local task_desc="Fix failing test $test_id"
                    echo "" >> "$PLAN_FILE"
                    echo "- [ ] **FIX-$test_id**: $task_desc" >> "$PLAN_FILE"
                    echo "  - **Test**: $test_id" >> "$PLAN_FILE"
                    echo "  - **Issue**: Test failed during beta verification" >> "$PLAN_FILE"
                fi

                # Run targeted fix agent with specific context
                print_status "info" "Running targeted fix agent for $test_id..."
                run_fix_agent "$test_id" "$test_block"

                # Re-test
                local retry_result=$(run_single_test "$test_id" "$test_block")
                if [[ "$retry_result" == "PASS" ]]; then
                    mark_test_passed "$test_id"
                    reset_test_attempts "$test_id"
                    # Mark implementation task as done
                    sed -i "s/^- \[ \] \*\*FIX-$test_id\*\*/- [x] **FIX-$test_id**/" "$PLAN_FILE"
                    print_status "ok" "$test_id FIXED and PASSED"
                    auto_commit "loop-v2($SPRINT): $test_id FIXED and PASSED"

                    # Track fix for regression check
                    ((++FIXES_SINCE_REGRESSION_CHECK))
                else
                    # Still failing - will retry on next iteration (attempts already incremented)
                    print_status "warn" "$test_id still failing after fix (attempt $attempts/$MAX_TEST_FIX_ATTEMPTS)"
                fi
            fi
            ;;
    esac

    # Check if regression check is due after fixes
    if should_run_regression_check; then
        print_status "info" "Regression check due ($FIXES_SINCE_REGRESSION_CHECK fixes since last check)"
        if run_regression_check "interval"; then
            FIXES_SINCE_REGRESSION_CHECK=0
        else
            # Regressions found - reset counter, tests have been reset to pending
            FIXES_SINCE_REGRESSION_CHECK=0
            print_status "warn" "Regressions detected - continuing loop to fix them"
        fi
    fi

    # Random spot check - adds unpredictability to regression detection
    if should_run_spot_check; then
        if ! run_random_spot_check; then
            print_status "warn" "Spot check found regressions - continuing loop to fix them"
        fi
    fi

    # Check if we're making progress - if not, break the stuck loop
    handle_stuck_loop "$progress_before"

    # Small delay
    sleep 2

    return 0
}

# Check if any progress was made (tests passed or properly blocked)
check_test_progress() {
    local passed blocked
    passed=$(grepcount "^- \[x\] \*\*" "$BETA_TEST_PLAN")
    blocked=$(grepcount "^- \[B\] \*\*" "$BETA_TEST_PLAN")
    # Ensure we have valid numbers
    [[ -z "$passed" ]] && passed=0
    [[ -z "$blocked" ]] && blocked=0
    echo "$((passed + blocked))"
}

# Detect and handle stuck test loop
handle_stuck_loop() {
    local progress_before="$1"
    local progress_after=$(check_test_progress)

    if [[ "$progress_after" -gt "$progress_before" ]]; then
        # Progress was made
        CONSECUTIVE_NO_PROGRESS=0
        return 0
    else
        # No progress
        ((CONSECUTIVE_NO_PROGRESS++)) || true
        export CONSECUTIVE_NO_PROGRESS

        if [[ $CONSECUTIVE_NO_PROGRESS -ge $MAX_NO_PROGRESS ]]; then
            print_status "error" "Loop stuck: $CONSECUTIVE_NO_PROGRESS iterations with no progress"
            print_status "info" "Force-blocking stuck tests to break the cycle..."

            # Get the current test that's stuck
            local stuck_test=$(get_next_test)
            if [[ -n "$stuck_test" ]]; then
                local test_id=$(echo "$stuck_test" | sed -n 's/.*\*\*\([A-Z]*-[0-9]*\)\*\*.*/\1/p')
                if [[ -n "$test_id" ]]; then
                    mark_test_blocked "$test_id"
                    print_status "warn" "Force-blocked $test_id after $MAX_NO_PROGRESS stuck iterations"
                fi
            fi

            CONSECUTIVE_NO_PROGRESS=0
            return 1
        fi
    fi
    return 0
}

# Run the FULL testing phase (legacy - runs until all tests complete)
# Kept for compatibility but the closed loop uses run_single_test_iteration
run_testing_phase() {
    while true; do
        if ! run_single_test_iteration; then
            break
        fi

        # Check if there are more tests
        if ! has_pending_tests; then
            break
        fi
    done
}
