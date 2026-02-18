#!/usr/bin/env bash
# Verification: Blue B2B theme CSS variables are correctly defined
# PRD Reference: Section 4.1 (Color Scheme), 4.2 (Typography)
# Vision Goal: "Professional B2B look" - consistent blue (#1e40af) across all pages
# Category: unit

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "=== Unit: CSS Theme Variables ==="
echo ""

PASS=0
FAIL=0

check() {
  local label="$1"
  local result="$2"
  if [[ "$result" == "pass" ]]; then
    echo "  PASS: $label"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $label"
    FAIL=$((FAIL + 1))
  fi
}

# Find CSS file (globals.css or global.css)
CSS_FILE=""
if [[ -f "$SPRINT_DIR/src/styles/globals.css" ]]; then
  CSS_FILE="$SPRINT_DIR/src/styles/globals.css"
elif [[ -f "$SPRINT_DIR/src/styles/global.css" ]]; then
  CSS_FILE="$SPRINT_DIR/src/styles/global.css"
fi

if [[ -z "$CSS_FILE" ]]; then
  echo "FAIL: No CSS file found at src/styles/globals.css or src/styles/global.css"
  exit 1
fi

echo "CSS file: $CSS_FILE"
echo ""

echo "[ Tailwind v4 directives ]"
grep -q "@import.*tailwindcss" "$CSS_FILE" && check "@import tailwindcss (Tailwind v4)" "pass" || check "@import tailwindcss (Tailwind v4)" "fail"
grep -q "@theme" "$CSS_FILE" && check "@theme block exists" "pass" || check "@theme block exists" "fail"
# Ensure no tailwind.config.mjs (Tailwind v4 uses CSS-based config)
if [[ -f "$SPRINT_DIR/tailwind.config.mjs" ]]; then
  check "No tailwind.config.mjs (Tailwind v4 uses @theme in CSS)" "fail"
else
  check "No tailwind.config.mjs (Tailwind v4 uses @theme in CSS)" "pass"
fi

echo ""
echo "[ Primary blue color palette (PRD 4.1) ]"
grep -q "#1e40af" "$CSS_FILE" && check "Blue-800 primary (#1e40af) defined" "pass" || check "Blue-800 primary (#1e40af) defined" "fail"
grep -q "#3b82f6" "$CSS_FILE" && check "Blue-500 accent (#3b82f6) defined" "pass" || check "Blue-500 accent (#3b82f6) defined" "fail"
grep -q "#2563eb" "$CSS_FILE" && check "Blue-600 hover (#2563eb) defined" "pass" || check "Blue-600 hover (#2563eb) defined" "fail"

echo ""
echo "[ Background and text colors (PRD 4.1) ]"
grep -q "#ffffff" "$CSS_FILE" && check "White background (#ffffff) defined" "pass" || check "White background (#ffffff) defined" "fail"
grep -q "#0f172a\|#1e293b" "$CSS_FILE" && check "Dark text slate-800/900 defined" "pass" || check "Dark text slate-800/900 defined" "fail"

echo ""
echo "[ Font stack (PRD 4.2) ]"
grep -q "system-ui\|ui-sans-serif\|font-sans" "$CSS_FILE" && check "System font stack defined" "pass" || check "System font stack defined" "fail"

echo ""
echo "[ CSS custom properties (root) ]"
grep -q ":root" "$CSS_FILE" && check ":root CSS variables block present" "pass" || check ":root CSS variables block present" "fail"

echo ""
echo "=== Summary ==="
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo ""

if [[ $FAIL -gt 0 ]]; then
  echo "RESULT: FAIL ($FAIL checks failed)"
  exit 1
else
  echo "RESULT: PASS (all $PASS checks passed)"
  exit 0
fi
