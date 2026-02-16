#!/bin/bash
# Loop V2 State Management - For resumability
#
# Dependencies: lib/config.sh (for colors)
# Requires: STATE_FILE to be set before use

# State values (global - intentionally shared)
STATE_PHASE=""
STATE_ITERATION=0
STATE_GATES_PASSED=""

load_state() {
    if [[ -f "$STATE_FILE" ]]; then
        STATE_PHASE=$(grep "^phase:" "$STATE_FILE" 2>/dev/null | cut -d: -f2 | tr -d ' ' || echo "")
        STATE_ITERATION=$(grep "^iteration:" "$STATE_FILE" 2>/dev/null | cut -d: -f2 | tr -d ' ' || echo "0")
        STATE_GATES_PASSED=$(grep "^gates_passed:" "$STATE_FILE" 2>/dev/null | cut -d: -f2 | tr -d ' ' || echo "")
        return 0
    fi
    return 1
}

save_state() {
    local phase="$1"
    local iteration="$2"
    local gates="${3:-$STATE_GATES_PASSED}"

    cat > "$STATE_FILE" << EOF
# Loop V2 State - DO NOT EDIT MANUALLY
# This file tracks progress for resumability

phase: $phase
iteration: $iteration
gates_passed: $gates
last_updated: $(date -Iseconds)
sprint: $SPRINT
EOF
}

gate_passed() {
    local gate="$1"
    [[ "$STATE_GATES_PASSED" == *"$gate"* ]]
}

mark_gate_passed() {
    local gate="$1"
    if ! gate_passed "$gate"; then
        STATE_GATES_PASSED="${STATE_GATES_PASSED}${gate},"
    fi
}

# Invalidate a specific gate (forces re-check on next iteration)
invalidate_gate() {
    local gate="$1"
    STATE_GATES_PASSED=$(echo "$STATE_GATES_PASSED" | sed "s/${gate},//g")
}

# Invalidate all quality gates (craap, clarity, validate, connect, tidy)
# Use when major changes require re-verification
invalidate_quality_gates() {
    local reason="${1:-unspecified}"
    print_status "warn" "Invalidating quality gates: $reason"
    STATE_GATES_PASSED=$(echo "$STATE_GATES_PASSED" | sed 's/craap,//g; s/clarity,//g; s/validate,//g; s/connect,//g; s/tidy,//g')
}

# Invalidate all planning-related gates
# Use when new tasks are created that require re-planning
invalidate_all_planning() {
    local reason="${1:-unspecified}"
    print_status "warn" "Invalidating all planning gates: $reason"
    STATE_GATES_PASSED=$(echo "$STATE_GATES_PASSED" | sed 's/planning,//g; s/vrc1,//g; s/vrc2,//g; s/craap,//g; s/clarity,//g; s/validate,//g; s/connect,//g; s/tidy,//g; s/preflight,//g')
}

# Reset all gates (complete restart)
reset_all_gates() {
    print_status "warn" "Resetting ALL gates - full re-verification required"
    STATE_GATES_PASSED=""
}
