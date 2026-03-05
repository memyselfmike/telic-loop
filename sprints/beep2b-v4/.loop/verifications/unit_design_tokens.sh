#!/bin/bash
# Unit test: CSS design tokens are defined

set -e

echo "=== Design Tokens Test ==="

# Get homepage HTML which includes styles
HOME_HTML=$(curl -s http://localhost:4321 || echo "")

# Check for key design tokens (use grep -F for fixed strings to avoid option interpretation)
REQUIRED_TOKENS=(
  "color-bg-primary"
  "color-text-primary"
  "color-accent-primary"
  "space-4"
  "radius-lg"
  "shadow-md"
  "transition-base"
  "text-xl"
  "font-bold"
  "z-sticky"
)

for token in "${REQUIRED_TOKENS[@]}"; do
  if ! echo "$HOME_HTML" | grep -F "$token" > /dev/null; then
    echo "FAIL: Design token --$token not found"
    exit 1
  fi
done

echo "✓ All required design tokens defined"

# Check dark theme background color
if ! echo "$HOME_HTML" | grep -q "#0a0a0f"; then
  echo "FAIL: Dark theme background color not found"
  exit 1
fi

echo "✓ Dark theme colors present"

echo ""
echo "=== PASS: Design token system complete ==="
exit 0
