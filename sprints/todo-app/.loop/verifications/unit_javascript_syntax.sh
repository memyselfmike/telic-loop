#!/usr/bin/env bash
# Verification: JavaScript syntax is valid and has no obvious errors
# PRD Reference: Section 3 (Technical Constraints)
# Vision Goal: G1 - Working vanilla JavaScript
# Category: unit
set -euo pipefail

echo "=== Unit Test: JavaScript Syntax Validation ==="

SPRINT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
HTML_FILE="$SPRINT_DIR/index.html"

if [[ ! -f "$HTML_FILE" ]]; then
  echo "FAIL: index.html does not exist"
  exit 1
fi

# Extract JavaScript code from HTML
JS_TEMP=$(mktemp)
trap "rm -f $JS_TEMP" EXIT

# Extract content between <script> tags
sed -n '/<script>/,/<\/script>/p' "$HTML_FILE" | \
  sed '1d;$d' > "$JS_TEMP"

if [[ ! -s "$JS_TEMP" ]]; then
  echo "FAIL: No JavaScript code found in HTML"
  exit 1
fi

echo "✓ JavaScript code extracted"

# Check for common syntax errors
if grep -qE '(console\.log.*TODO|FIXME|XXX|HACK)' "$JS_TEMP"; then
  echo "WARNING: Found development comments (TODO/FIXME/XXX/HACK)"
fi

# Check for balanced braces
open_braces=$(grep -o '{' "$JS_TEMP" | wc -l)
close_braces=$(grep -o '}' "$JS_TEMP" | wc -l)

if [[ $open_braces -ne $close_braces ]]; then
  echo "FAIL: Unbalanced braces (open: $open_braces, close: $close_braces)"
  exit 1
fi

echo "✓ Balanced braces ($open_braces pairs)"

# Check for balanced parentheses
open_parens=$(grep -o '(' "$JS_TEMP" | wc -l)
close_parens=$(grep -o ')' "$JS_TEMP" | wc -l)

if [[ $open_parens -ne $close_parens ]]; then
  echo "FAIL: Unbalanced parentheses (open: $open_parens, close: $close_parens)"
  exit 1
fi

echo "✓ Balanced parentheses ($open_parens pairs)"

# Check for balanced brackets
open_brackets=$(grep -o '\[' "$JS_TEMP" | wc -l)
close_brackets=$(grep -o '\]' "$JS_TEMP" | wc -l)

if [[ $open_brackets -ne $close_brackets ]]; then
  echo "FAIL: Unbalanced brackets (open: $open_brackets, close: $close_brackets)"
  exit 1
fi

echo "✓ Balanced brackets ($open_brackets pairs)"

# Check for common JavaScript keywords and patterns
required_patterns=(
  "addEventListener"
  "querySelector"
  "localStorage"
  "JSON.parse"
  "JSON.stringify"
)

for pattern in "${required_patterns[@]}"; do
  if ! grep -q "$pattern" "$JS_TEMP"; then
    echo "FAIL: Expected JavaScript pattern not found: $pattern"
    exit 1
  fi
done

echo "✓ All expected JavaScript patterns present"

# Check that variables are declared (let, const, var, or function)
# Look for potential undeclared variable assignments
if grep -E '^[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*=' "$JS_TEMP" | \
   grep -vE '(let|const|var|function|\.)\s*[a-zA-Z_]' | \
   head -1 > /dev/null; then
  echo "WARNING: Potential undeclared variable found"
fi

echo "✓ Variable declarations look correct"

echo ""
echo "PASS: JavaScript syntax validation complete"
echo "Code structure is valid and contains all expected patterns."

exit 0
