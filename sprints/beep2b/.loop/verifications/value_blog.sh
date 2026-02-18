#!/usr/bin/env bash
# Verification: Blog system delivers content marketing value (listing, pagination, categories, posts)
# PRD Reference: §3.6 (Blog Listing), §3.7 (Blog Post), §3.8 (Category Filter)
# Vision Goal: "Blog posts paginate at 10 per page with prev/next navigation and category filtering works"
#              "Portable Text content renders correctly with proper typography on blog post pages"
# Category: value

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERIF_DIR="$(dirname "${BASH_SOURCE[0]}")"

echo "=== Value: Blog System (Listing, Pagination, Categories, Posts) ==="
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
  ".loop/verifications/playwright/value_blog.spec.ts" \
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
