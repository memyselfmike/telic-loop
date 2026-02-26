#!/usr/bin/env bash
# Verification: Template cards include preview/thumbnail HTML elements
# PRD Reference: CE-85-12, EVAL-2 - visual thumbnail previews
# Vision Goal: Templates displayed as visual cards with live previews
# Category: integration
set -euo pipefail

echo "=== Template Card Preview Elements Verification ==="

cd "$(dirname "$0")/../.."

JS_FILE="public/js/templates.js"
CSS_FILE="public/css/app.css"

if [ ! -f "$JS_FILE" ]; then
  echo "FAIL: templates.js not found"
  exit 1
fi

echo "Checking templates.js for preview thumbnail generation..."

# Look for preview/thumbnail creation in template card rendering
has_preview_element=$(grep -c -E '(preview|thumbnail|card-preview|template-preview)' "$JS_FILE" || echo "0")

if [ "$has_preview_element" -eq 0 ]; then
  echo "FAIL: No preview/thumbnail elements found in templates.js"
  echo "Expected to find preview/thumbnail creation in renderTemplateCards function"
  echo ""
  echo "Template card rendering code:"
  grep -A 20 'renderTemplateCards\|template-card' "$JS_FILE" | head -30
  exit 1
fi

echo "  Found $has_preview_element preview-related references in templates.js"

# Check CSS for preview/thumbnail styling
if [ -f "$CSS_FILE" ]; then
  has_preview_css=$(grep -c -E '\.(preview|thumbnail|card-preview|template-preview)' "$CSS_FILE" || echo "0")
  echo "  Found $has_preview_css preview-related CSS rules in app.css"

  if [ "$has_preview_css" -eq 0 ]; then
    echo "WARN: No preview/thumbnail CSS styling found - thumbnails may not be styled"
  fi
fi

# Check for scale transform or thumbnail sizing
has_scale=$(grep -c -E '(transform.*scale|width.*px|height.*px)' "$JS_FILE" "$CSS_FILE" || echo "0")
echo "  Found $has_scale sizing/scale references (for thumbnail rendering)"

echo "PASS: Template preview elements are implemented in templates.js"
exit 0
