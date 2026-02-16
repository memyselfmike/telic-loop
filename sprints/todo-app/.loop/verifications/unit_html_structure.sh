#!/usr/bin/env bash
# Verification: HTML structure and required elements exist
# PRD Reference: Section 2 (Functional Requirements)
# Vision Goal: G1 - Self-contained HTML file
# Category: unit
set -euo pipefail

echo "=== Unit Test: HTML Structure ==="

SPRINT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
HTML_FILE="$SPRINT_DIR/index.html"

if [[ ! -f "$HTML_FILE" ]]; then
  echo "FAIL: index.html does not exist at $HTML_FILE"
  exit 1
fi

echo "✓ index.html exists"

# Check for required HTML structure
required_elements=(
  "<title>Todo App</title>"
  'id="taskInput"'
  'placeholder="What needs to be done?"'
  'id="addButton"'
  'id="taskList"'
  'id="taskCount"'
  'data-filter="all"'
  'data-filter="active"'
  'data-filter="completed"'
  "<style>"
  "<script>"
)

for element in "${required_elements[@]}"; do
  if ! grep -q "$element" "$HTML_FILE"; then
    echo "FAIL: Missing required element: $element"
    exit 1
  fi
done

echo "✓ All required HTML elements present"

# Check that it's self-contained (no external dependencies)
if grep -E '(src=|href=)["'"'"']https?://' "$HTML_FILE"; then
  echo "FAIL: Found external dependencies (CDN links)"
  exit 1
fi

echo "✓ No external dependencies (self-contained)"

# Check for localStorage implementation
if ! grep -q "localStorage" "$HTML_FILE"; then
  echo "FAIL: localStorage implementation not found"
  exit 1
fi

echo "✓ localStorage implementation present"

# Check for essential JavaScript functions
required_functions=(
  "function addTask"
  "function deleteTask"
  "function toggleTask"
  "function renderTasks"
  "function saveTasks"
  "function loadTasks"
)

for func in "${required_functions[@]}"; do
  if ! grep -q "$func" "$HTML_FILE"; then
    echo "FAIL: Missing required function: $func"
    exit 1
  fi
done

echo "✓ All essential JavaScript functions present"

# Check for mobile responsiveness in CSS
if ! grep -q "@media.*max-width" "$HTML_FILE"; then
  echo "FAIL: No mobile media queries found"
  exit 1
fi

echo "✓ Mobile media queries present"

echo ""
echo "PASS: HTML structure verification complete"
echo "All required elements, functions, and features are present in the HTML file."

exit 0
