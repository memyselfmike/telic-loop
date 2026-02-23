#!/usr/bin/env bash
# Verification Runner: Execute all verification scripts in order
# This script runs Unit → Integration → Value tests to verify LinkVault delivers promised value

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

echo "═══════════════════════════════════════════════════════"
echo "  LinkVault Verification Suite"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "This test suite verifies that LinkVault delivers on all"
echo "promises made in the Vision and PRD documents."
echo ""

# Check if server is running
echo "Checking server health..."
if ! curl -sf http://localhost:3000/health > /dev/null 2>&1; then
  echo "❌ ERROR: Server is not running on http://localhost:3000"
  echo "Please start the server with: npm start"
  exit 1
fi
echo "✓ Server is running"
echo ""

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
FAILED_SCRIPTS=()

run_test() {
  local category=$1
  local script=$2
  local description=$3

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "[$category] $description"
  echo "Script: $script"
  echo ""

  TOTAL_TESTS=$((TOTAL_TESTS + 1))

  if node "$SCRIPT_DIR/$script" 2>&1; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo ""
    echo "✅ PASSED: $script"
  else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    FAILED_SCRIPTS+=("$script")
    echo ""
    echo "❌ FAILED: $script"
  fi

  echo ""
}

echo "═══════════════════════════════════════════════════════"
echo "  PHASE 1: UNIT TESTS"
echo "  Fast tests of individual components"
echo "═══════════════════════════════════════════════════════"
echo ""

run_test "UNIT" "unit_storage_module.js" "Storage module creates data directory and JSON file"
run_test "UNIT" "unit_api_validation.js" "API validates input correctly"
run_test "UNIT" "unit_stats_calculation.js" "Stats calculations are accurate"
run_test "UNIT" "unit_tag_color_consistency.js" "Tag colors are consistent and deterministic"

echo "═══════════════════════════════════════════════════════"
echo "  PHASE 2: INTEGRATION TESTS"
echo "  Components working together"
echo "═══════════════════════════════════════════════════════"
echo ""

run_test "INTEGRATION" "integration_health_check.js" "Health check endpoint works"
run_test "INTEGRATION" "integration_api_crud.js" "CRUD operations work end-to-end"
run_test "INTEGRATION" "integration_persistence.js" "Data persists across restarts"
run_test "INTEGRATION" "integration_stats_edge_cases.js" "Stats API handles edge cases"
run_test "INTEGRATION" "integration_navigation.js" "Navigation between pages works"

echo "═══════════════════════════════════════════════════════"
echo "  PHASE 3: VALUE DELIVERY TESTS"
echo "  User gets the promised outcomes"
echo "═══════════════════════════════════════════════════════"
echo ""

run_test "VALUE" "value_bookmark_creation.js" "User can create bookmarks instantly"
run_test "VALUE" "value_tag_filtering.js" "User can filter by tags"
run_test "VALUE" "value_delete_bookmark.js" "User can delete bookmarks"
run_test "VALUE" "value_responsive_structure.js" "Responsive design structure supports mobile and desktop"
run_test "VALUE" "value_navigation_flow.js" "User can navigate freely between pages"
run_test "VALUE" "value_dashboard_stats.js" "User views dashboard stats and insights"
run_test "VALUE" "value_complete_workflow.js" "Complete user workflow delivers value"
run_test "VALUE" "value_full_epic_flow.js" "Full Epic 1 + Epic 2 experience"
run_test "VALUE" "value_all_proofs.js" "All 10 value proofs from Sprint Context"

echo "═══════════════════════════════════════════════════════"
echo "  VERIFICATION SUITE SUMMARY"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
  echo "✅ ALL TESTS PASSED"
  echo ""
  echo "🎉 LinkVault delivers all promised value!"
  echo ""
  echo "Vision validation:"
  echo "  ✓ Users can save links with tags instantly"
  echo "  ✓ Cards display in responsive grid (3 cols → 1 col)"
  echo "  ✓ Tag filtering works with visual feedback"
  echo "  ✓ Data persists across browser refreshes"
  echo "  ✓ Dashboard shows collection insights"
  echo "  ✓ Navigation between pages is seamless"
  echo ""
  exit 0
else
  echo "❌ SOME TESTS FAILED"
  echo ""
  echo "Failed scripts:"
  for script in "${FAILED_SCRIPTS[@]}"; do
    echo "  - $script"
  done
  echo ""
  exit 1
fi
