#!/bin/bash
# Loop V2 Metrics - Counting functions and value checks
#
# Dependencies: lib/ui.sh (for print_status), lib/prompts.sh (for run_prompt)
# Requires: PLAN_FILE, VALUE_CHECKLIST, BLOCKERS_FILE

# ═══════════════════════════════════════════════════════════════════════════
# BLOCKER VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════

# Check if there are any blockers that need verification
# Returns 0 if blockers exist, 1 if no blockers
has_blockers_to_verify() {
    if [[ ! -f "$VALUE_CHECKLIST" ]]; then
        return 1
    fi

    # Check if there are any BLOCKED items
    local blocked_count
    blocked_count=$(grep -c "BLOCKED" "$VALUE_CHECKLIST" 2>/dev/null) || blocked_count=0
    [[ "$blocked_count" -gt 0 ]]
}

# Verify blockers and update VALUE_CHECKLIST if any are resolved
# Blockers can be resolved by:
#   - Credential configuration (.env changes)
#   - Browser login sessions (if VISION requires browser automation)
#   - Code fixes (architecture gaps)
#   - File creation (missing configs)
#   - Any other user action
#
# This runs the verify-blockers prompt which checks actual system state
verify_blockers() {
    if ! has_blockers_to_verify; then
        return 0  # No blockers to verify
    fi

    print_status "info" "Verifying blockers (credentials, auth, architecture gaps)..."

    # Store hash before verification
    local checklist_hash_before=""
    if [[ -f "$VALUE_CHECKLIST" ]]; then
        checklist_hash_before=$(md5sum "$VALUE_CHECKLIST" 2>/dev/null | cut -d' ' -f1 || md5 -q "$VALUE_CHECKLIST" 2>/dev/null || echo "")
    fi

    # Run the verify-blockers prompt
    run_prompt "verify-blockers"

    # Check if changes were made
    local checklist_hash_after=""
    if [[ -f "$VALUE_CHECKLIST" ]]; then
        checklist_hash_after=$(md5sum "$VALUE_CHECKLIST" 2>/dev/null | cut -d' ' -f1 || md5 -q "$VALUE_CHECKLIST" 2>/dev/null || echo "")
    fi

    if [[ "$checklist_hash_before" != "$checklist_hash_after" ]]; then
        print_status "ok" "Blockers updated - some were resolved"
        return 0
    else
        print_status "info" "All blockers still active"
        return 0
    fi
}

check_all_value_delivered() {
    if [[ ! -f "$VALUE_CHECKLIST" ]]; then
        return 1
    fi

    # Count unchecked value items that are NOT blocked
    # Pattern: "| [ ] |" but NOT on lines containing "BLOCKED" or "[B]"
    local unchecked=$(grep -E "\| \[ \] \|" "$VALUE_CHECKLIST" 2>/dev/null | grep -v "BLOCKED\|^\[B\]" | wc -l)

    if [[ "$unchecked" -gt 0 ]]; then
        return 1
    fi

    return 0
}

has_uncomplete_tasks() {
    if [[ ! -f "$PLAN_FILE" ]]; then
        return 1
    fi

    # Count unchecked tasks that are NOT blocked [B]
    # Pattern: "- [ ]" but NOT "- [B]"
    local unchecked
    unchecked=$(grep -c "^- \[ \]" "$PLAN_FILE" 2>/dev/null) || unchecked=0

    if [[ "$unchecked" -gt 0 ]]; then
        return 0
    fi

    return 1
}

count_tasks() {
    if [[ ! -f "$PLAN_FILE" ]]; then
        echo "0/0"
        return
    fi

    local total done
    total=$(grep -c "^- \[.\]" "$PLAN_FILE" 2>/dev/null) || total=0
    done=$(grep -c "^- \[x\]" "$PLAN_FILE" 2>/dev/null) || done=0
    echo "$done/$total"
}

count_blocked_tasks() {
    if [[ ! -f "$PLAN_FILE" ]]; then
        echo "0"
        return
    fi

    local count
    count=$(grep -c "^- \[B\]" "$PLAN_FILE" 2>/dev/null) || count=0
    echo "$count"
}

has_external_blockers() {
    if [[ ! -f "$BLOCKERS_FILE" ]]; then
        return 1
    fi

    # Check if there are active external blockers
    local blockers
    blockers=$(grep -c "| B[0-9]" "$BLOCKERS_FILE" 2>/dev/null) || blockers=0
    [[ "$blockers" -gt 0 ]]
}

check_deliverable_value() {
    # Check if we can deliver value (all non-blocked items complete)
    if [[ ! -f "$VALUE_CHECKLIST" ]]; then
        return 1
    fi

    # Count unchecked items that are NOT blocked
    local unchecked=$(grep -E "\| \[ \] \|" "$VALUE_CHECKLIST" 2>/dev/null | grep -v "BLOCKED" | wc -l)

    if [[ "$unchecked" -gt 0 ]]; then
        return 1
    fi

    return 0
}
