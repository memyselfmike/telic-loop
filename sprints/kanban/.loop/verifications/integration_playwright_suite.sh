#!/usr/bin/env bash
# Verification: Run the complete Playwright end-to-end test suite
# PRD Reference: Section 11 (Testing), Section 12 (Acceptance Criteria #3)
# Vision Goal: All value promises verified end-to-end in a real browser
# Category: integration

set -uo pipefail

echo "=== Integration: Playwright E2E Test Suite ==="
echo ""

TESTS_DIR="sprints/kanban/tests"

if [[ ! -d "$TESTS_DIR" ]]; then
  echo "FAIL: Tests directory $TESTS_DIR does not exist"
  exit 1
fi

if [[ ! -f "$TESTS_DIR/conftest.py" ]]; then
  echo "FAIL: $TESTS_DIR/conftest.py does not exist"
  exit 1
fi

# Count test files
TEST_FILES=$(find "$TESTS_DIR" -name "test_*.py" | wc -l)
echo "Test files found: $TEST_FILES"

if [[ "$TEST_FILES" -eq 0 ]]; then
  echo "FAIL: No test files found in $TESTS_DIR"
  exit 1
fi

echo "Running: pytest $TESTS_DIR -v --tb=short"
echo "---"

python -m pytest "$TESTS_DIR" -v --tb=short 2>&1
EXIT_CODE=$?

echo "---"
if [[ "$EXIT_CODE" -eq 0 ]]; then
  echo "PASS: All Playwright tests passed"
else
  echo "FAIL: One or more Playwright tests failed (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
