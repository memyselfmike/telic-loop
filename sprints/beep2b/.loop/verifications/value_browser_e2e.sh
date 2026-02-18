#!/usr/bin/env bash
# Verification: Full browser E2E test suite (Playwright)
# PRD Reference: All sections - end-to-end value delivery proof
# Vision Goal: All 10 value proofs verified via real browser
# Category: value

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERIF_DIR="$(dirname "${BASH_SOURCE[0]}")"

echo "=== Value: Browser E2E Verification (Playwright) ==="
echo "Sprint dir: $SPRINT_DIR"
echo ""

# --- Check if Playwright is installed ---
if [[ ! -d "$SPRINT_DIR/node_modules/@playwright" ]]; then
  echo "Playwright not installed. Running setup..."
  bash "$VERIF_DIR/setup_playwright.sh"
fi

# --- Check if playwright.config.ts exists ---
if [[ ! -f "$SPRINT_DIR/playwright.config.ts" ]]; then
  echo "playwright.config.ts missing. Running setup..."
  bash "$VERIF_DIR/setup_playwright.sh"
fi

# --- Check if the Astro dev server is reachable (optional - webServer config starts it) ---
echo "[ Checking Astro dev server availability ]"
if curl -s --connect-timeout 5 "http://localhost:4321" > /dev/null 2>&1; then
  echo "  Dev server already running on port 4321"
else
  echo "  Dev server not running - Playwright webServer config will start it"
fi

echo ""
echo "[ Running Playwright E2E tests ]"
echo "  Test files: .loop/verifications/playwright/*.spec.ts"
echo ""

cd "$SPRINT_DIR"

# Set env vars for graceful CMS handling
export SANITY_PROJECT_ID="${SANITY_PROJECT_ID:-placeholder}"
export SANITY_DATASET="${SANITY_DATASET:-production}"
export SANITY_API_TOKEN="${SANITY_API_TOKEN:-placeholder}"
export PUBLIC_FORM_ACTION="${PUBLIC_FORM_ACTION:-https://example.com/form}"

# Run Playwright tests
PLAYWRIGHT_EXIT=0
npx playwright test \
  --config="$SPRINT_DIR/playwright.config.ts" \
  --reporter=list \
  2>&1 || PLAYWRIGHT_EXIT=$?

echo ""
if [[ $PLAYWRIGHT_EXIT -eq 0 ]]; then
  echo "RESULT: PASS - All Playwright E2E tests passed"
  exit 0
else
  echo "RESULT: FAIL - Some Playwright E2E tests failed (exit code: $PLAYWRIGHT_EXIT)"
  echo ""
  echo "To see detailed report: npx playwright show-report"
  exit 1
fi
