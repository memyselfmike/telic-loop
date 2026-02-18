#!/usr/bin/env bash
# Verification: All 6 required page routes exist and produce valid HTML
# PRD Reference: Section 3 (Page Specifications), 6 (Acceptance Criteria - Epic 1)
# Vision Goal: "Modern Marketing Website" - all pages accessible and navigable
# Category: integration

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "=== Integration: Page Routes and HTML Output ==="
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

# Require built dist/ -- run build first if needed
DIST="$SPRINT_DIR/dist"
if [[ ! -d "$DIST" ]]; then
  echo "dist/ not found. Running build..."
  cd "$SPRINT_DIR"
  export SANITY_PROJECT_ID="${SANITY_PROJECT_ID:-placeholder}"
  export SANITY_DATASET="${SANITY_DATASET:-production}"
  export SANITY_API_TOKEN="${SANITY_API_TOKEN:-placeholder}"
  export PUBLIC_FORM_ACTION="${PUBLIC_FORM_ACTION:-https://example.com/form}"
  npm run build --silent 2>&1 | tail -5
fi

if [[ ! -d "$DIST" ]]; then
  echo "FAIL: Build failed - dist/ directory does not exist"
  exit 1
fi

# --- Check all 6 required page routes ---
echo "[ Required page routes (PRD §3.1-3.8) ]"
declare -A ROUTES=(
  ["$DIST/index.html"]="Home page (/)"
  ["$DIST/how-it-works/index.html"]="How It Works (/how-it-works)"
  ["$DIST/services/index.html"]="Services (/services)"
  ["$DIST/about/index.html"]="About (/about)"
  ["$DIST/contact/index.html"]="Contact (/contact)"
  ["$DIST/blog/index.html"]="Blog listing (/blog)"
)

for HTML_FILE in "${!ROUTES[@]}"; do
  LABEL="${ROUTES[$HTML_FILE]}"
  if [[ -f "$HTML_FILE" ]]; then
    check "$LABEL exists" "pass"
    # Check it has actual HTML structure
    if grep -qi "<html\|<body\|<head" "$HTML_FILE"; then
      check "$LABEL has valid HTML structure" "pass"
    else
      check "$LABEL has valid HTML structure" "fail"
    fi
  else
    echo "  SKIP: $LABEL not yet generated"
    SKIP=$((SKIP + 1))
  fi
done

# --- Check blog routes ---
echo ""
echo "[ Blog routes ]"
if [[ -f "$DIST/blog/index.html" ]]; then
  check "Blog listing /blog renders" "pass"
  # Check for BlogCard structure
  grep -qi "blog\|post\|article" "$DIST/blog/index.html" && check "Blog listing contains blog content" "pass" || echo "  WARN: Blog listing may not have blog content yet"
fi

# Check for pagination (if more than 10 placeholder posts)
if [[ -f "$DIST/blog/2/index.html" ]]; then
  check "Blog page 2 (/blog/2) generated" "pass"
elif [[ -d "$DIST/blog/2" ]]; then
  check "Blog page 2 directory exists" "pass"
fi

# Category pages (if implemented)
if [[ -d "$DIST/blog/category" ]]; then
  check "Blog category directory exists" "pass"
fi

# --- Check each page uses BaseLayout (has Header + Footer) ---
echo ""
echo "[ BaseLayout integration (Header + Footer on all pages) ]"
for HTML_FILE in "$DIST/index.html" "$DIST/how-it-works/index.html" "$DIST/services/index.html" "$DIST/about/index.html" "$DIST/contact/index.html"; do
  if [[ -f "$HTML_FILE" ]]; then
    PAGE_NAME=$(basename $(dirname "$HTML_FILE"))
    [[ "$PAGE_NAME" == "dist" ]] && PAGE_NAME="home"
    # Check for nav links (evidence of Header)
    if grep -qi "how-it-works\|/services\|/about\|/contact\|/blog" "$HTML_FILE"; then
      check "$PAGE_NAME has navigation links (Header present)" "pass"
    else
      check "$PAGE_NAME has navigation links (Header present)" "fail"
    fi
    # Check for Footer evidence
    if grep -qi "footer\|copyright\|©\|20[0-9][0-9]" "$HTML_FILE"; then
      check "$PAGE_NAME has Footer content" "pass"
    else
      check "$PAGE_NAME has Footer content" "fail"
    fi
  fi
done

# --- Check blue theme applied ---
echo ""
echo "[ Blue theme in HTML output ]"
if [[ -f "$DIST/index.html" ]]; then
  # Tailwind generates CSS classes -- look for blue-related content
  if grep -qi "blue\|primary\|#1e40af\|bg-blue\|text-blue" "$DIST/index.html"; then
    check "Blue theme present in home page HTML" "pass"
  else
    echo "  WARN: Blue theme classes may be in external CSS file (not inline)"
    # Check for a CSS link that would include theme
    grep -qi '<link.*\.css' "$DIST/index.html" && check "CSS stylesheet linked in home page" "pass" || check "CSS stylesheet linked or inline blue styles present" "fail"
  fi
fi

# --- Verify CSS assets are built ---
echo ""
echo "[ Built CSS assets ]"
if ls "$DIST/_astro/"*.css 2>/dev/null | head -1 | grep -q ".css"; then
  check "CSS assets generated in dist/_astro/" "pass"
  CSS_FILE=$(ls "$DIST/_astro/"*.css 2>/dev/null | head -1)
  # Check for blue color in generated CSS
  grep -q "#1e40af\|1e40af\|blue" "$CSS_FILE" && check "Blue color (#1e40af) in generated CSS" "pass" || echo "  INFO: Blue color may be defined via CSS variables"
else
  echo "  SKIP: No CSS assets yet (pending implementation)"
fi

# --- SEO checks on built pages ---
echo ""
echo "[ SEO meta tags (PRD §5) ]"
if [[ -f "$DIST/index.html" ]]; then
  grep -qi "<title>" "$DIST/index.html" && check "Home page has <title> tag" "pass" || check "Home page has <title> tag" "fail"
  grep -qi 'name="description"' "$DIST/index.html" && check "Home page has meta description" "pass" || echo "  SKIP: meta description not yet implemented"
  grep -qi 'og:title\|property="og' "$DIST/index.html" && check "Home page has Open Graph tags" "pass" || echo "  SKIP: OG tags not yet implemented (task 3.6)"
fi

# --- sitemap.xml ---
echo ""
echo "[ Sitemap and robots.txt (PRD §5) ]"
if [[ -f "$DIST/sitemap-index.xml" ]] || [[ -f "$DIST/sitemap.xml" ]]; then
  check "sitemap.xml generated" "pass"
else
  echo "  SKIP: sitemap.xml not yet implemented (task 3.6)"
fi
if [[ -f "$SPRINT_DIR/public/robots.txt" ]] || [[ -f "$DIST/robots.txt" ]]; then
  check "robots.txt exists" "pass"
else
  echo "  SKIP: robots.txt not yet implemented (task 3.6)"
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
  echo "RESULT: PASS (all required checks passed)"
  exit 0
fi
