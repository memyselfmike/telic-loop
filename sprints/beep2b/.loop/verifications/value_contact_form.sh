#!/usr/bin/env bash
# Verification: Contact form validates fields client-side and submits with success/error feedback
# PRD Reference: §3.5 (Contact), §3 (Page Specifications)
# Vision Goal: "Contact form validates fields client-side and submits to configurable endpoint
#               with success/error feedback"
# Category: value

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERIF_DIR="$(dirname "${BASH_SOURCE[0]}")"

echo "=== Value: Contact Form (Validation + Submission Feedback) ==="
echo ""

# Setup Playwright if needed
if [[ ! -d "$SPRINT_DIR/node_modules/@playwright" ]]; then
  bash "$VERIF_DIR/setup_playwright.sh"
fi

cd "$SPRINT_DIR"
export SANITY_PROJECT_ID="${SANITY_PROJECT_ID:-placeholder}"
export SANITY_DATASET="${SANITY_DATASET:-production}"
export SANITY_API_TOKEN="${SANITY_API_TOKEN:-placeholder}"
export PUBLIC_FORM_ACTION="${PUBLIC_FORM_ACTION:-https://example.com/form}"

npx playwright test \
  --config="$SPRINT_DIR/playwright.config.ts" \
  ".loop/verifications/playwright/value_contact_form.spec.ts" \
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
