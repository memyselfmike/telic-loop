#!/usr/bin/env bash
# Verification: Data persistence across server restarts
# PRD Reference: Storage - JSON file persistence survives restarts
# Vision Goal: Notes survive server restarts (JSON persistence proof)
# Category: integration
set -euo pipefail

echo "=== Integration: Persistence Across Server Restarts ==="

cd "$(dirname "$0")/../.."

# Isolated test environment
TEST_PORT="${PORT:-3300}"
DATA_DIR="${TEST_DATA_DIR:-$(mktemp -d)}"

# Server script template (will be reused)
create_server() {
  cat > .test_persist_temp.js <<EOF
const express = require('express');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const NOTES_FILE = '${DATA_DIR}/notes.json';

function readNotes() {
  try {
    if (!fs.existsSync(NOTES_FILE)) return [];
    const content = fs.readFileSync(NOTES_FILE, 'utf-8');
    if (!content || content.trim() === '') return [];
    return JSON.parse(content);
  } catch (e) { return []; }
}

function writeNotes(notes) {
  const dir = path.dirname(NOTES_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(NOTES_FILE, JSON.stringify(notes, null, 2));
}

const app = express();
app.use(express.json());

app.get('/api/notes', (req, res) => res.status(200).json(readNotes()));

app.post('/api/notes', (req, res) => {
  const { title, body } = req.body;
  if (!title?.trim() || !body?.trim()) {
    return res.status(400).json({ error: 'Title and body required' });
  }
  const note = {
    id: crypto.randomUUID(),
    title: title.trim(),
    body: body.trim(),
    createdAt: new Date().toISOString()
  };
  const notes = readNotes();
  notes.push(note);
  writeNotes(notes);
  res.status(201).json(note);
});

app.listen(${TEST_PORT});
EOF
}

trap 'kill $SERVER_PID 2>/dev/null || true; rm -rf "$DATA_DIR" .test_persist_temp.js' EXIT

BASE_URL="http://localhost:${TEST_PORT}"

echo "Step 1: Start server and create a note"
create_server
node .test_persist_temp.js > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2

if ! kill -0 $SERVER_PID 2>/dev/null; then
  echo "FAIL: Server failed to start"
  exit 1
fi

# Create a note
response=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"title":"Persistence Test","body":"This note should survive server restart"}' \
  "${BASE_URL}/api/notes")

NOTE_ID=$(echo "$response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$NOTE_ID" ]; then
  echo "FAIL: Could not create test note"
  echo "Response: $response"
  exit 1
fi

echo "✓ Created note with ID: $NOTE_ID"

# Verify note exists in JSON file
if [ ! -f "${DATA_DIR}/notes.json" ]; then
  echo "FAIL: notes.json file not created"
  exit 1
fi

echo "✓ notes.json file created"

if grep -q "$NOTE_ID" "${DATA_DIR}/notes.json"; then
  echo "✓ Note persisted to JSON file"
else
  echo "FAIL: Note not found in JSON file"
  cat "${DATA_DIR}/notes.json"
  exit 1
fi

echo ""
echo "Step 2: Stop server"
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null || true
echo "✓ Server stopped"

echo ""
echo "Step 3: Restart server"
create_server
node .test_persist_temp.js > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2

if ! kill -0 $SERVER_PID 2>/dev/null; then
  echo "FAIL: Server failed to restart"
  exit 1
fi

echo "✓ Server restarted"

echo ""
echo "Step 4: Verify note still exists"
response=$(curl -s "${BASE_URL}/api/notes")

if echo "$response" | grep -q "$NOTE_ID"; then
  echo "✓ Note survived server restart"
else
  echo "FAIL: Note lost after server restart"
  echo "Response: $response"
  exit 1
fi

if echo "$response" | grep -q "Persistence Test"; then
  echo "✓ Note content intact"
else
  echo "FAIL: Note content corrupted"
  exit 1
fi

echo ""
echo "PASS: Persistence across server restarts verified"
exit 0
