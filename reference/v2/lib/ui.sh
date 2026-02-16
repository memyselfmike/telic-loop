#!/bin/bash
# Loop V2 UI Functions - Print functions for user feedback
#
# Dependencies: lib/config.sh (for colors)
# Requires: SPRINT, SPRINT_DIR, MAX_ITERATIONS, STATE_PHASE, STATE_ITERATION

print_banner() {
    echo ""
    echo -e "${PURPLE}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                    LOOP V2: VALUE-DRIVEN DELIVERY                 ║${NC}"
    echo -e "${PURPLE}╠═══════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║${NC}  Sprint: ${CYAN}$SPRINT${NC}"
    echo -e "${PURPLE}║${NC}  Directory: ${CYAN}$SPRINT_DIR${NC}"
    echo -e "${PURPLE}║${NC}  Max iterations: ${CYAN}${MAX_ITERATIONS:-unlimited}${NC}"
    if [[ -n "$STATE_PHASE" ]]; then
    echo -e "${PURPLE}║${NC}  ${GREEN}Resuming from: Phase $STATE_PHASE, Iteration $STATE_ITERATION${NC}"
    fi
    echo -e "${PURPLE}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_phase() {
    local phase="$1"
    local description="$2"
    echo ""
    echo -e "${BLUE}┌─────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BLUE}│${NC} ${YELLOW}PHASE $phase${NC}: $description"
    echo -e "${BLUE}└─────────────────────────────────────────────────────────────────┘${NC}"
}

print_vrc() {
    local checkpoint="$1"
    local question="$2"
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}VRC-$checkpoint${NC}: $question"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
}

print_status() {
    local status="$1"
    local message="$2"
    case "$status" in
        "ok")
            echo -e "${GREEN}✓${NC} $message"
            ;;
        "warn")
            echo -e "${YELLOW}⚠${NC} $message"
            ;;
        "error")
            echo -e "${RED}✗${NC} $message"
            ;;
        "info")
            echo -e "${BLUE}ℹ${NC} $message"
            ;;
        "skip")
            echo -e "${CYAN}→${NC} $message (already done)"
            ;;
    esac
}

print_iteration_header() {
    local iteration="$1"
    local test_status="$2"
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}  ITERATION $iteration | $test_status${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_regression_header() {
    local trigger="$1"
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║             REGRESSION CHECK - Verifying Passing Tests            ║${NC}"
    echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC}  Trigger: ${YELLOW}$trigger${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_spot_check_header() {
    local count="$1"
    echo ""
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} ${YELLOW}RANDOM SPOT CHECK${NC} - Verifying $count random passing tests"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────┘${NC}"
}

print_regression_failure() {
    local regressions="$1"
    local regressed_tests="$2"
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ⚠️  REGRESSIONS DETECTED - $regressions tests now failing        ${NC}"
    echo -e "${RED}╠═══════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${RED}║${NC}  Affected tests:${regressed_tests}"
    echo -e "${RED}║${NC}  These tests have been reset to pending."
    echo -e "${RED}║${NC}  Regression fix tasks created."
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_final_regression_failure() {
    local pending="$1"
    echo ""
    echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║   ⚠️  REGRESSIONS DETECTED DURING FINAL SWEEP                      ║${NC}"
    echo -e "${YELLOW}╠═══════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${YELLOW}║${NC}  Tests reset to pending: ${RED}$pending${NC}"
    echo -e "${YELLOW}║${NC}  Re-run the loop to fix regressions."
    echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_partial_success() {
    local branch="$1"
    local iteration="$2"
    local task_progress="$3"
    local blocked="$4"

    echo ""
    echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║                                                                   ║${NC}"
    echo -e "${YELLOW}║   ⚠️  PARTIAL SUCCESS - VALUE DELIVERED WITH BLOCKERS             ║${NC}"
    echo -e "${YELLOW}║                                                                   ║${NC}"
    echo -e "${YELLOW}║${NC}   Branch: ${CYAN}$branch${NC}"
    echo -e "${YELLOW}║${NC}   Iterations: ${CYAN}$iteration${NC}"
    echo -e "${YELLOW}║${NC}   Tasks Completed: ${GREEN}$task_progress${NC}"
    echo -e "${YELLOW}║${NC}   Tasks Blocked: ${RED}$blocked${NC}"
    echo -e "${YELLOW}║                                                                   ║${NC}"
    echo -e "${YELLOW}║${NC}   Deliverable value has been maximized.                         ${NC}"
    echo -e "${YELLOW}║${NC}   See ${CYAN}$BLOCKERS_FILE${NC} for required human actions.${NC}"
    echo -e "${YELLOW}║                                                                   ║${NC}"
    echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_full_success() {
    local passed="$1"
    local iteration="$2"
    local branch="$3"

    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✅ SPRINT COMPLETE - ALL VALUE DELIVERED                        ║${NC}"
    echo -e "${GREEN}╠═══════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║${NC}  Tests Passed: ${CYAN}$passed${NC}"
    echo -e "${GREEN}║${NC}  Iterations: ${CYAN}$iteration${NC}"
    echo -e "${GREEN}║${NC}  Branch: ${CYAN}$branch${NC}"
    echo -e "${GREEN}║${NC}  Final Regression: ${GREEN}PASSED${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_partial_blocked() {
    local passed="$1"
    local blocked="$2"
    local branch="$3"

    echo ""
    echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║   ⚠️  PARTIAL SUCCESS - Some tests blocked                         ║${NC}"
    echo -e "${YELLOW}╠═══════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${YELLOW}║${NC}  Tests Passed: ${GREEN}$passed${NC}"
    echo -e "${YELLOW}║${NC}  Tests Blocked: ${RED}$blocked${NC}"
    echo -e "${YELLOW}║${NC}  Branch: ${CYAN}$branch${NC}"
    echo -e "${YELLOW}║${NC}"
    echo -e "${YELLOW}║${NC}  See BLOCKERS.md for required human actions."
    echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_incomplete() {
    local passed="$1"
    local blocked="$2"
    local pending="$3"

    echo ""
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ❌ INCOMPLETE - Some tests still pending                        ║${NC}"
    echo -e "${RED}╠═══════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${RED}║${NC}  Tests Passed: ${GREEN}$passed${NC}"
    echo -e "${RED}║${NC}  Tests Blocked: ${YELLOW}$blocked${NC}"
    echo -e "${RED}║${NC}  Tests Pending: ${RED}$pending${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}
