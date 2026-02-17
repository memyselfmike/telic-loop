#!/usr/bin/env bash
# Verification: index.html file size is under 30KB
# PRD Reference: Section 1 (Deliverable), Section 12 (Acceptance Criteria #2)
# Vision Goal: "Single HTML file, under 30KB"
# Category: unit

set -euo pipefail

echo "=== Unit: File Size Check ==="

INDEX="sprints/kanban/index.html"

if [[ ! -f "$INDEX" ]]; then
  echo "FAIL: $INDEX does not exist"
  exit 1
fi

SIZE=$(wc -c < "$INDEX")
LIMIT=30720  # 30KB = 30 * 1024

echo "File: $INDEX"
echo "Size: ${SIZE} bytes (limit: ${LIMIT} bytes / 30KB)"

if [[ "$SIZE" -le "$LIMIT" ]]; then
  echo "PASS: File size ${SIZE} bytes is within the 30KB budget"
  exit 0
else
  OVER=$((SIZE - LIMIT))
  echo "FAIL: File size ${SIZE} bytes exceeds 30KB by ${OVER} bytes"
  echo "  PRD requires: under 30KB (${LIMIT} bytes)"
  echo "  Current size: ${SIZE} bytes"
  echo "  Overage: ${OVER} bytes"
  exit 1
fi
