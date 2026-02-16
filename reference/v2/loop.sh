#!/bin/bash
# Loop V2: Value-Driven Sprint Delivery
#
# A TRUE CLOSED-LOOP system that delivers production-ready implementations
# where the USER gets the VALUE they were promised.
#
# RESUMABLE: If interrupted, run again to continue from last state.
#
# Usage:
#   ./loop-v2/loop.sh <sprint> [max-iterations]
#
# Example:
#   ./loop-v2/loop.sh 1-mvp          # Run until all value delivered
#   ./loop-v2/loop.sh 1-mvp 50       # Max 50 iterations
#
# The loop will NOT exit until:
#   - Every VISION deliverable verified for VALUE delivery
#   - User can achieve the complete workflow end-to-end
#   - All quality gates pass
#
# Creates branch: loop-v2/{sprint}-{timestamp}
# State tracked in: {SPRINT_DIR}/LOOP_STATE.md

set -e

# ═══════════════════════════════════════════════════════════════════════════
# BOOTSTRAP - Source all modules
# ═══════════════════════════════════════════════════════════════════════════

# Get the directory where this script lives (before sourcing anything)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source bootstrap first (defines LOOP_ROOT)
source "$SCRIPT_DIR/lib/_init.sh"

# Source libraries in dependency order
source "$LOOP_ROOT/lib/config.sh"
source "$LOOP_ROOT/lib/state.sh"
source "$LOOP_ROOT/lib/ui.sh"
source "$LOOP_ROOT/lib/docs.sh"
source "$LOOP_ROOT/lib/prompts.sh"
source "$LOOP_ROOT/lib/metrics.sh"
source "$LOOP_ROOT/lib/git.sh"
source "$LOOP_ROOT/lib/branch.sh"
source "$LOOP_ROOT/lib/services.sh"
source "$LOOP_ROOT/lib/tests.sh"

# Source phases
source "$LOOP_ROOT/phases/planning.sh"
source "$LOOP_ROOT/phases/service-check.sh"
source "$LOOP_ROOT/phases/testing.sh"
source "$LOOP_ROOT/phases/completion.sh"

# ═══════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSING
# ═══════════════════════════════════════════════════════════════════════════

if [[ $# -lt 1 ]]; then
    echo -e "${RED}Usage: ./loop-v2/loop.sh <sprint> [max-iterations]${NC}"
    echo ""
    echo "  sprint:          Sprint folder name (e.g., 1-mvp, 2-automation)"
    echo "  max-iterations:  Optional max iterations (default: unlimited)"
    echo ""
    echo "Example:"
    echo "  ./loop-v2/loop.sh 1-mvp"
    echo ""
    echo "The loop is RESUMABLE - if interrupted, run again to continue."
    exit 1
fi

SPRINT="$1"
MAX_ITERATIONS="${2:-0}"

# ═══════════════════════════════════════════════════════════════════════════
# SPRINT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Validate sprint directory
SPRINT_DIR="docs/sprints/$SPRINT"
if [[ ! -d "$SPRINT_DIR" ]]; then
    echo -e "${RED}Error: Sprint folder not found: $SPRINT_DIR${NC}"
    echo ""
    echo "Available sprints:"
    ls -d docs/sprints/*/ 2>/dev/null | xargs -n1 basename
    exit 1
fi

# File paths
VISION_FILE="$SPRINT_DIR/VISION.md"
PRD_FILE="$SPRINT_DIR/PRD.md"
ARCH_FILE="$SPRINT_DIR/ARCHITECTURE.md"
PLAN_FILE="$SPRINT_DIR/IMPLEMENTATION_PLAN.md"
VALUE_CHECKLIST="$SPRINT_DIR/VALUE_CHECKLIST.md"
BLOCKERS_FILE="$SPRINT_DIR/BLOCKERS.md"
STATE_FILE="$SPRINT_DIR/LOOP_STATE.md"
BETA_TEST_PLAN="$SPRINT_DIR/BETA_TEST_PLAN_v1.md"
REGRESSION_LOG="$SPRINT_DIR/REGRESSION_LOG.md"

# Export for prompts and submodules
export SPRINT
export SPRINT_DIR
export VISION_FILE
export PRD_FILE
export ARCH_FILE
export PLAN_FILE
export VALUE_CHECKLIST
export BLOCKERS_FILE
export MAX_TASK_ATTEMPTS
export BETA_TEST_PLAN
export REGRESSION_LOG

# ═══════════════════════════════════════════════════════════════════════════
# SPRINT-SPECIFIC CONFIGURATION (Optional)
# ═══════════════════════════════════════════════════════════════════════════
# Load sprint-specific config if it exists. This allows each sprint to
# override default settings (ports, timeouts, service requirements, etc.)
#
# Example sprint config (docs/sprints/1-mvp/loop-config.sh):
#   LOOP_BACKEND_PORT=8080
#   LOOP_FRONTEND_PORT=4000
#   LOOP_SKIP_BROWSER=true

SPRINT_CONFIG="$SPRINT_DIR/loop-config.sh"
if [[ -f "$SPRINT_CONFIG" ]]; then
    print_status "info" "Loading sprint-specific config: $SPRINT_CONFIG"
    source "$SPRINT_CONFIG"
fi

# ═══════════════════════════════════════════════════════════════════════════
# LOOP CONTROL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

# Check if planning is needed (no plan or plan is stale)
needs_planning() {
    # No plan file exists
    if [[ ! -f "$PLAN_FILE" ]]; then
        return 0
    fi

    # Planning gate not passed
    if ! gate_passed "planning"; then
        return 0
    fi

    return 1
}

# Check if there are pending tests
has_pending_tests() {
    if [[ ! -f "$BETA_TEST_PLAN" ]]; then
        return 1
    fi

    local pending=$(grepcount "^- \[ \] \*\*" "$BETA_TEST_PLAN")
    [[ "$pending" -gt 0 ]]
}

# Check if VISION is delivered (all non-blocked value complete)
vision_delivered() {
    if [[ ! -f "$VALUE_CHECKLIST" ]]; then
        return 1
    fi

    # Count unchecked VALUE items that are NOT blocked
    local unchecked=$(grep -E "\| \[ \] \|[^|]*\| \[ \] \|" "$VALUE_CHECKLIST" 2>/dev/null | grep -v "BLOCKED" | wc -l)

    # Also check if we have any verified value at all
    local verified=$(grepcount "\| \[x\] \|" "$VALUE_CHECKLIST")

    # Vision delivered if no unchecked items AND we have some verified value
    [[ "$unchecked" -eq 0 && "$verified" -gt 0 ]]
}

# Invalidate planning gate (forces re-planning)
# For minor changes - just re-run planning phase
invalidate_planning() {
    local reason="$1"
    print_status "warn" "Invalidating planning: $reason"
    invalidate_gate "planning"
    invalidate_gate "vrc2"
    save_state "$STATE_PHASE" "$ITERATION"
}

# Invalidate planning AND quality gates
# For major changes that require full re-verification
invalidate_planning_and_quality() {
    local reason="$1"
    print_status "warn" "Major change detected - invalidating planning and quality gates"
    invalidate_all_planning "$reason"
    save_state "$STATE_PHASE" "$ITERATION"
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

# Load existing state if present
if load_state; then
    print_status "info" "Found existing state - will resume"
fi

ITERATION=${STATE_ITERATION:-0}
LOOP_ITERATION=0
MAX_LOOP_ITERATIONS=100  # Safety limit for outer loop

# Stuck detection - track progress to trigger value discovery
LAST_PROGRESS_HASH=""
NO_PROGRESS_COUNT=0
MAX_NO_PROGRESS=${MAX_NO_PROGRESS:-3}  # After N iterations with no progress, run value discovery

# Implementation stuck detection - prevent infinite implementation loops
IMPL_NO_PROGRESS_COUNT=0
MAX_IMPL_NO_PROGRESS=3  # After 3 implementation iterations with no progress, move to testing
LAST_IMPL_TASK=""

# Function to compute progress hash (tests passed + blocked + tasks done)
compute_progress_hash() {
    local passed=$(grepcount "^- \[x\] \*\*" "$BETA_TEST_PLAN")
    local blocked=$(grepcount "^- \[B\] \*\*" "$BETA_TEST_PLAN")
    local tasks=$(grepcount "^- \[x\]" "$PLAN_FILE")
    echo "${passed}-${blocked}-${tasks}"
}

# Function to run value discovery and reclassify blockers
run_value_discovery() {
    print_status "warn" "Loop stuck for $NO_PROGRESS_COUNT iterations - running value discovery"
    echo ""
    echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║          VALUE DISCOVERY - Breaking the stuck loop                ║${NC}"
    echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # First, reclassify blockers (UI missing → BUILD, infra missing → INFRA)
    print_status "info" "Step 1: Reclassifying blockers..."
    run_prompt "verify-blockers"

    # Then run value discovery to find additional BUILDABLE blockers
    print_status "info" "Step 2: Discovering buildable value..."
    run_prompt "discover-value"

    # Reset stuck counter after discovery
    NO_PROGRESS_COUNT=0
    LAST_PROGRESS_HASH=$(compute_progress_hash)

    # Invalidate planning to pick up new BUILD tasks
    invalidate_planning "Value discovery found buildable blockers"
}

print_banner

# Check claude CLI exists
if ! command -v claude &> /dev/null; then
    print_status "error" "claude CLI not found in PATH"
    exit 1
fi

# ───────────────────────────────────────────────────────────────────────────
# PHASE 0: Verify approved docs exist (one-time)
# ───────────────────────────────────────────────────────────────────────────

if [[ "$STATE_PHASE" == "" ]] || [[ "$STATE_PHASE" == "0" ]]; then
    print_phase "0" "Verify Approved Documents"

    if ! check_docs_exist; then
        print_status "error" "Required documents missing. Create VISION.md and PRD.md first."
        exit 1
    fi

    save_state "0" "$ITERATION"
fi

# ───────────────────────────────────────────────────────────────────────────
# Create/switch to branch (one-time)
# ───────────────────────────────────────────────────────────────────────────

setup_sprint_branch

# Ensure sensitive files are in .gitignore
ensure_gitignore

# ═══════════════════════════════════════════════════════════════════════════
# THE CLOSED LOOP - Iterate until VISION is delivered
# ═══════════════════════════════════════════════════════════════════════════
#
# This is the TRUE closed loop. It keeps iterating through phases until:
# 1. All tests pass (or are blocked on external factors)
# 2. VRC confirms VISION is delivered
# 3. No new gaps are discovered
#
# If any phase discovers new work, the loop continues from the appropriate
# phase rather than procedurally marching to completion.
# ═══════════════════════════════════════════════════════════════════════════

while true; do
    ((++LOOP_ITERATION))

    echo ""
    echo -e "${PURPLE}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║          LOOP ITERATION $LOOP_ITERATION - Checking VISION delivery              ║${NC}"
    echo -e "${PURPLE}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Safety limit
    if [[ $LOOP_ITERATION -gt $MAX_LOOP_ITERATIONS ]]; then
        print_status "error" "Max loop iterations reached ($MAX_LOOP_ITERATIONS) - possible infinite loop"
        print_status "info" "Check for oscillating conditions or unresolvable blockers"
        exit 1
    fi

    # ─────────────────────────────────────────────────────────────────────
    # STEP 1: Start services (always ensure environment is ready)
    # ─────────────────────────────────────────────────────────────────────
    # Note: Service startup failure is NOT fatal. If services can't start,
    # the service_check phase will create implementation tasks.
    # The || true prevents set -e from exiting on startup failure.

    start_required_services || true

    # ─────────────────────────────────────────────────────────────────────
    # STEP 1.5: Verify blockers (check if user resolved any blockers)
    # ─────────────────────────────────────────────────────────────────────
    # This checks if .env or other config files have been updated since
    # the last VALUE_CHECKLIST update, and re-verifies blockers if so.
    # This allows the loop to automatically detect when credentials are
    # configured without needing manual VALUE_CHECKLIST updates.

    verify_blockers

    # ─────────────────────────────────────────────────────────────────────
    # STEP 2: Planning (if needed)
    # ─────────────────────────────────────────────────────────────────────

    if needs_planning; then
        print_status "info" "Planning needed - running planning phase"
        run_planning_phase
        run_preflight_phase

        # After planning, always check services
        continue
    fi

    # ─────────────────────────────────────────────────────────────────────
    # STEP 3: Service readiness check
    # ─────────────────────────────────────────────────────────────────────

    if ! gate_passed "service_readiness"; then
        print_status "info" "Checking service readiness"

        # Store task count before
        tasks_before=$(grepcount "^- \[ \]" "$PLAN_FILE")

        run_service_check_phase

        # Check if new tasks were created
        tasks_after=$(grepcount "^- \[ \]" "$PLAN_FILE")

        if [[ "$tasks_after" -gt "$tasks_before" ]]; then
            print_status "warn" "Service check created new tasks - invalidating planning"
            invalidate_planning "Service check created new implementation tasks"
            continue
        fi
    else
        # Gate is passed - verify services are still running
        run_service_check_phase
        if [[ $? -ne 0 ]]; then
            # Services stopped, gate was invalidated, restart loop
            print_status "info" "Restarting loop to re-check services"
            continue
        fi
    fi

    # ─────────────────────────────────────────────────────────────────────
    # PHASE: IMPLEMENT - Build pending tasks before testing
    # ─────────────────────────────────────────────────────────────────────
    # Implementation runs FIRST, before test plan generation.
    # Order: Plan → Implement → Generate Tests → Run Tests
    #
    # Task types implemented here:
    # - BUILD-* : Missing UI features (from blocker validation)
    # - INT-*   : Architecture gaps (from CONNECT review)
    # - Task X.Y: Original plan tasks
    # FIX-*/ARCH-* are created and handled during testing phase.

    # Count different task types - use flexible patterns
    # Strip \r\n to avoid CRLF issues on Windows causing arithmetic errors
    pending_build=$(grepcount "^\- \[ \] \*\*BUILD-" "$PLAN_FILE")
    pending_int=$(grepcount "^\- \[ \] \*\*INT-" "$PLAN_FILE")
    pending_task=$(grepcount "^\- \[ \] \*\*Task" "$PLAN_FILE")

    # Ensure we have valid numbers (default to 0 if empty)
    pending_build=${pending_build:-0}
    pending_int=${pending_int:-0}
    pending_task=${pending_task:-0}

    total_pending=$((pending_build + pending_int + pending_task))

    # Always show implementation phase status
    print_phase "IMPL" "Implementation Phase"

    if [[ "$total_pending" -gt 0 ]]; then
        print_status "info" "Pending tasks: BUILD=$pending_build, INT=$pending_int, Task=$pending_task (Total: $total_pending)"

        # Store task count before implementation
        tasks_before=$(grepcount "^\- \[ \]" "$PLAN_FILE")

        # Extract and display the next task to be implemented (priority order)
        next_task=""
        if [[ "$pending_build" -gt 0 ]]; then
            next_task=$(grep -m1 "^\- \[ \] \*\*BUILD-" "$PLAN_FILE" 2>/dev/null | sed 's/^- \[ \] //' | head -c 100)
        elif [[ "$pending_int" -gt 0 ]]; then
            next_task=$(grep -m1 "^\- \[ \] \*\*INT-" "$PLAN_FILE" 2>/dev/null | sed 's/^- \[ \] //' | head -c 100)
        elif [[ "$pending_task" -gt 0 ]]; then
            next_task=$(grep -m1 "^\- \[ \] \*\*Task" "$PLAN_FILE" 2>/dev/null | sed 's/^- \[ \] //' | head -c 100)
        fi

        if [[ -n "$next_task" ]]; then
            # Check if this is a user-action task (not implementable by the loop)
            # Look for the task and its following lines for "User must" indicators
            task_line_num=$(grep -n "^\- \[ \] \*\*Task" "$PLAN_FILE" 2>/dev/null | head -1 | cut -d: -f1)
            if [[ -n "$task_line_num" ]]; then
                # Check the task line and next 3 lines for user action indicators
                task_context=$(sed -n "${task_line_num},$((task_line_num + 3))p" "$PLAN_FILE" 2>/dev/null)
                if echo "$task_context" | grep -qiE "user must|user action|manual|configure.*credentials|login.*via|requires user"; then
                    # This is a user action task - mark as user-blocked and skip
                    task_id=$(echo "$next_task" | sed -n 's/.*\*\*\(Task [0-9.]*\)\*\*.*/\1/p')
                    if [[ -n "$task_id" ]]; then
                        print_status "info" "Skipping user-action task: $task_id"
                        # Mark with [U] for user-action required
                        sed -i "s/^\- \[ \] \*\*$task_id\*\*/- [U] **$task_id**/g" "$PLAN_FILE"
                        print_status "ok" "Marked $task_id as user-action required [U]"
                        # Continue to next iteration to process remaining tasks
                        continue
                    fi
                fi
            fi
            print_status "info" "Implementing: $next_task"
        fi

        # Run implement prompt to work on highest priority task
        run_prompt "implement"

        # Check progress
        tasks_after=$(grepcount "^\- \[ \]" "$PLAN_FILE")
        completed=$((tasks_before - tasks_after))

        if [[ "$completed" -gt 0 ]]; then
            print_status "ok" "Completed $completed tasks ($tasks_after remaining)"
            auto_commit "loop-v2($SPRINT): Implementation progress"
            # Reset stuck detection on progress
            IMPL_NO_PROGRESS_COUNT=0
            LAST_IMPL_TASK=""
        elif [[ "$tasks_after" -gt "$tasks_before" ]]; then
            # New tasks were created (sub-tasks, dependencies discovered)
            print_status "info" "Implementation created new tasks"
            IMPL_NO_PROGRESS_COUNT=0
        else
            # No progress - check if we're stuck on the same task
            if [[ "$next_task" == "$LAST_IMPL_TASK" ]]; then
                ((IMPL_NO_PROGRESS_COUNT++)) || true
                print_status "warn" "No progress on same task ($IMPL_NO_PROGRESS_COUNT/$MAX_IMPL_NO_PROGRESS)"

                if [[ $IMPL_NO_PROGRESS_COUNT -ge $MAX_IMPL_NO_PROGRESS ]]; then
                    # Extract task ID and mark as blocked
                    stuck_task_id=$(echo "$next_task" | sed -n 's/.*\*\*\([A-Z]*-[0-9]*\)\*\*.*/\1/p')
                    if [[ -n "$stuck_task_id" ]]; then
                        print_status "warn" "Implementation stuck on $stuck_task_id - marking as blocked"
                        # Mark task as blocked in plan file
                        sed -i "s/^\- \[ \] \*\*$stuck_task_id\*\*/- [B] **$stuck_task_id**/g" "$PLAN_FILE"
                        auto_commit "loop-v2($SPRINT): Blocked stuck task $stuck_task_id"
                    fi
                    IMPL_NO_PROGRESS_COUNT=0
                    LAST_IMPL_TASK=""
                    # Don't continue - fall through to testing phase
                    print_status "info" "Proceeding to testing phase (implementation blocked)"
                fi
            else
                # Different task - reset counter
                IMPL_NO_PROGRESS_COUNT=1
                LAST_IMPL_TASK="$next_task"
                print_status "warn" "No tasks completed this iteration"
            fi
        fi

        # Only continue if we haven't hit max stuck iterations
        if [[ $IMPL_NO_PROGRESS_COUNT -lt $MAX_IMPL_NO_PROGRESS ]]; then
            continue
        fi
    else
        print_status "ok" "All implementation tasks complete"
    fi

    # ─────────────────────────────────────────────────────────────────────
    # STEP 4: Generate test plan (after implementation, before testing)
    # ─────────────────────────────────────────────────────────────────────
    # The test plan is generated AFTER implementation so it reflects
    # what was actually built, not just what was planned.

    if [[ ! -f "$BETA_TEST_PLAN" ]] || ! gate_passed "test_plan_generated"; then
        generate_test_plan
    fi

    # ─────────────────────────────────────────────────────────────────────
    # STEP 5: Run tests (one batch at a time for responsiveness)
    # ─────────────────────────────────────────────────────────────────────
    # Note: Tests will run even if some services are down.
    # Tests requiring unavailable services will fail/block naturally.
    # This allows frontend-only tests to pass while backend is being fixed.

    if has_pending_tests; then
        print_status "info" "Running test iteration"

        # Store task count before
        tasks_before=$(grepcount "^- \[ \]" "$PLAN_FILE")

        # Run one iteration of testing (not the full loop)
        run_single_test_iteration

        # Check if new tasks were created (fix tasks, architecture gaps, etc.)
        tasks_after=$(grepcount "^- \[ \]" "$PLAN_FILE")

        if [[ "$tasks_after" -gt "$tasks_before" ]]; then
            print_status "info" "Testing created new tasks"

            # Check if these are significant structural changes
            if check_for_significant_changes "$tasks_before" "$tasks_after"; then
                # Significant changes - invalidate quality gates for re-verification
                invalidate_quality_gates "Significant structural changes during implementation"
                save_state "$STATE_PHASE" "$ITERATION"
            fi

            # Periodic VRC check regardless
            if [[ $((ITERATION % 10)) -eq 0 ]]; then
                print_status "info" "Periodic VRC check..."
                run_prompt "vrc"
            fi
        fi

        # ─────────────────────────────────────────────────────────────────
        # STUCK DETECTION: Check if we're making progress
        # ─────────────────────────────────────────────────────────────────
        current_progress=$(compute_progress_hash)
        if [[ "$current_progress" == "$LAST_PROGRESS_HASH" ]]; then
            ((++NO_PROGRESS_COUNT))
            print_status "warn" "No progress this iteration ($NO_PROGRESS_COUNT/$MAX_NO_PROGRESS)"

            if [[ $NO_PROGRESS_COUNT -ge $MAX_NO_PROGRESS ]]; then
                # We're stuck - run value discovery to find buildable blockers
                run_value_discovery
                # After discovery, restart the loop to pick up new tasks
                continue
            fi
        else
            # Progress was made - reset counter
            NO_PROGRESS_COUNT=0
            LAST_PROGRESS_HASH="$current_progress"
        fi

        # Continue loop to process more tests
        continue
    fi

    # ─────────────────────────────────────────────────────────────────────
    # STEP 4.5: Check if all tests are BLOCKED (not just complete)
    # ─────────────────────────────────────────────────────────────────────
    # If there are no pending tests but there ARE blocked tests,
    # run value discovery before giving up - some blockers may be buildable

    blocked_tests=$(grepcount "^- \[B\] \*\*" "$BETA_TEST_PLAN")
    passed_tests=$(grepcount "^- \[x\] \*\*" "$BETA_TEST_PLAN")

    if [[ "$blocked_tests" -gt 0 && "$blocked_tests" -gt "$passed_tests" ]]; then
        print_status "warn" "More tests blocked ($blocked_tests) than passed ($passed_tests)"
        print_status "info" "Running value discovery to find buildable blockers..."

        run_value_discovery

        # After discovery, check if we have new pending tests/tasks
        if has_pending_tests || has_uncomplete_tasks; then
            print_status "ok" "Value discovery found work to do"
            continue
        fi
    fi

    # ─────────────────────────────────────────────────────────────────────
    # STEP 5: All tests complete - run final VRC
    # ─────────────────────────────────────────────────────────────────────

    print_phase "VRC" "Vision Reality Check - Is VISION truly delivered?"

    # Run VRC to check if vision is delivered
    run_prompt "vrc"

    # Check if VRC found gaps (it will update VALUE_CHECKLIST)
    if ! vision_delivered; then
        # Check if new tasks were added
        pending_tasks=$(grepcount "^- \[ \]" "$PLAN_FILE")

        if [[ "$pending_tasks" -gt 0 ]]; then
            print_status "warn" "VRC found gaps - $pending_tasks tasks pending"
            print_status "info" "Continuing loop to address gaps..."
            continue
        fi

        # Check for blocked items
        blocked_tasks=$(grepcount "^- \[B\]" "$PLAN_FILE")

        if [[ "$blocked_tasks" -gt 0 ]]; then
            # CRITICAL: Before giving up, check if blockers are BUILDABLE
            # BUILD-* tasks represent "external blockers" that are actually missing UI features
            pending_build=$(grepcount "^- \[ \] \*\*BUILD-" "$PLAN_FILE")

            if [[ "$pending_build" -gt 0 ]]; then
                print_status "warn" "Found $blocked_tasks blocked items, but $pending_build BUILD tasks can unblock them"
                print_status "info" "BUILD tasks are missing UI features that need implementation, not external blockers"
                print_status "info" "Running implementation to build missing features..."

                # Force implementation of BUILD tasks
                run_prompt "implement"

                # Check if we made progress
                remaining_build=$(grepcount "^- \[ \] \*\*BUILD-" "$PLAN_FILE")
                if [[ "$remaining_build" -lt "$pending_build" ]]; then
                    print_status "ok" "Implemented $(($pending_build - $remaining_build)) BUILD tasks"
                    auto_commit "loop-v2($SPRINT): Built missing features to unblock"
                fi

                # Continue loop to re-evaluate
                continue
            fi

            print_status "warn" "Some items blocked on truly external factors"
            # Run final regression and exit with partial success
            break
        fi

        # No tasks, no blocked items, but vision not delivered?
        # This means VRC needs to create tasks
        print_status "warn" "Vision not delivered but no tasks - VRC should create gap tasks"
        run_prompt "discover"  # Discovery prompt to find gaps

        new_tasks=$(grepcount "^- \[ \]" "$PLAN_FILE")
        if [[ "$new_tasks" -gt 0 ]]; then
            invalidate_planning "Gap discovery found new work"
            continue
        else
            print_status "error" "Cannot determine how to deliver VISION"
            break
        fi
    fi

    # ─────────────────────────────────────────────────────────────────────
    # STEP 6: Vision delivered! Final checks and exit
    # ─────────────────────────────────────────────────────────────────────

    print_status "ok" "VRC confirms VISION is delivered!"
    break

done

# ═══════════════════════════════════════════════════════════════════════════
# POST-LOOP: Final regression sweep and completion
# ═══════════════════════════════════════════════════════════════════════════

print_phase "FINAL" "Final Verification Before Completion"

# Final regression sweep
if ! run_final_regression_sweep; then
    print_status "warn" "Final regression found issues"

    # Check if we should re-enter the loop
    if has_pending_tests; then
        print_status "info" "Re-entering loop to fix regressions..."
        # Re-run the loop (recursive call or state reset)
        save_state "2" "$ITERATION"
        exec "$0" "$SPRINT" "$MAX_ITERATIONS"
    fi
fi

# Run completion phase (reports final status and exits)
run_completion_phase
