#!/usr/bin/env bash
# Verification: CSS files exist and contain required styles for sections
# PRD Reference: Task 1.3 (app.css), Task 1.4 (templates.css)
# Vision Goal: Professional visual styling
# Category: integration
set -euo pipefail

echo "=== Integration: CSS Styles Applied ==="

cd "$(dirname "$0")/../.."

FAIL=0

# Check app.css exists and has builder UI styles
if [[ ! -f "public/css/app.css" ]]; then
  echo "FAIL: app.css does not exist"
  exit 1
fi

# Check for key app.css patterns
if ! grep -q "template-card" public/css/app.css; then
  echo "FAIL: app.css missing template-card styles"
  FAIL=1
fi

if ! grep -q "preview-panel" public/css/app.css; then
  echo "FAIL: app.css missing preview-panel styles"
  FAIL=1
fi

# Check templates.css exists and has section styles
if [[ ! -f "public/css/templates.css" ]]; then
  echo "FAIL: templates.css does not exist"
  exit 1
fi

# Check for all 5 section type styles
SECTION_TYPES=("hero" "features" "testimonials" "pricing" "cta")

for section in "${SECTION_TYPES[@]}"; do
  if ! grep -q "section-${section}" public/css/templates.css; then
    echo "FAIL: templates.css missing styles for section-${section}"
    FAIL=1
  fi
done

# Check for accent color CSS variable usage
if ! grep -q "accent-color" public/css/templates.css; then
  echo "FAIL: templates.css does not use --accent-color CSS variable"
  FAIL=1
fi

if [[ $FAIL -eq 0 ]]; then
  echo "PASS: CSS files contain required styles"
  exit 0
else
  exit 1
fi
