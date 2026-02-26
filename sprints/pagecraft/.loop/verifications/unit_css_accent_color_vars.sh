#!/usr/bin/env bash
# Verification: CSS uses --accent-color variable correctly
# PRD Reference: F3 Inline Editing - accent color applies to buttons, headings, borders
# Vision Goal: User picks accent color and all elements update
# Category: unit
set -euo pipefail

echo "=== CSS Accent Color Variable Verification ==="

cd "$(dirname "$0")/../.."

TEMPLATES_CSS="public/css/templates.css"

if [ ! -f "$TEMPLATES_CSS" ]; then
  echo "FAIL: templates.css not found"
  exit 1
fi

echo "Checking for --accent-color CSS variable usage..."

# Count uses of var(--accent-color)
accent_var_count=$(grep -c 'var(--accent-color)' "$TEMPLATES_CSS" || echo "0")

echo "  Found $accent_var_count uses of var(--accent-color)"

if [ "$accent_var_count" -eq 0 ]; then
  echo "FAIL: No uses of var(--accent-color) found in templates.css"
  echo "Expected it to be used for buttons, headings, and borders"
  exit 1
fi

# Check specific element types use accent color
has_button_accent=$(grep -E 'button.*var\(--accent-color\)|background.*var\(--accent-color\)' "$TEMPLATES_CSS" || echo "")
has_heading_accent=$(grep -E 'h[1-6].*var\(--accent-color\)|color.*var\(--accent-color\)' "$TEMPLATES_CSS" || echo "")
has_border_accent=$(grep -E 'border.*var\(--accent-color\)' "$TEMPLATES_CSS" || echo "")

elements_using_accent=0

if [ -n "$has_button_accent" ]; then
  echo "  ✓ Buttons use --accent-color"
  elements_using_accent=$((elements_using_accent + 1))
else
  echo "  WARN: No button accent color usage found"
fi

if [ -n "$has_heading_accent" ]; then
  echo "  ✓ Headings use --accent-color"
  elements_using_accent=$((elements_using_accent + 1))
else
  echo "  WARN: No heading accent color usage found"
fi

if [ -n "$has_border_accent" ]; then
  echo "  ✓ Borders use --accent-color"
  elements_using_accent=$((elements_using_accent + 1))
fi

if [ "$elements_using_accent" -lt 2 ]; then
  echo "FAIL: --accent-color should be used on multiple element types (buttons, headings, borders)"
  exit 1
fi

echo "PASS: CSS properly uses --accent-color variable"
exit 0
