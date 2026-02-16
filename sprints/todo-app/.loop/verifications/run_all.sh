#!/usr/bin/env bash
# Master verification runner - executes all verification scripts
# Usage: ./run_all.sh [category]
#   category: unit, integration, value, or all (default)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CATEGORY="${1:-all}"

echo "======================================================================"
echo "TODO APP - VERIFICATION SUITE"
echo "======================================================================"
echo "Category: $CATEGORY"
echo "Directory: $SCRIPT_DIR"
echo "======================================================================"
echo ""

# Track results
TOTAL=0
PASSED=0
FAILED=0
FAILED_TESTS=()

run_verification() {
  local script="$1"
  local name="$(basename "$script")"

  echo "----------------------------------------------------------------------"
  echo "Running: $name"
  echo "----------------------------------------------------------------------"

  TOTAL=$((TOTAL + 1))

  if [[ "$script" == *.py ]]; then
    if python "$script"; then
      PASSED=$((PASSED + 1))
      echo "✓ $name PASSED"
    else
      FAILED=$((FAILED + 1))
      FAILED_TESTS+=("$name")
      echo "✗ $name FAILED"
    fi
  elif [[ "$script" == *.sh ]]; then
    if bash "$script"; then
      PASSED=$((PASSED + 1))
      echo "✓ $name PASSED"
    else
      FAILED=$((FAILED + 1))
      FAILED_TESTS+=("$name")
      echo "✗ $name FAILED"
    fi
  fi

  echo ""
}

# Determine which tests to run
case "$CATEGORY" in
  unit)
    echo "Running UNIT tests (fast regression checks)..."
    echo ""
    for script in "$SCRIPT_DIR"/unit_*.sh "$SCRIPT_DIR"/unit_*.py; do
      [[ -f "$script" ]] && run_verification "$script"
    done
    ;;

  integration)
    echo "Running INTEGRATION tests (component interactions)..."
    echo ""
    for script in "$SCRIPT_DIR"/integration_*.sh "$SCRIPT_DIR"/integration_*.py; do
      [[ -f "$script" ]] && run_verification "$script"
    done
    ;;

  value)
    echo "Running VALUE tests (user outcome verification)..."
    echo ""
    for script in "$SCRIPT_DIR"/value_*.sh "$SCRIPT_DIR"/value_*.py; do
      [[ -f "$script" ]] && run_verification "$script"
    done
    ;;

  all)
    echo "Running ALL tests (unit → integration → value)..."
    echo ""

    # Unit tests first (fast)
    for script in "$SCRIPT_DIR"/unit_*.sh "$SCRIPT_DIR"/unit_*.py; do
      [[ -f "$script" ]] && run_verification "$script"
    done

    # Integration tests
    for script in "$SCRIPT_DIR"/integration_*.sh "$SCRIPT_DIR"/integration_*.py; do
      [[ -f "$script" ]] && run_verification "$script"
    done

    # Value tests last (most comprehensive)
    for script in "$SCRIPT_DIR"/value_*.sh "$SCRIPT_DIR"/value_*.py; do
      [[ -f "$script" ]] && run_verification "$script"
    done
    ;;

  *)
    echo "✗ ERROR: Unknown category '$CATEGORY'"
    echo "Usage: $0 [unit|integration|value|all]"
    exit 1
    ;;
esac

# Summary
echo "======================================================================"
echo "VERIFICATION SUMMARY"
echo "======================================================================"
echo "Total:  $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "======================================================================"

if [[ $FAILED -gt 0 ]]; then
  echo ""
  echo "Failed tests:"
  for test in "${FAILED_TESTS[@]}"; do
    echo "  - $test"
  done
  echo ""
  echo "✗ VERIFICATION FAILED"
  exit 1
else
  echo ""
  echo "✓ ALL VERIFICATIONS PASSED"
  echo ""
  echo "The todo app delivers its promised value:"
  echo "  • Zero-setup HTML file opens in any browser"
  echo "  • Add, complete, delete tasks work correctly"
  echo "  • Filter by status shows correct subsets"
  echo "  • Tasks persist across page reloads"
  echo "  • Mobile responsive (375px viewport)"
  echo ""
  exit 0
fi
