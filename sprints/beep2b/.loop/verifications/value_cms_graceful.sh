#!/usr/bin/env bash
# Verification: CMS unavailability does not crash the site
# PRD Reference: §1.3 (graceful handling), §2.3 (empty results, not throws)
# Vision Goal: "When CMS data is unavailable, pages show graceful placeholder content
#               instead of crashing"
# Category: value

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERIF_DIR="$(dirname "${BASH_SOURCE[0]}")"

echo "=== Value: CMS Graceful Degradation ==="
echo ""

# Setup Playwright if needed
if [[ ! -d "$SPRINT_DIR/node_modules/@playwright" ]]; then
  bash "$VERIF_DIR/setup_playwright.sh"
fi

cd "$SPRINT_DIR"
# Intentionally use empty/placeholder Sanity credentials to simulate CMS unavailability
export SANITY_PROJECT_ID="placeholder"
export SANITY_DATASET="production"
export SANITY_API_TOKEN="placeholder"
export PUBLIC_FORM_ACTION="https://example.com/form"

npx playwright test \
  --config="$SPRINT_DIR/playwright.config.ts" \
  ".loop/verifications/playwright/value_cms_graceful.spec.ts" \
  --reporter=list \
  2>&1

EXIT_CODE=$?
if [[ $EXIT_CODE -eq 0 ]]; then
  echo ""
  echo "RESULT: PASS"
  exit 0
else
  echo ""
  echo "RESULT: FAIL"
  exit 1
fi
