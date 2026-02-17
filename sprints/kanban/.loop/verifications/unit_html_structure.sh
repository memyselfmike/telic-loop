#!/usr/bin/env bash
# Verification: index.html contains required structural elements
# PRD Reference: Section 2 (Board Structure), Section 10 (Visual Design)
# Vision Goal: "See their work at a glance" — three columns always present
# Category: unit

set -euo pipefail

echo "=== Unit: HTML Structure Verification ==="

INDEX="sprints/kanban/index.html"

if [[ ! -f "$INDEX" ]]; then
  echo "FAIL: $INDEX does not exist"
  exit 1
fi

FAIL=0

check_contains() {
  local pattern="$1"
  local description="$2"
  if grep -qiE "$pattern" "$INDEX"; then
    echo "PASS: $description"
  else
    echo "FAIL: Missing — $description (pattern: $pattern)"
    FAIL=1
  fi
}

# Required HTML structural elements
check_contains "<!DOCTYPE html>" "Has DOCTYPE declaration"
check_contains "<html" "Has html element"
check_contains "<style" "Has inline CSS"
check_contains "<script" "Has inline JavaScript"
check_contains "To Do" "Has 'To Do' column reference"
check_contains "In Progress" "Has 'In Progress' column reference"
check_contains "Done" "Has 'Done' column reference"
check_contains "localStorage" "Uses localStorage for persistence"
check_contains "kanban_board_state" "Uses correct localStorage key"
check_contains "Search" "Has search functionality"
check_contains "priority" "Has priority handling"
check_contains "Ctrl\+Z|ctrlKey|Control\+z" "Has undo (Ctrl+Z) handling"
check_contains "#0d1117" "Has dark background color"
check_contains "#161b22" "Has column background color"
check_contains "#21262d" "Has card background color"
check_contains "mousedown|addEventListener.*mouse" "Has mouse drag event handling"
check_contains "touchstart|addEventListener.*touch" "Has touch event handling"
check_contains "aria-label" "Has ARIA labels for accessibility"
check_contains "flex|grid" "Uses flexbox or grid layout"

# Check for the media query that handles mobile stacking
check_contains "@media.*max-width.*767|@media.*max-width.*768" "Has mobile breakpoint media query"

echo ""
if [[ "$FAIL" -eq 0 ]]; then
  echo "PASS: All required structural elements present"
  exit 0
else
  echo "FAIL: Some required structural elements are missing"
  exit 1
fi
