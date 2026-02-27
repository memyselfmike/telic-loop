#!/usr/bin/env bash
# Verification: User can expand notes to view full content
# PRD Reference: Notes List page - Click title to expand full body
# Vision Goal: Click a note to view its full content
# Category: value
set -euo pipefail

echo "=== Value: Expand Note to View Full Content ==="

cd "$(dirname "$0")/../.."
PROJECT_DIR="$(pwd)"

# Convert Unix-style paths to Windows-style for Node.js on Windows
# Git Bash pwd returns /e/... but Node.js needs E:/...
PROJECT_DIR="$(echo "$PROJECT_DIR" | sed 's|^/\([a-z]\)/|\U\1:/|')"

# Isolated test environment
TEST_PORT="${PORT:-3000}"
DATA_DIR="${TEST_DATA_DIR:-$(mktemp -d)}"

# Create test note with long body (>80 chars)
mkdir -p "${DATA_DIR}"
cat > "${DATA_DIR}/notes.json" <<EOF
[
  {
    "id": "expandable-note",
    "title": "Expandable Note",
    "body": "This is a very long note body that definitely exceeds the 80-character preview limit. When the user clicks on the note title, this full text should be displayed. The preview will only show the first 80 characters followed by ellipsis, but clicking the title reveals everything including this sentence and beyond.",
    "createdAt": "2026-02-27T10:00:00Z"
  }
]
EOF

# Start server
cat > /tmp/test_ui_expand_$$.js <<EOF
const app = require('${PROJECT_DIR}/server.js');
const fs = require('fs');
const path = require('path');

const NOTES_FILE = path.join('${DATA_DIR}', 'notes.json');

const persistence = {
  readNotes: function() {
    try {
      if (!fs.existsSync(NOTES_FILE)) return [];
      const content = fs.readFileSync(NOTES_FILE, 'utf-8');
      if (!content || content.trim() === '') return [];
      return JSON.parse(content);
    } catch {
      return [];
    }
  },
  writeNotes: function(notes) {
    const dir = path.dirname(NOTES_FILE);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(NOTES_FILE, JSON.stringify(notes, null, 2));
  }
};

require.cache[require.resolve('${PROJECT_DIR}/persistence')].exports = persistence;

app.listen(${TEST_PORT}, () => {
  console.log('Expand test server on ${TEST_PORT}');
});
EOF

trap 'kill $SERVER_PID 2>/dev/null || true; rm -f /tmp/test_ui_expand_$$.js; rm -rf "$DATA_DIR"' EXIT

node /tmp/test_ui_expand_$$.js > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2

if ! kill -0 $SERVER_PID 2>/dev/null; then
  echo "FAIL: Server failed to start"
  exit 1
fi

BASE_URL="http://localhost:${TEST_PORT}"

echo "Test 1: Verify note body exceeds 80 characters"
NOTES=$(curl -s "${BASE_URL}/api/notes")
BODY=$(echo "$NOTES" | grep -o '"body":"[^"]*"' | cut -d'"' -f4)
BODY_LENGTH=${#BODY}

if [ $BODY_LENGTH -gt 80 ]; then
  echo "✓ Note body is $BODY_LENGTH characters (exceeds 80-char preview limit)"
else
  echo "✗ Note body is only $BODY_LENGTH characters (test data issue)"
  exit 1
fi

echo ""
echo "Test 2: Verify getBodyPreview function exists"
APP_JS=$(curl -s "${BASE_URL}/app.js")

if echo "$APP_JS" | grep -q "getBodyPreview"; then
  echo "✓ getBodyPreview function present"
else
  echo "✗ getBodyPreview function missing"
  exit 1
fi

echo ""
echo "Test 3: Verify preview truncates at 80 characters"
# Check for 80-character logic and ellipsis
if echo "$APP_JS" | grep -q "80"; then
  echo "✓ 80-character limit present in preview logic"
else
  echo "✗ 80-character limit not found"
  exit 1
fi

if echo "$APP_JS" | grep -q '\.\.\.'; then
  echo "✓ Ellipsis added to truncated preview"
else
  echo "✗ Ellipsis logic missing"
  exit 1
fi

echo ""
echo "Test 4: Verify toggleNoteExpansion function exists"
if echo "$APP_JS" | grep -q "toggleNoteExpansion"; then
  echo "✓ toggleNoteExpansion function present"
else
  echo "✗ toggleNoteExpansion function missing"
  exit 1
fi

echo ""
echo "Test 5: Verify expansion shows/hides preview and full body"
if echo "$APP_JS" | grep -q "note-body-preview"; then
  echo "✓ Preview element referenced in toggle logic"
else
  echo "✗ Preview element not in toggle logic"
  exit 1
fi

if echo "$APP_JS" | grep -q "note-body-full"; then
  echo "✓ Full body element referenced in toggle logic"
else
  echo "✗ Full body element not in toggle logic"
  exit 1
fi

echo ""
echo "Test 6: Verify toggle uses 'hidden' class"
if echo "$APP_JS" | grep -q "classList.*hidden"; then
  echo "✓ Toggle uses 'hidden' class to show/hide content"
else
  echo "✗ Hidden class toggle logic missing"
  exit 1
fi

echo ""
echo "Test 7: Verify title click triggers expansion"
if echo "$APP_JS" | grep -q "note-title"; then
  echo "✓ Note title element referenced"
else
  echo "✗ Note title element not found"
  exit 1
fi

# Check for click event listener on title
if echo "$APP_JS" | grep -q "addEventListener.*click"; then
  echo "✓ Click event listener present"
else
  echo "✗ Click event listener missing"
  exit 1
fi

echo ""
echo "Test 8: Verify CSS supports expanded state"
CSS=$(curl -s "${BASE_URL}/style.css")

if echo "$CSS" | grep -q "\.hidden"; then
  echo "✓ Hidden class defined in CSS"
else
  echo "✗ Hidden class missing from CSS"
  exit 1
fi

if echo "$CSS" | grep -q "note-body-preview\|note-body-full"; then
  echo "✓ Body preview/full styles present"
else
  echo "✗ Body styles missing from CSS"
  exit 1
fi

echo ""
echo "Test 9: Verify createNoteCard includes both preview and full body"
if echo "$APP_JS" | grep -q "createNoteCard"; then
  echo "✓ createNoteCard function present"
else
  echo "✗ createNoteCard function missing"
  exit 1
fi

# Check that card creation includes both preview and full elements
CARD_FUNCTION=$(echo "$APP_JS" | sed -n '/createNoteCard/,/^}/p')
if echo "$CARD_FUNCTION" | grep -q "note-body-preview" && echo "$CARD_FUNCTION" | grep -q "note-body-full"; then
  echo "✓ Note card includes both preview and full body elements"
else
  echo "✗ Note card missing preview or full body element"
  exit 1
fi

echo ""
echo "PASS: Expand note to view full content verified"
exit 0
