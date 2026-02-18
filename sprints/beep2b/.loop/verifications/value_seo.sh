#!/usr/bin/env bash
# Verification: Every page has SEO meta tags, OG tags, canonical URL; sitemap.xml and robots.txt generated
# PRD Reference: §5 (SEO and Meta)
# Vision Goal: "Every page has SEO meta tags, OG tags, canonical URL, and the site generates
#               sitemap.xml and robots.txt"
# Category: value

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERIF_DIR="$(dirname "${BASH_SOURCE[0]}")"

echo "=== Value: SEO Meta Tags, OG Tags, Sitemap, robots.txt ==="
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
  ".loop/verifications/playwright/value_seo.spec.ts" \
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
