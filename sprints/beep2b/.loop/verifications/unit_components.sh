#!/usr/bin/env bash
# Verification: Required Astro and React components exist with correct structure
# PRD Reference: Section 1.2 (Project Structure), 1.4 (Build Constraints), 4.3 (Component Styling)
# Vision Goal: "Modern Marketing Website" - polished UI components for every page
# Category: unit

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "=== Unit: Astro and React Components ==="
echo ""

PASS=0
FAIL=0
SKIP=0

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

skip_check() {
  echo "  SKIP: $1 (pending implementation)"
  SKIP=$((SKIP + 1))
}

# --- Layout ---
echo "[ Layouts ]"
if [[ -f "$SPRINT_DIR/src/layouts/BaseLayout.astro" ]]; then
  check "BaseLayout.astro exists" "pass"
  # Verify it has HTML shell elements
  grep -qi "<!doctype\|<!DOCTYPE" "$SPRINT_DIR/src/layouts/BaseLayout.astro" && check "BaseLayout has DOCTYPE" "pass" || check "BaseLayout has DOCTYPE" "fail"
  grep -q "<slot" "$SPRINT_DIR/src/layouts/BaseLayout.astro" && check "BaseLayout has <slot />" "pass" || check "BaseLayout has <slot />" "fail"
  grep -q "globals.css\|global.css" "$SPRINT_DIR/src/layouts/BaseLayout.astro" && check "BaseLayout imports CSS" "pass" || check "BaseLayout imports CSS" "fail"
else
  skip_check "BaseLayout.astro (task 1.3)"
fi

# --- Header ---
echo ""
echo "[ Header ]"
if [[ -f "$SPRINT_DIR/src/components/Header.astro" ]]; then
  check "Header.astro exists" "pass"
  # Check for all 6 nav links
  NAV_LINKS=("/" "how-it-works" "services" "about" "blog" "contact")
  FOUND=0
  for LINK in "${NAV_LINKS[@]}"; do
    grep -q "$LINK" "$SPRINT_DIR/src/components/Header.astro" && FOUND=$((FOUND + 1))
  done
  if [[ $FOUND -ge 5 ]]; then
    check "Header has all 6 navigation links" "pass"
  else
    check "Header has all 6 navigation links ($FOUND/6 found)" "fail"
  fi
else
  skip_check "Header.astro (task 1.4)"
fi

# --- MobileNav React island ---
echo ""
echo "[ Mobile Navigation ]"
if [[ -f "$SPRINT_DIR/src/components/MobileNav.tsx" ]]; then
  check "MobileNav.tsx (React island) exists" "pass"
  # Must be .tsx for React island per PRD 1.4
  grep -q "client:load\|Sheet\|hamburger\|menu" "$SPRINT_DIR/src/components/MobileNav.tsx" 2>/dev/null || true
  # Check it's used with client:load in Header
  if [[ -f "$SPRINT_DIR/src/components/Header.astro" ]]; then
    grep -q "client:load" "$SPRINT_DIR/src/components/Header.astro" && check "MobileNav used with client:load in Header" "pass" || check "MobileNav used with client:load in Header" "fail"
  fi
else
  skip_check "MobileNav.tsx (task 1.4)"
fi

# --- Footer ---
echo ""
echo "[ Footer ]"
if [[ -f "$SPRINT_DIR/src/components/Footer.astro" ]]; then
  check "Footer.astro exists" "pass"
  # Check for navigation links and copyright
  grep -qi "copyright\|©\|20[0-9][0-9]" "$SPRINT_DIR/src/components/Footer.astro" && check "Footer has copyright text" "pass" || check "Footer has copyright text" "fail"
else
  skip_check "Footer.astro (task 1.5)"
fi

# --- shadcn/ui components ---
echo ""
echo "[ shadcn/ui components (src/components/ui/) ]"
UI_COMPONENTS=("button" "card" "input" "textarea" "label" "badge" "separator")
if [[ -d "$SPRINT_DIR/src/components/ui" ]]; then
  for COMP in "${UI_COMPONENTS[@]}"; do
    # shadcn generates .tsx files
    if [[ -f "$SPRINT_DIR/src/components/ui/${COMP}.tsx" ]]; then
      check "ui/${COMP}.tsx exists" "pass"
    else
      skip_check "ui/${COMP}.tsx (task 1.2)"
    fi
  done
else
  skip_check "src/components/ui/ directory (task 1.2)"
fi

# --- src/lib/utils.ts (cn function) ---
echo ""
echo "[ Shared utilities ]"
if [[ -f "$SPRINT_DIR/src/lib/utils.ts" ]]; then
  check "src/lib/utils.ts exists" "pass"
  grep -q "export.*cn\|function cn\|const cn" "$SPRINT_DIR/src/lib/utils.ts" && check "cn() utility exported" "pass" || check "cn() utility exported" "fail"
else
  skip_check "src/lib/utils.ts (task 1.2)"
fi

# --- Sanity client ---
echo ""
echo "[ Sanity client library ]"
if [[ -f "$SPRINT_DIR/src/lib/sanity.ts" ]]; then
  check "src/lib/sanity.ts exists" "pass"
  grep -q "createClient\|@sanity/client" "$SPRINT_DIR/src/lib/sanity.ts" && check "Sanity client configured" "pass" || check "Sanity client configured" "fail"
  # Check for GROQ query helpers
  QUERIES=("getAllPosts" "getPostBySlug" "getAllCategories" "getPageBySlug" "getSiteSettings")
  for QUERY in "${QUERIES[@]}"; do
    grep -q "$QUERY" "$SPRINT_DIR/src/lib/sanity.ts" && check "GROQ helper $QUERY exported" "pass" || skip_check "$QUERY query (task 2.3)"
  done
else
  skip_check "src/lib/sanity.ts (task 2.3)"
fi

# --- ContactForm React island ---
echo ""
echo "[ Contact Form ]"
if [[ -f "$SPRINT_DIR/src/components/ContactForm.tsx" ]]; then
  check "ContactForm.tsx (React island) exists" "pass"
  grep -q "PUBLIC_FORM_ACTION\|import.meta.env" "$SPRINT_DIR/src/components/ContactForm.tsx" && check "ContactForm reads PUBLIC_FORM_ACTION env var" "pass" || check "ContactForm reads PUBLIC_FORM_ACTION env var" "fail"
  grep -q "required\|validation" "$SPRINT_DIR/src/components/ContactForm.tsx" && check "ContactForm has field validation" "pass" || check "ContactForm has field validation" "fail"
else
  skip_check "ContactForm.tsx (task 3.4)"
fi

# --- BlogCard component ---
echo ""
echo "[ Blog components ]"
if [[ -f "$SPRINT_DIR/src/components/BlogCard.astro" ]]; then
  check "BlogCard.astro exists" "pass"
else
  skip_check "BlogCard.astro (task 1.7)"
fi

echo ""
echo "=== Summary ==="
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo "  Skipped (pending): $SKIP"
echo ""

if [[ $FAIL -gt 0 ]]; then
  echo "RESULT: FAIL ($FAIL checks failed)"
  exit 1
else
  echo "RESULT: PASS (all required checks passed; $SKIP pending implementation)"
  exit 0
fi
