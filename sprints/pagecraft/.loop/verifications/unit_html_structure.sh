#!/usr/bin/env bash
# Verification: index.html has all required regions and script/link tags
# PRD Reference: Architecture - index.html app shell, Task 1.2
# Vision Goal: Builder UI foundation
# Category: unit
set -euo pipefail

echo "=== Unit: HTML Structure ==="

cd "$(dirname "$0")/../.."

HTML_FILE="public/index.html"
FAIL=0

# Check for required IDs
REQUIRED_IDS=(
  "template-selector"
  "workspace"
  "preview-panel"
  "template-cards"
  "section-list"
  "preview-content"
)

for id in "${REQUIRED_IDS[@]}"; do
  if ! grep -q "id=\"$id\"" "$HTML_FILE"; then
    echo "FAIL: Missing required element with id=\"$id\""
    FAIL=1
  fi
done

# Check for required script tags
REQUIRED_SCRIPTS=(
  "app.js"
  "templates.js"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
  if ! grep -q "src=\"js/$script\"" "$HTML_FILE" && ! grep -q "src=\".*/$script\"" "$HTML_FILE"; then
    echo "FAIL: Missing required script tag for $script"
    FAIL=1
  fi
done

# Check for required CSS links
REQUIRED_CSS=(
  "app.css"
  "templates.css"
)

for css in "${REQUIRED_CSS[@]}"; do
  if ! grep -q "href=\"css/$css\"" "$HTML_FILE" && ! grep -q "href=\".*/$css\"" "$HTML_FILE"; then
    echo "FAIL: Missing required CSS link for $css"
    FAIL=1
  fi
done

if [[ $FAIL -eq 0 ]]; then
  echo "PASS: HTML structure has all required elements"
  exit 0
else
  exit 1
fi
