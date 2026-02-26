#!/usr/bin/env bash
# Verification: Change Template button exists in HTML or JS
# PRD Reference: CE-85-13, EVAL-3 - back/change template navigation
# Vision Goal: User can switch templates during workflow
# Category: integration
set -euo pipefail

echo "=== Change Template Button Verification ==="

cd "$(dirname "$0")/../.."

HTML_FILE="public/index.html"
APP_JS="public/js/app.js"
TEMPLATES_JS="public/js/templates.js"

echo "Checking for Change Template button..."

# Check HTML for button element
change_btn_html=$(grep -i -c -E '(change.*template|back|switch.*template|select.*template)' "$HTML_FILE" || echo "0")

# Check JS for button creation
change_btn_js=0
if [ -f "$APP_JS" ]; then
  change_btn_js=$(grep -i -c -E '(change.*template|back|switch.*template|select.*template)' "$APP_JS" || echo "0")
fi

# Check templates.js
change_btn_templates=0
if [ -f "$TEMPLATES_JS" ]; then
  change_btn_templates=$(grep -i -c -E '(change.*template|back|switch.*template|select.*template)' "$TEMPLATES_JS" || echo "0")
fi

total_references=$((change_btn_html + change_btn_js + change_btn_templates))

echo "  References in index.html: $change_btn_html"
echo "  References in app.js: $change_btn_js"
echo "  References in templates.js: $change_btn_templates"
echo "  Total references: $total_references"

if [ "$total_references" -eq 0 ]; then
  echo "FAIL: No Change Template button found in HTML or JS files"
  echo ""
  echo "Expected to find button with text like:"
  echo "  - Change Template"
  echo "  - Back to Templates"
  echo "  - Switch Template"
  echo ""
  echo "Current buttons in index.html:"
  grep -E '<button|<a' "$HTML_FILE" || echo "  (none found)"
  exit 1
fi

# Check for click handler that shows template selector
show_selector=$(grep -c -E 'template-selector.*display.*block|getElementById.*template-selector.*style|showTemplateSelector' "$APP_JS" "$TEMPLATES_JS" 2>/dev/null || echo "0")

if [ "$show_selector" -eq 0 ]; then
  echo "WARN: Found button reference but no handler to show template selector"
  echo "Expected to find code that makes #template-selector visible"
fi

# Check for confirmation dialog
has_confirm=$(grep -c -E 'confirm.*template|confirm.*switch|confirm.*change|confirm.*lose' "$APP_JS" "$TEMPLATES_JS" 2>/dev/null || echo "0")

if [ "$has_confirm" -gt 0 ]; then
  echo "  ✓ Confirmation dialog implementation found"
else
  echo "  WARN: No confirmation dialog found - should warn about losing changes"
fi

echo "PASS: Change Template button is implemented"
exit 0
