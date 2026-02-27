#!/usr/bin/env bash
# Verification: Notes CRUD API unit tests via Jest (regression coverage for Epic 1)
# PRD Reference: GET/POST/DELETE /api/notes endpoints
# Vision Goal: Notes CRUD functionality remains working
# Category: unit
set -euo pipefail

echo "=== Notes API Unit Tests (Regression) ==="

cd "$(dirname "$0")/../.."

# Run Jest tests for notes API only
# Jest handles its own test isolation and parallelization
npm test -- tests/api.test.js --silent 2>&1

exit_code=$?

if [ $exit_code -eq 0 ]; then
  echo "PASS: All notes API unit tests passed"
  exit 0
else
  echo "FAIL: Notes API unit tests failed"
  exit 1
fi
