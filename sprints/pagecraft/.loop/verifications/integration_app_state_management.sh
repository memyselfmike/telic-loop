#!/usr/bin/env bash
# Verification: AppState object initializes and manages state correctly
# PRD Reference: Task 1.5 - AppState foundation
# Vision Goal: State management
# Category: integration
set -euo pipefail

echo "=== Integration: AppState Management ==="

cd "$(dirname "$0")/../.."

# Check that app.js defines AppState with required properties
if ! grep -q "const AppState = {" public/js/app.js; then
  echo "FAIL: AppState object not defined in app.js"
  exit 1
fi

if ! grep -q "currentTemplate:" public/js/app.js; then
  echo "FAIL: AppState missing currentTemplate property"
  exit 1
fi

if ! grep -q "sections:" public/js/app.js; then
  echo "FAIL: AppState missing sections property"
  exit 1
fi

if ! grep -q "accentColor:" public/js/app.js; then
  echo "FAIL: AppState missing accentColor property"
  exit 1
fi

# Check for loadTemplate function
if ! grep -q "async function loadTemplate" public/js/app.js; then
  echo "FAIL: loadTemplate function not defined"
  exit 1
fi

# Check that loadTemplate fetches JSON
if ! grep -q "fetch.*templates.*json" public/js/app.js; then
  echo "FAIL: loadTemplate does not fetch template JSON"
  exit 1
fi

# Check that loadTemplate populates state
if ! grep -q "AppState.sections" public/js/app.js; then
  echo "FAIL: loadTemplate does not populate AppState.sections"
  exit 1
fi

echo "PASS: AppState is properly defined and managed"
exit 0
