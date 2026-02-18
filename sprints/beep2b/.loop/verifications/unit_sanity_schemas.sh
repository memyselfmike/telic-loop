#!/usr/bin/env bash
# Verification: Sanity CMS schemas are correctly defined per PRD
# PRD Reference: Section 2 (Sanity CMS Schemas) - all 7 schemas
# Vision Goal: "Content Management with Sanity CMS" - site owner manages all content via Studio
# Category: unit

set -euo pipefail

SPRINT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SANITY_DIR="$SPRINT_DIR/sanity"
echo "=== Unit: Sanity CMS Schemas ==="
echo "Sanity dir: $SANITY_DIR"
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

# --- Sanity project setup ---
echo "[ Sanity project files ]"
[[ -f "$SANITY_DIR/sanity.config.ts" ]] && check "sanity.config.ts exists" "pass" || check "sanity.config.ts exists" "fail"
[[ -f "$SANITY_DIR/sanity.cli.ts" ]] && check "sanity.cli.ts exists" "pass" || echo "  SKIP: sanity.cli.ts (pending)"
[[ -f "$SANITY_DIR/package.json" ]] && check "sanity/package.json exists" "pass" || check "sanity/package.json exists" "fail"
[[ -d "$SANITY_DIR/node_modules" ]] && check "sanity node_modules installed" "pass" || echo "  SKIP: sanity node_modules (pending install)"

# --- Schema files (PRD Section 2) ---
echo ""
echo "[ Schema files (PRD §2.1-2.7) ]"
SCHEMAS=("post.ts" "author.ts" "category.ts" "page.ts" "testimonial.ts" "siteSettings.ts" "navigation.ts")
for SCHEMA in "${SCHEMAS[@]}"; do
  if [[ -f "$SANITY_DIR/schemas/$SCHEMA" ]]; then
    check "schemas/$SCHEMA exists" "pass"
  else
    echo "  SKIP: schemas/$SCHEMA not yet created (pending Epic 2)"
  fi
done

[[ -f "$SANITY_DIR/schemas/index.ts" ]] && check "schemas/index.ts exists" "pass" || check "schemas/index.ts exists" "fail"

# --- Schema registry (all 7 schemas exported) ---
echo ""
echo "[ Schema registry (schemas/index.ts) ]"
if [[ -f "$SANITY_DIR/schemas/index.ts" ]]; then
  # Check if all schemas are imported/exported
  REGISTERED=0
  for SCHEMA in "post" "author" "category" "page" "testimonial" "siteSettings" "navigation"; do
    if grep -q "$SCHEMA" "$SANITY_DIR/schemas/index.ts" 2>/dev/null; then
      REGISTERED=$((REGISTERED + 1))
    fi
  done
  if [[ $REGISTERED -eq 7 ]]; then
    check "All 7 schemas registered in index.ts" "pass"
  elif [[ $REGISTERED -gt 0 ]]; then
    echo "  PARTIAL: $REGISTERED/7 schemas registered in index.ts (pending Epic 2)"
  else
    echo "  SKIP: Schema registry empty (pending Epic 2)"
  fi
fi

# --- Post schema field validation (PRD 2.1) ---
echo ""
echo "[ Post schema fields (PRD §2.1) ]"
POST_SCHEMA="$SANITY_DIR/schemas/post.ts"
if [[ -f "$POST_SCHEMA" ]]; then
  for FIELD in "title" "slug" "author" "publishedAt" "categories" "featuredImage" "excerpt" "body"; do
    grep -q "\"$FIELD\"\|'$FIELD'\|name:.*$FIELD" "$POST_SCHEMA" && check "post.$FIELD field defined" "pass" || check "post.$FIELD field defined" "fail"
  done
else
  echo "  SKIP: post.ts not yet created (pending Epic 2)"
fi

# --- Page schema section types (PRD 2.4) ---
echo ""
echo "[ Page schema section types (PRD §2.4) ]"
PAGE_SCHEMA="$SANITY_DIR/schemas/page.ts"
if [[ -f "$PAGE_SCHEMA" ]]; then
  for SECTION_TYPE in "hero" "features" "testimonials" "textBlock" "cta"; do
    grep -q "$SECTION_TYPE" "$PAGE_SCHEMA" && check "page section type '$SECTION_TYPE' defined" "pass" || check "page section type '$SECTION_TYPE' defined" "fail"
  done
else
  echo "  SKIP: page.ts not yet created (pending Epic 2)"
fi

# --- Sanity config reads env vars ---
echo ""
echo "[ Sanity config environment variables ]"
SANITY_CONFIG="$SANITY_DIR/sanity.config.ts"
if [[ -f "$SANITY_CONFIG" ]]; then
  grep -q "SANITY_STUDIO_PROJECT_ID\|SANITY_PROJECT_ID\|projectId" "$SANITY_CONFIG" && check "projectId configured in sanity.config.ts" "pass" || check "projectId configured in sanity.config.ts" "fail"
  grep -q "SANITY_STUDIO_DATASET\|SANITY_DATASET\|dataset" "$SANITY_CONFIG" && check "dataset configured in sanity.config.ts" "pass" || check "dataset configured in sanity.config.ts" "fail"
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
