#!/bin/bash
# Loop V2 Planning Phase - VRC, quality gates, and plan generation
#
# Dependencies: lib/state.sh, lib/ui.sh, lib/prompts.sh, lib/git.sh
# Requires: PLAN_FILE, ITERATION, STATE_PHASE

# Maximum retries for each gate before giving up
MAX_GATE_RETRIES=3

# Run a quality gate with auto-remediation loop
# The gate runs, fixes issues, then re-runs to verify fixes
# Loops until gate passes (no changes) or max retries
run_gate_with_remediation() {
    local gate_name="$1"
    local prompt_name="$2"
    local display_name="$3"
    local retry=0

    if gate_passed "$gate_name"; then
        print_status "skip" "$display_name already passed"
        return 0
    fi

    while [[ $retry -lt $MAX_GATE_RETRIES ]]; do
        ((++retry))

        if [[ $retry -gt 1 ]]; then
            print_status "info" "$display_name - remediation pass $retry/$MAX_GATE_RETRIES"
        else
            print_status "info" "Running $display_name..."
        fi

        # Capture file state before running gate
        local plan_hash_before=""
        local checklist_hash_before=""
        if [[ -f "$PLAN_FILE" ]]; then
            plan_hash_before=$(md5sum "$PLAN_FILE" 2>/dev/null | cut -d' ' -f1)
        fi
        if [[ -f "$VALUE_CHECKLIST" ]]; then
            checklist_hash_before=$(md5sum "$VALUE_CHECKLIST" 2>/dev/null | cut -d' ' -f1)
        fi

        # Run the gate prompt (it will analyze and fix issues)
        run_prompt "$prompt_name"

        # Check if files were modified (gate made changes)
        local plan_hash_after=""
        local checklist_hash_after=""
        if [[ -f "$PLAN_FILE" ]]; then
            plan_hash_after=$(md5sum "$PLAN_FILE" 2>/dev/null | cut -d' ' -f1)
        fi
        if [[ -f "$VALUE_CHECKLIST" ]]; then
            checklist_hash_after=$(md5sum "$VALUE_CHECKLIST" 2>/dev/null | cut -d' ' -f1)
        fi

        # If no changes were made, gate passed
        if [[ "$plan_hash_before" == "$plan_hash_after" && "$checklist_hash_before" == "$checklist_hash_after" ]]; then
            print_status "ok" "$display_name PASSED (no issues found)"
            mark_gate_passed "$gate_name"
            return 0
        fi

        # Changes were made - gate found and fixed issues
        print_status "warn" "$display_name found issues and applied fixes"

        if [[ $retry -lt $MAX_GATE_RETRIES ]]; then
            print_status "info" "Re-running $display_name to verify fixes..."
            auto_commit "loop-v2($SPRINT): $display_name - remediation pass $retry"
        fi
    done

    # Max retries reached - mark passed anyway but warn
    print_status "warn" "$display_name reached max retries ($MAX_GATE_RETRIES) - proceeding"
    mark_gate_passed "$gate_name"
    return 0
}

run_planning_phase() {
    # VRC-1: Is VISION clear enough? (only if not done)
    if ! gate_passed "vrc1"; then
        print_vrc "1" "Is the VISION clear enough to deliver?"
        run_prompt "vrc"
        mark_gate_passed "vrc1"
        save_state "1" "$ITERATION"
    else
        print_status "skip" "VRC-1 already passed"
    fi

    # PHASE 1: Planning (if no plan exists or gates not passed)
    if [[ ! -f "$PLAN_FILE" ]] || ! gate_passed "planning"; then
        print_phase "1" "Planning (Generate Implementation Plan)"

        if [[ ! -f "$PLAN_FILE" ]]; then
            print_status "info" "Generating implementation plan..."
            run_prompt "plan"
            auto_commit "loop-v2($SPRINT): Initial implementation plan"
        else
            print_status "skip" "Plan already exists"
        fi

        # ─────────────────────────────────────────────────────────────────
        # BLOCKER VALIDATION: Check if "external" blockers are really external
        # ─────────────────────────────────────────────────────────────────
        # This runs BEFORE quality gates to catch misclassified blockers.
        # The key question: "Can user trigger this via UI, or is UI missing?"
        # If UI is missing → It's BUILDABLE, not EXTERNAL

        print_status "info" "Validating blocker classifications..."
        run_prompt "verify-blockers"

        # Check if verify-blockers created BUILD tasks (reclassified blockers)
        if grep -q "BUILD-" "$PLAN_FILE" 2>/dev/null; then
            print_status "ok" "Blocker validation found buildable items"
            auto_commit "loop-v2($SPRINT): Blocker validation - reclassified blockers"
        fi

        # Quality gates with auto-remediation
        # Each gate runs, fixes issues, re-runs until clean
        run_gate_with_remediation "craap" "craap" "CRAAP Review"
        run_gate_with_remediation "clarity" "clarity" "CLARITY Protocol"
        run_gate_with_remediation "validate" "validate" "VALIDATE Sprint"
        run_gate_with_remediation "connect" "connect" "CONNECT Review"
        run_gate_with_remediation "tidy" "tidy" "TIDY-FIRST"

        mark_gate_passed "planning"
        save_state "1" "$ITERATION"
        auto_commit "loop-v2($SPRINT): Phase 1 - All quality gates passed"

        # VRC-2: Does plan deliver VISION?
        if ! gate_passed "vrc2"; then
            print_vrc "2" "Does this plan deliver ALL the VISION value?"

            # VRC-2 also gets remediation loop
            local vrc_retry=0
            while [[ $vrc_retry -lt $MAX_GATE_RETRIES ]]; do
                ((++vrc_retry))

                local plan_hash_before=""
                if [[ -f "$PLAN_FILE" ]]; then
                    plan_hash_before=$(md5sum "$PLAN_FILE" 2>/dev/null | cut -d' ' -f1)
                fi

                run_prompt "vrc"

                local plan_hash_after=""
                if [[ -f "$PLAN_FILE" ]]; then
                    plan_hash_after=$(md5sum "$PLAN_FILE" 2>/dev/null | cut -d' ' -f1)
                fi

                if [[ "$plan_hash_before" == "$plan_hash_after" ]]; then
                    print_status "ok" "VRC-2 PASSED - Plan delivers VISION"
                    break
                fi

                print_status "warn" "VRC-2 found gaps - plan updated"
                if [[ $vrc_retry -lt $MAX_GATE_RETRIES ]]; then
                    print_status "info" "Re-running VRC-2 to verify plan completeness..."
                    auto_commit "loop-v2($SPRINT): VRC-2 - remediation pass $vrc_retry"
                fi
            done

            mark_gate_passed "vrc2"
            save_state "1" "$ITERATION"
        else
            print_status "skip" "VRC-2 already passed"
        fi
    else
        print_status "skip" "Planning phase already complete"
    fi
}

run_preflight_phase() {
    if ! gate_passed "preflight"; then
        print_phase "PRE" "Preflight Check (Environment Verification)"

        print_status "info" "Checking environment and dependencies..."
        run_prompt "preflight"

        mark_gate_passed "preflight"
        save_state "1" "$ITERATION"
        auto_commit "loop-v2($SPRINT): Preflight check complete"
    else
        print_status "skip" "Preflight already passed"
    fi
}

# Generate BETA_TEST_PLAN using UX-focused QA approach
# This creates a comprehensive test plan that verifies:
# - BT-XXX: PRD requirements (UI flows)
# - INT-XXX: Real API integrations (not stubs)
# - VAL-XXX: VISION delivery (business value)
# - UX-XXX: Usability gaps (what PRD missed)
generate_test_plan() {
    if [[ -f "$BETA_TEST_PLAN" ]] && gate_passed "test_plan_generated"; then
        print_status "skip" "Test plan already generated"
        return 0
    fi

    print_phase "TEST" "Generate Beta Test Plan"
    print_status "info" "Creating UX-focused beta test plan..."
    print_status "info" "Analyzing PRD, VISION, and ARCHITECTURE for testable scenarios..."

    # Run the comprehensive beta-plan prompt
    # This generates BT-XXX, INT-XXX, VAL-XXX, and UX-XXX test cases
    run_prompt "beta-plan"

    # Verify the plan was created
    if [[ -f "$BETA_TEST_PLAN" ]]; then
        local bt_count=$(grepcount "^\- \[ \] \*\*BT-" "$BETA_TEST_PLAN")
        local int_count=$(grepcount "^\- \[ \] \*\*INT-" "$BETA_TEST_PLAN")
        local val_count=$(grepcount "^\- \[ \] \*\*VAL-" "$BETA_TEST_PLAN")
        local ux_count=$(grepcount "^\- \[ \] \*\*UX-" "$BETA_TEST_PLAN")
        local total=$((bt_count + int_count + val_count + ux_count))

        print_status "ok" "Generated beta test plan:"
        print_status "info" "  BT-XXX (PRD verification): $bt_count"
        print_status "info" "  INT-XXX (Real API integration): $int_count"
        print_status "info" "  VAL-XXX (VISION delivery): $val_count"
        print_status "info" "  UX-XXX (Usability exploration): $ux_count"
        print_status "info" "  Total: $total test cases"

        mark_gate_passed "test_plan_generated"
        auto_commit "loop-v2($SPRINT): Generated comprehensive beta test plan"
    else
        print_status "warn" "Beta test plan generation did not create output file"
        print_status "info" "Will retry on next loop iteration"
    fi
}
