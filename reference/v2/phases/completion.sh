#!/bin/bash
# Loop V2 Completion Phase - Final sweep and reporting
#
# Dependencies: lib/tests.sh, lib/state.sh, lib/ui.sh, lib/git.sh
# Requires: BETA_TEST_PLAN, ITERATION, BRANCH_NAME, STATE_FILE

run_final_regression_sweep() {
    print_phase "REG" "Final Regression Sweep (Before Completion)"

    # Check if we have any passing tests to verify
    local passing_count=$(grepcount "^- \[x\] \*\*" "$BETA_TEST_PLAN")

    if [[ "$passing_count" -gt 0 ]]; then
        print_status "info" "Running final regression check on $passing_count passing tests..."

        if ! run_regression_check "completion"; then
            print_status "error" "Final regression sweep found issues!"
            print_status "info" "Tests have been reset - loop will continue to fix regressions"

            # Re-count after regressions were reset
            local pending=$(grepcount "^- \[ \] \*\*" "$BETA_TEST_PLAN")

            if [[ "$pending" -gt 0 ]]; then
                print_status "warn" "$pending tests need to be re-verified after regression detection"
                print_final_regression_failure "$pending"
                save_state "2" "$ITERATION"
                return 1
            fi
        else
            print_status "ok" "Final regression sweep passed - all tests still working"
        fi
    else
        print_status "info" "No passing tests to verify in final sweep"
    fi

    return 0
}

run_completion_phase() {
    # Final counts (re-count after potential regression resets)
    local passed=$(grepcount "^- \[x\] \*\*" "$BETA_TEST_PLAN")
    local blocked=$(grepcount "^- \[B\] \*\*" "$BETA_TEST_PLAN")
    local pending=$(grepcount "^- \[ \] \*\*" "$BETA_TEST_PLAN")

    auto_commit "loop-v2($SPRINT): Beta testing complete - $passed passed, $blocked blocked"

    if [[ "$pending" -eq 0 && "$blocked" -eq 0 ]]; then
        # FULL SUCCESS
        print_full_success "$passed" "$ITERATION" "$BRANCH_NAME"
        rm -f "$STATE_FILE"
        exit 0
    elif [[ "$pending" -eq 0 ]]; then
        # PARTIAL SUCCESS - all done but some blocked
        print_partial_blocked "$passed" "$blocked" "$BRANCH_NAME"
        exit 2
    else
        # INCOMPLETE
        print_incomplete "$passed" "$blocked" "$pending"
        exit 1
    fi
}
