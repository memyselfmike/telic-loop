#!/usr/bin/env bash
# Verification: User can view notes list with title and preview
# PRD Reference: Notes List page - cards with title + 80-char preview
# Vision Goal: See all notes in a list (title + preview of body)
# Category: value
set -euo pipefail

echo "=== Value: Display Notes List with Preview ==="

cd "$(dirname "$0")/../.."
PROJECT_DIR="$(pwd)"

# Convert Unix-style paths to Windows-style for Node.js on Windows
# Git Bash pwd returns /e/... but Node.js needs E:/...
PROJECT_DIR="$(echo "$PROJECT_DIR" | sed 's|^/\([a-z]\)/|\U\1:/|')"

# Isolated test environment
TEST_PORT="${PORT:-3000}"
DATA_DIR="${TEST_DATA_DIR:-$(mktemp -d)}"

# Convert DATA_DIR to Windows format for Node.js
# On Git Bash, mktemp -d returns paths like /tmp/tmp.XXXXXX
# We need to convert to Windows format for Node.js to resolve correctly
if [[ "$DATA_DIR" =~ ^/([a-z])/ ]]; then
  # Drive letter path: /e/... → E:/...
  DATA_DIR="$(echo "$DATA_DIR" | sed 's|^/\([a-z]\)/|\U\1:/|')"
elif [[ "$DATA_DIR" =~ ^/tmp/ ]]; then
  # Git Bash /tmp maps to Windows TEMP dir
  # Use cygpath if available, otherwise use realpath
  if command -v cygpath &> /dev/null; then
    DATA_DIR="$(cygpath -w "$DATA_DIR" | tr '\\' '/')"
  else
    # Fallback: get absolute Windows path
    DATA_DIR="$(cd "$DATA_DIR" && pwd -W 2>/dev/null || pwd | sed 's|^/\([a-z]\)/|\U\1:/|')"
  fi
fi

# Pre-populate test data with notes of varying body lengths
mkdir -p "${DATA_DIR}"
cat > "${DATA_DIR}/notes.json" <<EOF
[
  {
    "id": "note-short",
    "title": "Short Note",
    "body": "This is a short note under 80 characters.",
    "createdAt": "2026-02-27T10:00:00Z"
  },
  {
    "id": "note-long",
    "title": "Long Note",
    "body": "This is a very long note that exceeds 80 characters and should be truncated in the preview display. The full text will only be visible when expanded by clicking the title.",
    "createdAt": "2026-02-27T11:00:00Z"
  }
]
EOF

# Start server with isolated data
cat > /tmp/test_ui_display_$$.js <<EOF
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

// Clear all potentially cached modules to ensure clean state
delete require.cache[require.resolve('${PROJECT_DIR}/server.js')];
delete require.cache[require.resolve('${PROJECT_DIR}/routes/notes')];
delete require.cache[require.resolve('${PROJECT_DIR}/persistence')];

// Inject patched persistence into require.cache
const persistencePath = require.resolve('${PROJECT_DIR}/persistence');
require.cache[persistencePath] = {
  id: persistencePath,
  filename: persistencePath,
  loaded: true,
  exports: persistence
};

// Now require server.js - routes/notes.js will get the patched persistence from cache
const app = require('${PROJECT_DIR}/server.js');

app.listen(${TEST_PORT}, () => {
  console.log('Display test server on ${TEST_PORT}');
});
EOF

trap 'kill $SERVER_PID 2>/dev/null || true; rm -f /tmp/test_ui_display_$$.js; rm -rf "$DATA_DIR"' EXIT

node /tmp/test_ui_display_$$.js > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2

if ! kill -0 $SERVER_PID 2>/dev/null; then
  echo "FAIL: Server failed to start"
  exit 1
fi

BASE_URL="http://localhost:${TEST_PORT}"

echo "Test 1: GET /api/notes returns pre-populated notes"
NOTES=$(curl -s "${BASE_URL}/api/notes")

if echo "$NOTES" | grep -q "note-short"; then
  echo "✓ Short note present"
else
  echo "✗ Short note missing"
  exit 1
fi

if echo "$NOTES" | grep -q "note-long"; then
  echo "✓ Long note present"
else
  echo "✗ Long note missing"
  exit 1
fi

echo ""
echo "Test 2: Verify app.js contains preview logic"
APP_JS=$(curl -s "${BASE_URL}/app.js")

if echo "$APP_JS" | grep -q "getBodyPreview"; then
  echo "✓ Preview function present"
else
  echo "✗ Preview function missing"
  exit 1
fi

# Check for 80-character preview logic
if echo "$APP_JS" | grep -q "80"; then
  echo "✓ 80-character preview logic present"
else
  echo "✗ 80-character limit not found in app.js"
  exit 1
fi

echo ""
echo "Test 3: Verify HTML structure for note cards"
HTML=$(curl -s "${BASE_URL}/")

if echo "$HTML" | grep -q 'id="notes-list"'; then
  echo "✓ Notes list container present"
else
  echo "✗ Notes list container missing"
  exit 1
fi

echo ""
echo "Test 4: Verify app.js creates note cards with preview"
if echo "$APP_JS" | grep -q "note-card"; then
  echo "✓ Note card creation logic present"
else
  echo "✗ Note card creation missing"
  exit 1
fi

if echo "$APP_JS" | grep -q "note-body-preview"; then
  echo "✓ Preview element creation present"
else
  echo "✗ Preview element missing"
  exit 1
fi

if echo "$APP_JS" | grep -q "note-body-full"; then
  echo "✓ Full body element creation present"
else
  echo "✗ Full body element missing"
  exit 1
fi

echo ""
echo "Test 5: Verify expand/collapse functionality exists"
if echo "$APP_JS" | grep -q "toggleNoteExpansion"; then
  echo "✓ Toggle expansion function present"
else
  echo "✗ Toggle function missing"
  exit 1
fi

echo ""
echo "Test 6: Verify delete button functionality exists"
if echo "$APP_JS" | grep -q "deleteNote"; then
  echo "✓ Delete function present"
else
  echo "✗ Delete function missing"
  exit 1
fi

if echo "$APP_JS" | grep -q "delete-btn"; then
  echo "✓ Delete button creation present"
else
  echo "✗ Delete button missing"
  exit 1
fi

echo ""
echo "Test 7: Verify CSS styling exists"
CSS=$(curl -s "${BASE_URL}/style.css")

if echo "$CSS" | grep -q "note-card"; then
  echo "✓ Note card styles present"
else
  echo "✗ Note card styles missing"
  exit 1
fi

echo ""
echo "Test 8: Verify navigation link to stats page"
if echo "$HTML" | grep -q "/stats"; then
  echo "✓ Stats page link present"
else
  echo "✗ Stats page link missing"
  exit 1
fi

echo ""
echo "PASS: Notes list display with preview verified"
exit 0
