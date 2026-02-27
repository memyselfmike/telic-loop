#!/usr/bin/env bash
# Verification: Stats API unit tests via Jest
# PRD Reference: GET /api/stats endpoint
# Vision Goal: Stats page showing total notes, average body length, and newest/oldest note dates
# Category: unit
set -euo pipefail

echo "=== Stats API Unit Tests ==="

cd "$(dirname "$0")/../.."

# Run Jest tests for stats API only
# Jest handles its own test isolation and parallelization
npm test -- tests/stats.test.js --silent 2>&1

exit_code=$?

if [ $exit_code -eq 0 ]; then
  echo "PASS: All stats API unit tests passed"
  exit 0
else
  echo "FAIL: Stats API unit tests failed"
  exit 1
fi
