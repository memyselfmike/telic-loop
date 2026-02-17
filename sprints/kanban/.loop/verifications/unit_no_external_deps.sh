#!/usr/bin/env bash
# Verification: index.html has zero external dependencies (no CDN links, no external scripts)
# PRD Reference: Section 1 (Deliverable) — "No external dependencies"
# Vision Goal: "Works offline in any modern browser" — zero CDN links
# Category: unit

set -euo pipefail

echo "=== Unit: No External Dependencies ==="

INDEX="sprints/kanban/index.html"

if [[ ! -f "$INDEX" ]]; then
  echo "FAIL: $INDEX does not exist"
  exit 1
fi

FAIL=0

# Check for external script tags (src=http/https)
EXTERNAL_SCRIPTS=$(grep -iE '<script[^>]+src=["'"'"'][https?://' "$INDEX" 2>/dev/null || true)
if [[ -n "$EXTERNAL_SCRIPTS" ]]; then
  echo "FAIL: Found external <script> tags:"
  echo "$EXTERNAL_SCRIPTS"
  FAIL=1
fi

# Check for external link/stylesheet tags
EXTERNAL_LINKS=$(grep -iE '<link[^>]+href=["'"'"'][https?://' "$INDEX" 2>/dev/null || true)
if [[ -n "$EXTERNAL_LINKS" ]]; then
  echo "FAIL: Found external <link> tags:"
  echo "$EXTERNAL_LINKS"
  FAIL=1
fi

# Check for @import with http/https URLs in CSS
EXTERNAL_IMPORTS=$(grep -iE "@import\s+[\"']https?://" "$INDEX" 2>/dev/null || true)
if [[ -n "$EXTERNAL_IMPORTS" ]]; then
  echo "FAIL: Found external CSS @import:"
  echo "$EXTERNAL_IMPORTS"
  FAIL=1
fi

# Check for fetch() calls to external URLs
EXTERNAL_FETCH=$(grep -iE "fetch\([\"']https?://" "$INDEX" 2>/dev/null || true)
if [[ -n "$EXTERNAL_FETCH" ]]; then
  echo "FAIL: Found external fetch() calls:"
  echo "$EXTERNAL_FETCH"
  FAIL=1
fi

if [[ "$FAIL" -eq 0 ]]; then
  echo "PASS: No external dependencies found in index.html"
  exit 0
else
  exit 1
fi
