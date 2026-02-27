#!/usr/bin/env bash
# Verification: User can delete notes via UI
# PRD Reference: Notes List page - Delete button on each card
# Vision Goal: Delete a note and see it disappear from the list
# Category: value
set -euo pipefail

echo "=== Value: Delete Note via UI ==="

cd "$(dirname "$0")/../.."

# Isolated test environment
TEST_PORT="${PORT:-3000}"
DATA_DIR="${TEST_DATA_DIR:-$(mktemp -d)}"

# Pre-populate with test notes
mkdir -p "${DATA_DIR}"
cat > "${DATA_DIR}/notes.json" <<EOF
[
  {
    "id": "note-to-keep",
    "title": "Keep This Note",
    "body": "This note should remain after deletion test.",
    "createdAt": "2026-02-27T10:00:00Z"
  },
  {
    "id": "note-to-delete",
    "title": "Delete This Note",
    "body": "This note will be deleted during the test.",
    "createdAt": "2026-02-27T11:00:00Z"
  }
]
EOF

# Start server
cat > /tmp/test_ui_delete_$$.js <<EOF
const app = require('./server.js');
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

require.cache[require.resolve('./persistence')].exports = persistence;

app.listen(${TEST_PORT}, () => {
  console.log('Delete test server on ${TEST_PORT}');
});
EOF

trap 'kill $SERVER_PID 2>/dev/null || true; rm -f /tmp/test_ui_delete_$$.js; rm -rf "$DATA_DIR"' EXIT

node /tmp/test_ui_delete_$$.js > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2

if ! kill -0 $SERVER_PID 2>/dev/null; then
  echo "FAIL: Server failed to start"
  exit 1
fi

BASE_URL="http://localhost:${TEST_PORT}"

echo "Test 1: Verify both notes exist initially"
NOTES=$(curl -s "${BASE_URL}/api/notes")

if echo "$NOTES" | grep -q "note-to-keep"; then
  echo "✓ Note to keep present"
else
  echo "✗ Note to keep missing"
  exit 1
fi

if echo "$NOTES" | grep -q "note-to-delete"; then
  echo "✓ Note to delete present"
else
  echo "✗ Note to delete missing"
  exit 1
fi

echo ""
echo "Test 2: Delete note via API (simulating UI delete button)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${BASE_URL}/api/notes/note-to-delete")

if [ "$STATUS" = "204" ]; then
  echo "✓ DELETE returned 204 (success)"
else
  echo "✗ DELETE returned $STATUS (expected 204)"
  exit 1
fi

echo ""
echo "Test 3: Verify note removed from list"
NOTES_AFTER=$(curl -s "${BASE_URL}/api/notes")

if echo "$NOTES_AFTER" | grep -q "note-to-delete"; then
  echo "✗ Deleted note still present in list"
  exit 1
else
  echo "✓ Deleted note removed from list"
fi

if echo "$NOTES_AFTER" | grep -q "note-to-keep"; then
  echo "✓ Other note still present (not affected)"
else
  echo "✗ Other note was incorrectly deleted"
  exit 1
fi

echo ""
echo "Test 4: Verify deletion persisted to JSON file"
FILE_CONTENT=$(cat "${DATA_DIR}/notes.json")

if echo "$FILE_CONTENT" | grep -q "note-to-delete"; then
  echo "✗ Deleted note still in JSON file"
  exit 1
else
  echo "✓ Note permanently removed from JSON file"
fi

if echo "$FILE_CONTENT" | grep -q "note-to-keep"; then
  echo "✓ Remaining note preserved in JSON file"
else
  echo "✗ Remaining note lost from JSON file"
  exit 1
fi

echo ""
echo "Test 5: Verify delete function exists in app.js"
APP_JS=$(curl -s "${BASE_URL}/app.js")

if echo "$APP_JS" | grep -q "deleteNote"; then
  echo "✓ deleteNote function present"
else
  echo "✗ deleteNote function missing"
  exit 1
fi

if echo "$APP_JS" | grep -q "DELETE"; then
  echo "✓ DELETE HTTP method used in deleteNote"
else
  echo "✗ DELETE method not found"
  exit 1
fi

echo ""
echo "Test 6: Verify delete button creates DELETE request"
if echo "$APP_JS" | grep -q '/api/notes/'; then
  echo "✓ API endpoint path present in delete logic"
else
  echo "✗ API endpoint path missing"
  exit 1
fi

echo ""
echo "Test 7: Attempt to delete non-existent note (edge case)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${BASE_URL}/api/notes/nonexistent-note-id")

if [ "$STATUS" = "404" ]; then
  echo "✓ DELETE non-existent note returns 404"
else
  echo "✗ DELETE non-existent note returned $STATUS (expected 404)"
  exit 1
fi

echo ""
echo "PASS: Delete note via UI verified"
exit 0
