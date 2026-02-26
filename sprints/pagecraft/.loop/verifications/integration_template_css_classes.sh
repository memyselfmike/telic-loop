#!/usr/bin/env bash
# Verification: Template-specific CSS classes are defined in templates.css
# PRD Reference: CE-85-11, EVAL-1 - template-specific visual treatments
# Vision Goal: Each template produces visually distinct landing page
# Category: integration
set -euo pipefail

echo "=== Template CSS Classes Verification ==="

cd "$(dirname "$0")/../.."

CSS_FILE="public/css/templates.css"

if [ ! -f "$CSS_FILE" ]; then
  echo "FAIL: templates.css not found at $CSS_FILE"
  exit 1
fi

echo "Checking for template-specific CSS classes..."

# Look for template-specific class definitions
# Expected patterns: .template-saas, .template-event, .template-portfolio
# OR: .saas, .event, .portfolio with template-specific rules

has_saas=$(grep -c -E '\.(template-)?saas' "$CSS_FILE" || echo "0")
has_event=$(grep -c -E '\.(template-)?event' "$CSS_FILE" || echo "0")
has_portfolio=$(grep -c -E '\.(template-)?portfolio' "$CSS_FILE" || echo "0")

echo "  SaaS-specific CSS rules: $has_saas"
echo "  Event-specific CSS rules: $has_event"
echo "  Portfolio-specific CSS rules: $has_portfolio"

if [ "$has_saas" -eq 0 ] || [ "$has_event" -eq 0 ] || [ "$has_portfolio" -eq 0 ]; then
  echo "FAIL: Missing template-specific CSS classes"
  echo "Expected .template-saas, .template-event, .template-portfolio or similar"
  echo ""
  echo "Current templates.css section headings:"
  grep -E '^/\*|^\.section|^\.[a-z-]+\s*\{' "$CSS_FILE" | head -20
  exit 1
fi

# Check for distinct visual properties per template
# Look for different colors, layouts, or backgrounds

saas_snippet=$(grep -A 10 -E '\.(template-)?saas' "$CSS_FILE" | head -15)
event_snippet=$(grep -A 10 -E '\.(template-)?event' "$CSS_FILE" | head -15)

if [ "$saas_snippet" == "$event_snippet" ]; then
  echo "FAIL: SaaS and Event CSS rules are identical - no visual distinction"
  exit 1
fi

echo "PASS: Template-specific CSS classes exist with distinct styling"
exit 0
