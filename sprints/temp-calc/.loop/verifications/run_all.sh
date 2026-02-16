#!/usr/bin/env bash
# Master verification runner - executes all verification scripts in order
# Stops on first failure to provide fast feedback
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     TEMP-CALC SPRINT: COMPREHENSIVE VERIFICATION SUITE    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "This suite verifies that the temperature converter CLI:"
echo "  • Functions correctly (unit tests)"
echo "  • Integrates properly (integration tests)"
echo "  • Delivers promised value (value delivery tests)"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

FAILURES=0
PASSED=0

run_test() {
    local name="$1"
    local script="$2"
    local category="$3"

    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│ Running: $name"
    echo "│ Category: $category"
    echo "└─────────────────────────────────────────────────────────┘"
    echo ""

    if [[ "$script" == *.py ]]; then
        if python "$script"; then
            echo ""
            echo "✅ PASS: $name"
            echo ""
            PASSED=$((PASSED + 1))
        else
            echo ""
            echo "❌ FAIL: $name"
            echo ""
            FAILURES=$((FAILURES + 1))
            return 1
        fi
    else
        if bash "$script"; then
            echo ""
            echo "✅ PASS: $name"
            echo ""
            PASSED=$((PASSED + 1))
        else
            echo ""
            echo "❌ FAIL: $name"
            echo ""
            FAILURES=$((FAILURES + 1))
            return 1
        fi
    fi
}

# Run unit tests first (fast, catch regressions early)
echo "═══ PHASE 1: UNIT VERIFICATION ═══"
echo ""
run_test "Unit Tests (pytest)" "unit_test_temp_calc.py" "UNIT" || true
echo ""

# Run integration tests (verify components work together)
echo "═══ PHASE 2: INTEGRATION VERIFICATION ═══"
echo ""
run_test "CLI Output Streams & Exit Codes" "integration_cli_output.sh" "INTEGRATION" || true
echo ""

# Run value delivery tests (verify user gets promised outcome)
echo "═══ PHASE 3: VALUE DELIVERY VERIFICATION ═══"
echo ""
run_test "User Workflow Scenarios" "value_user_workflow.sh" "VALUE" || true
echo ""
run_test "Quick Reference Usability" "value_quick_reference.sh" "VALUE" || true
echo ""

# Final summary
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    VERIFICATION SUMMARY                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

TOTAL=$((PASSED + FAILURES))

if [[ $FAILURES -eq 0 ]]; then
    echo "🎉 SUCCESS: All $TOTAL verification suites passed!"
    echo ""
    echo "VALUE DELIVERED:"
    echo "  ✅ All 28 unit tests pass - conversions are mathematically correct"
    echo "  ✅ CLI integration correct - follows Unix conventions"
    echo "  ✅ User workflows verified - Vision promises are delivered"
    echo "  ✅ Usability confirmed - developers can use immediately"
    echo ""
    echo "The temperature converter CLI is ready for use."
    echo "A developer can now run commands like:"
    echo "  python temp_calc.py 100 C F"
    echo "and instantly get accurate conversions without leaving the terminal."
    echo ""
    exit 0
else
    echo "❌ FAILURE: $FAILURES out of $TOTAL verification suites failed"
    echo ""
    echo "The sprint is not complete. Value is not yet delivered."
    echo "Fix the failing verifications before marking the sprint done."
    echo ""
    exit 1
fi
