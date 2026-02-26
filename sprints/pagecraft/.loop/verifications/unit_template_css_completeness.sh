#!/usr/bin/env bash
# Verification: templates.css defines styles for all 5 section types
# PRD Reference: Task 1.4 - styles for hero, features, testimonials, pricing, CTA
# Vision Goal: Professional landing page sections
# Category: unit
set -euo pipefail

echo "=== Template CSS Completeness Verification ==="

cd "$(dirname "$0")/../.."

CSS_FILE="public/css/templates.css"

if [ ! -f "$CSS_FILE" ]; then
  echo "FAIL: templates.css not found"
  exit 1
fi

echo "Checking for section type styles..."

# Check for each section type
section_types=("hero" "features" "testimonials" "pricing" "cta")
missing_sections=()

for section in "${section_types[@]}"; do
  count=$(grep -c -E "\.section-${section}|\.${section}-section" "$CSS_FILE" || echo "0")

  if [ "$count" -eq 0 ]; then
    echo "  ✗ Missing styles for section type: $section"
    missing_sections+=("$section")
  else
    echo "  ✓ Found $count style rules for $section"
  fi
done

if [ ${#missing_sections[@]} -gt 0 ]; then
  echo ""
  echo "FAIL: Missing styles for section types: ${missing_sections[*]}"
  echo ""
  echo "Current section classes in templates.css:"
  grep -E '^\.section-|^\.[a-z]+-section' "$CSS_FILE" || echo "  (none found)"
  exit 1
fi

# Check for responsive design (mobile stacking)
has_responsive=$(grep -c -E '@media|max-width|min-width|grid-template-columns.*auto|flex.*wrap' "$CSS_FILE" || echo "0")

if [ "$has_responsive" -gt 0 ]; then
  echo "  ✓ Responsive design rules found ($has_responsive)"
else
  echo "  WARN: No responsive design rules found - sections may not stack on mobile"
fi

# Check for grid layouts (features, testimonials, pricing should be 3-column grids)
has_grid=$(grep -c -E 'grid-template-columns.*1fr.*1fr|display.*grid' "$CSS_FILE" || echo "0")

if [ "$has_grid" -gt 0 ]; then
  echo "  ✓ Grid layouts defined ($has_grid rules)"
else
  echo "  WARN: No grid layouts found - features/testimonials/pricing should use grids"
fi

echo "PASS: All 5 section types have CSS styles defined"
exit 0
