#!/usr/bin/env bash
# Verification: User can create notes via UI form
# PRD Reference: Notes List page - inline new-note form
# Vision Goal: Click "New Note" to create a note with title and body
# Category: value
set -euo pipefail

echo "=== Value: Create Note via UI Form ==="

cd "$(dirname "$0")/../.."

# Isolated test environment
TEST_PORT="${PORT:-3000}"
DATA_DIR="${TEST_DATA_DIR:-$(mktemp -d)}"

# Start server with port isolation
cat > /tmp/test_ui_server_$$.js <<EOF
const app = require('./server.js');
const fs = require('fs');
const path = require('path');

// Override persistence path
const originalReadNotes = require('./persistence').readNotes;
const originalWriteNotes = require('./persistence').writeNotes;

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

// Patch the routes to use test persistence
require.cache[require.resolve('./persistence')].exports = persistence;

app.listen(${TEST_PORT}, () => {
  console.log('UI test server on ${TEST_PORT}');
});
EOF

trap 'kill $SERVER_PID 2>/dev/null || true; rm -f /tmp/test_ui_server_$$.js; rm -rf "$DATA_DIR"' EXIT

node /tmp/test_ui_server_$$.js > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2

if ! kill -0 $SERVER_PID 2>/dev/null; then
  echo "FAIL: Server failed to start"
  exit 1
fi

BASE_URL="http://localhost:${TEST_PORT}"

echo "Test 1: Index page serves successfully"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/")
if [ "$STATUS" = "200" ]; then
  echo "✓ GET / returns 200"
else
  echo "✗ GET / returned $STATUS (expected 200)"
  exit 1
fi

echo ""
echo "Test 2: Index page contains New Note button"
HTML=$(curl -s "${BASE_URL}/")
if echo "$HTML" | grep -q 'id="new-note-btn"'; then
  echo "✓ New Note button present"
else
  echo "✗ New Note button missing"
  exit 1
fi

echo ""
echo "Test 3: Index page contains note form"
if echo "$HTML" | grep -q 'id="new-note-form"'; then
  echo "✓ Note form present"
else
  echo "✗ Note form missing"
  exit 1
fi

if echo "$HTML" | grep -q 'id="note-title"'; then
  echo "✓ Title input present"
else
  echo "✗ Title input missing"
  exit 1
fi

if echo "$HTML" | grep -q 'id="note-body"'; then
  echo "✓ Body textarea present"
else
  echo "✗ Body textarea missing"
  exit 1
fi

echo ""
echo "Test 4: Create note via API (simulating form submission)"
RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"title":"UI Test Note","body":"This note was created via the form submission flow"}' \
  "${BASE_URL}/api/notes")

NOTE_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$NOTE_ID" ]; then
  echo "✓ Note created successfully (ID: $NOTE_ID)"
else
  echo "✗ Failed to create note"
  echo "Response: $RESPONSE"
  exit 1
fi

echo ""
echo "Test 5: Verify note appears in notes list API"
NOTES_LIST=$(curl -s "${BASE_URL}/api/notes")
if echo "$NOTES_LIST" | grep -q "$NOTE_ID"; then
  echo "✓ Note appears in GET /api/notes"
else
  echo "✗ Note missing from notes list"
  exit 1
fi

if echo "$NOTES_LIST" | grep -q "UI Test Note"; then
  echo "✓ Note title present in list"
else
  echo "✗ Note title missing from list"
  exit 1
fi

echo ""
echo "Test 6: Verify note persisted to JSON file"
if [ -f "${DATA_DIR}/notes.json" ]; then
  echo "✓ notes.json file created"

  if grep -q "$NOTE_ID" "${DATA_DIR}/notes.json"; then
    echo "✓ Note persisted to file"
  else
    echo "✗ Note not in JSON file"
    exit 1
  fi
else
  echo "✗ notes.json file not created"
  exit 1
fi

echo ""
echo "Test 7: Verify app.js script is served"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/app.js")
if [ "$STATUS" = "200" ]; then
  echo "✓ app.js served successfully"
else
  echo "✗ app.js returned $STATUS"
  exit 1
fi

# Check app.js contains form handling logic
APP_JS=$(curl -s "${BASE_URL}/app.js")
if echo "$APP_JS" | grep -q "handleCreateNote"; then
  echo "✓ app.js contains form submission handler"
else
  echo "✗ app.js missing form handler"
  exit 1
fi

echo ""
echo "PASS: User can create notes via UI form"
exit 0
