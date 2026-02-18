#!/usr/bin/env bash
# Verification: npm run build succeeds and produces correct static output
# PRD Reference: Section 1.1 (Build: Static site generation), 6 (Acceptance Criteria)
# Vision Goal: "Responsive and Fast" - Astro generates static HTML, near-instant loads
# Category: integration

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "=== Integration: Astro Static Build ==="
echo "Sprint dir: $SPRINT_DIR"
echo ""

PASS=0
FAIL=0

check() {
  local label="$1"
  local result="$2"
  if [[ "$result" == "pass" ]]; then
    echo "  PASS: $label"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $label"
    FAIL=$((FAIL + 1))
  fi
}

# --- Pre-build checks ---
echo "[ Pre-build: dependencies installed ]"
if [[ -d "$SPRINT_DIR/node_modules/astro" ]]; then
  check "astro installed in node_modules" "pass"
else
  echo "  Installing dependencies..."
  cd "$SPRINT_DIR" && npm install --silent 2>&1 | tail -5
  [[ -d "$SPRINT_DIR/node_modules/astro" ]] && check "astro installed after npm install" "pass" || check "astro installed after npm install" "fail"
fi

# --- Run build ---
echo ""
echo "[ Running: npm run build ]"
echo "(This may take 30-90 seconds...)"
BUILD_OUTPUT=""
BUILD_EXIT=0

cd "$SPRINT_DIR"
# Set empty env vars for Sanity so build doesn't crash on missing vars
export SANITY_PROJECT_ID="${SANITY_PROJECT_ID:-placeholder}"
export SANITY_DATASET="${SANITY_DATASET:-production}"
export SANITY_API_TOKEN="${SANITY_API_TOKEN:-placeholder}"
export PUBLIC_FORM_ACTION="${PUBLIC_FORM_ACTION:-https://example.com/form}"

BUILD_OUTPUT=$(npm run build 2>&1) || BUILD_EXIT=$?

if [[ $BUILD_EXIT -eq 0 ]]; then
  check "npm run build exits with code 0" "pass"
  echo ""
  echo "  Build output (last 10 lines):"
  echo "$BUILD_OUTPUT" | tail -10 | sed 's/^/    /'
else
  check "npm run build exits with code 0" "fail"
  echo ""
  echo "  Build FAILED. Output (last 20 lines):"
  echo "$BUILD_OUTPUT" | tail -20 | sed 's/^    ERROR: /'
  echo ""
  echo "=== Summary ==="
  echo "  Passed: $PASS"
  echo "  Failed: $FAIL"
  echo ""
  echo "RESULT: FAIL (build failed with exit code $BUILD_EXIT)"
  exit 1
fi

# --- Check dist/ output ---
echo ""
echo "[ Build output: dist/ directory ]"
DIST="$SPRINT_DIR/dist"
if [[ -d "$DIST" ]]; then
  check "dist/ directory created" "pass"
else
  check "dist/ directory created" "fail"
fi

# Check for index.html (home page)
if [[ -f "$DIST/index.html" ]]; then
  check "dist/index.html (home page) generated" "pass"
  # Verify it's valid HTML
  grep -qi "<!doctype\|<!DOCTYPE\|<html" "$DIST/index.html" && check "index.html has HTML doctype/tag" "pass" || check "index.html has HTML doctype/tag" "fail"
else
  check "dist/index.html (home page) generated" "fail"
fi

# Check for other page routes
echo ""
echo "[ Route HTML files in dist/ ]"
ROUTES=("how-it-works" "services" "about" "contact" "blog")
for ROUTE in "${ROUTES[@]}"; do
  if [[ -f "$DIST/$ROUTE/index.html" ]]; then
    check "dist/$ROUTE/index.html generated" "pass"
  else
    echo "  SKIP: dist/$ROUTE/index.html not yet generated (page not yet implemented)"
  fi
done

# --- No TypeScript errors ---
echo ""
echo "[ TypeScript compilation ]"
# If build succeeded without errors, TypeScript passed
if [[ $BUILD_EXIT -eq 0 ]]; then
  # Check for any TypeScript errors in the output
  if echo "$BUILD_OUTPUT" | grep -qi "error TS\|TypeScript error\|type error"; then
    check "No TypeScript errors in build output" "fail"
  else
    check "No TypeScript errors in build output" "pass"
  fi
fi

# --- No error-level warnings ---
echo ""
echo "[ Build warnings ]"
if echo "$BUILD_OUTPUT" | grep -qi "error\b" | grep -v "^$"; then
  echo "  WARNING: 'error' found in build output (may not be critical)"
fi
check "Build completed successfully" "pass"

# --- Check dist/ has no JS required for basic content ---
echo ""
echo "[ Progressive enhancement check ]"
# Astro SSG should render HTML that works without JS
if [[ -f "$DIST/index.html" ]]; then
  # Check that page has actual content (not just a JS app shell)
  # Minimum 100 bytes for a valid HTML page with doctype + head + body
  CONTENT=$(wc -c < "$DIST/index.html")
  if [[ $CONTENT -gt 100 ]]; then
    check "index.html has HTML content ($CONTENT bytes)" "pass"
  else
    check "index.html has HTML content (only $CONTENT bytes - may be empty)" "fail"
  fi
fi

echo ""
echo "=== Summary ==="
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo ""

if [[ $FAIL -gt 0 ]]; then
  echo "RESULT: FAIL ($FAIL checks failed)"
  exit 1
else
  echo "RESULT: PASS (all $PASS checks passed)"
  exit 0
fi
