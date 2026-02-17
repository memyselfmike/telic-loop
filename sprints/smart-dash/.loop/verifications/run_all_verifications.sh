#!/usr/bin/env bash
# Master verification runner - runs all verification scripts in order
# Category: meta
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "  Smart Dashboard - Complete Verification Suite"
echo "════════════════════════════════════════════════════════════════"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Track results
PASSED=0
FAILED=0
SKIPPED=0
FAILED_TESTS=()

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

run_verification() {
    local script="$1"
    local name=$(basename "$script" .sh)

    echo -e "${BLUE}Running: $name${NC}"
    echo "────────────────────────────────────────────────────────────────"

    if bash "$script"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo -e "${YELLOW}⊘ SKIPPED${NC}"
            ((SKIPPED++))
        else
            echo -e "${RED}✗ FAILED${NC}"
            ((FAILED++))
            FAILED_TESTS+=("$name")
        fi
    fi
    echo ""
}

echo "═══ UNIT VERIFICATIONS ═══"
echo ""

for script in "$SCRIPT_DIR"/unit_*.sh; do
    [ -f "$script" ] && run_verification "$script"
done

echo ""
echo "═══ INTEGRATION VERIFICATIONS ═══"
echo ""

for script in "$SCRIPT_DIR"/integration_*.sh; do
    [ -f "$script" ] && run_verification "$script"
done

echo ""
echo "═══ VALUE DELIVERY VERIFICATIONS ═══"
echo ""

for script in "$SCRIPT_DIR"/value_*.sh; do
    [ -f "$script" ] && run_verification "$script"
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  VERIFICATION SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "  ${GREEN}Passed:${NC}  $PASSED"
echo -e "  ${RED}Failed:${NC}  $FAILED"
echo -e "  ${YELLOW}Skipped:${NC} $SKIPPED"
echo -e "  Total:   $((PASSED + FAILED + SKIPPED))"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo ""
    exit 1
else
    echo -e "${GREEN}All verifications passed!${NC}"
    echo ""
    exit 0
fi
