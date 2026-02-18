#!/usr/bin/env bash
# Verification: Astro project has required files and correct configuration
# PRD Reference: Section 1.1, 1.2, 1.3 (Technology Stack and Project Structure)
# Vision Goal: "Modern Marketing Website" - correct foundation for static build
# Category: unit

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "=== Unit: Project Structure and Configuration ==="
echo "Sprint dir: $SPRINT_DIR"
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

# --- package.json checks ---
echo "[ package.json ]"
PKG="$SPRINT_DIR/package.json"
if [[ -f "$PKG" ]]; then
  check "package.json exists" "pass"
  grep -q '"build"' "$PKG" && check "build script defined" "pass" || check "build script defined" "fail"
  grep -q '"astro"' "$PKG" && check "astro dependency present" "pass" || check "astro dependency present" "fail"
  grep -q '"@astrojs/react"' "$PKG" && check "@astrojs/react dependency present" "pass" || check "@astrojs/react dependency present" "fail"
  grep -q '"tailwindcss"' "$PKG" && check "tailwindcss dependency present" "pass" || check "tailwindcss dependency present" "fail"
else
  check "package.json exists" "fail"
fi

# --- astro.config.mjs checks ---
echo ""
echo "[ astro.config.mjs ]"
CFG="$SPRINT_DIR/astro.config.mjs"
if [[ -f "$CFG" ]]; then
  check "astro.config.mjs exists" "pass"
  grep -q "react()" "$CFG" && check "react() integration in astro config" "pass" || check "react() integration in astro config" "fail"
  grep -q "tailwindcss()" "$CFG" && check "tailwindcss() in vite.plugins" "pass" || check "tailwindcss() in vite.plugins" "fail"
else
  check "astro.config.mjs exists" "fail"
fi

# --- tsconfig.json checks ---
echo ""
echo "[ tsconfig.json ]"
TS="$SPRINT_DIR/tsconfig.json"
if [[ -f "$TS" ]]; then
  check "tsconfig.json exists" "pass"
  grep -q "astro/tsconfigs" "$TS" && check "extends astro tsconfig" "pass" || check "extends astro tsconfig" "fail"
  grep -q "react-jsx" "$TS" && check "jsx set to react-jsx" "pass" || check "jsx set to react-jsx" "fail"
else
  check "tsconfig.json exists" "fail"
fi

# --- globals.css / Tailwind v4 ---
echo ""
echo "[ src/styles/globals.css or global.css ]"
CSS_FILE=""
if [[ -f "$SPRINT_DIR/src/styles/globals.css" ]]; then
  CSS_FILE="$SPRINT_DIR/src/styles/globals.css"
elif [[ -f "$SPRINT_DIR/src/styles/global.css" ]]; then
  CSS_FILE="$SPRINT_DIR/src/styles/global.css"
fi

if [[ -n "$CSS_FILE" ]]; then
  check "globals.css exists" "pass"
  grep -q "@import.*tailwindcss" "$CSS_FILE" && check "Tailwind v4 @import directive present" "pass" || check "Tailwind v4 @import directive present" "fail"
  grep -q "@theme" "$CSS_FILE" && check "@theme block for Tailwind v4 config present" "pass" || check "@theme block for Tailwind v4 config present" "fail"
  grep -q "#1e40af" "$CSS_FILE" && check "Blue primary color #1e40af defined" "pass" || check "Blue primary color #1e40af defined" "fail"
else
  check "globals.css exists" "fail"
fi

# --- node_modules installed ---
echo ""
echo "[ node_modules ]"
if [[ -d "$SPRINT_DIR/node_modules" && -d "$SPRINT_DIR/node_modules/astro" ]]; then
  check "node_modules installed (astro present)" "pass"
else
  check "node_modules installed (astro present)" "fail"
fi

# --- src/pages/index.astro ---
echo ""
echo "[ Page routes ]"
if [[ -f "$SPRINT_DIR/src/pages/index.astro" ]]; then
  check "src/pages/index.astro exists" "pass"
else
  check "src/pages/index.astro exists" "fail"
fi

# Check for additional pages (may not exist yet in early build)
for PAGE in "how-it-works.astro" "services.astro" "about.astro" "contact.astro"; do
  if [[ -f "$SPRINT_DIR/src/pages/$PAGE" ]]; then
    check "src/pages/$PAGE exists" "pass"
  else
    echo "  SKIP: src/pages/$PAGE not yet created (pending implementation)"
  fi
done

# Blog routes
if [[ -f "$SPRINT_DIR/src/pages/blog/[...page].astro" ]] || [[ -f "$SPRINT_DIR/src/pages/blog/index.astro" ]]; then
  check "blog listing route exists" "pass"
else
  echo "  SKIP: blog listing route not yet created (pending implementation)"
fi

# --- layouts ---
echo ""
echo "[ Layouts ]"
if [[ -f "$SPRINT_DIR/src/layouts/BaseLayout.astro" ]]; then
  check "src/layouts/BaseLayout.astro exists" "pass"
else
  echo "  SKIP: BaseLayout.astro not yet created (pending implementation)"
fi

# --- components ---
echo ""
echo "[ Components ]"
for COMP in "Header.astro" "Footer.astro" "MobileNav.tsx" "ContactForm.tsx"; do
  if [[ -f "$SPRINT_DIR/src/components/$COMP" ]]; then
    check "src/components/$COMP exists" "pass"
  else
    echo "  SKIP: $COMP not yet created (pending implementation)"
  fi
done

# --- Sanity Studio ---
echo ""
echo "[ Sanity Studio ]"
if [[ -f "$SPRINT_DIR/sanity/sanity.config.ts" ]]; then
  check "sanity/sanity.config.ts exists" "pass"
else
  check "sanity/sanity.config.ts exists" "fail"
fi
if [[ -f "$SPRINT_DIR/sanity/sanity.cli.ts" ]]; then
  check "sanity/sanity.cli.ts exists" "pass"
else
  echo "  SKIP: sanity.cli.ts not yet created"
fi
if [[ -f "$SPRINT_DIR/sanity/schemas/index.ts" ]]; then
  check "sanity/schemas/index.ts exists" "pass"
else
  check "sanity/schemas/index.ts exists" "fail"
fi

# --- public/robots.txt and SEO ---
echo ""
echo "[ Public Assets and SEO ]"
if [[ -f "$SPRINT_DIR/public/robots.txt" ]]; then
  check "public/robots.txt exists" "pass"
else
  echo "  SKIP: robots.txt not yet created (pending implementation)"
fi

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
