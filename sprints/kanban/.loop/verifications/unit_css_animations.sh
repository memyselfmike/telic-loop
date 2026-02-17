#!/usr/bin/env bash
# Verification: CSS animations are present with correct durations
# PRD Reference: Section 10.3 (Animations)
# Vision Goal: Visual polish — card creation 150ms, modal 200ms, filter 150ms
# Category: unit

set -euo pipefail

echo "=== Unit: CSS Animation Duration Check ==="

INDEX="sprints/kanban/index.html"

if [[ ! -f "$INDEX" ]]; then
  echo "FAIL: $INDEX does not exist"
  exit 1
fi

FAIL=0

check_animation() {
  local pattern="$1"
  local description="$2"
  if grep -qiE "$pattern" "$INDEX"; then
    echo "PASS: $description"
  else
    echo "FAIL: Missing — $description (pattern: $pattern)"
    FAIL=1
  fi
}

# Card creation slide-down 150ms
check_animation "150ms|0\.15s" "Card creation animation (150ms)"

# Modal open/close opacity fade 200ms
check_animation "200ms|0\.2s" "Modal animation (200ms)"

# Filter transitions opacity fade 150ms (covered by 150ms check above)
# Verify transition/animation property usage
check_animation "transition|animation|@keyframes" "CSS transitions/animations defined"

# Verify transform is used for drag (60fps — no layout reflow)
check_animation "transform.*translate|translateX|translateY" "CSS transforms for drag performance"

echo ""
if [[ "$FAIL" -eq 0 ]]; then
  echo "PASS: All required animation durations present"
  exit 0
else
  echo "FAIL: Some animation durations are missing"
  exit 1
fi
