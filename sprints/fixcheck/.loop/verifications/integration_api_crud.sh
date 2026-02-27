#!/usr/bin/env bash
# Verification: Notes CRUD API endpoints
# PRD Reference: API Endpoints - GET/POST/GET/:id/DELETE/:id
# Vision Goal: Create, view, and delete notes via REST API
# Category: integration
set -euo pipefail

echo "=== Integration: Notes CRUD API ==="

cd "$(dirname "$0")/../.."

# Isolated test environment
TEST_PORT="${PORT:-3200}"
DATA_DIR="${TEST_DATA_DIR:-$(mktemp -d)}"

# Ensure clean data directory
mkdir -p "${DATA_DIR}"
echo "[]" > "${DATA_DIR}/notes.json"

# Create test server IN PROJECT DIR (so it can find node_modules)
cat > .test_server_temp.js <<EOF
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
    const notes = JSON.parse(content);
    return Array.isArray(notes) ? notes : [];
  } catch (e) { return []; }
}

function writeNotes(notes) {
  const dir = path.dirname(NOTES_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(NOTES_FILE, JSON.stringify(notes, null, 2));
}

const app = express();
app.use(express.json());

app.get('/api/notes', (req, res) => {
  try {
    res.status(200).json(readNotes());
  } catch (e) {
    res.status(500).json({ error: 'Failed to retrieve notes' });
  }
});

app.post('/api/notes', (req, res) => {
  try {
    const { title, body } = req.body;
    if (!title || typeof title !== 'string' || title.trim() === '') {
      return res.status(400).json({ error: 'Title is required and must be non-empty' });
    }
    if (!body || typeof body !== 'string' || body.trim() === '') {
      return res.status(400).json({ error: 'Body is required and must be non-empty' });
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
  } catch (e) {
    res.status(500).json({ error: 'Failed to create note' });
  }
});

app.get('/api/notes/:id', (req, res) => {
  try {
    const notes = readNotes();
    const note = notes.find(n => n.id === req.params.id);
    if (!note) return res.status(404).json({ error: 'Note not found' });
    res.status(200).json(note);
  } catch (e) {
    res.status(500).json({ error: 'Failed to retrieve note' });
  }
});

app.delete('/api/notes/:id', (req, res) => {
  try {
    const notes = readNotes();
    const index = notes.findIndex(n => n.id === req.params.id);
    if (index === -1) return res.status(404).json({ error: 'Note not found' });
    notes.splice(index, 1);
    writeNotes(notes);
    res.status(204).send();
  } catch (e) {
    res.status(500).json({ error: 'Failed to delete note' });
  }
});

app.listen(${TEST_PORT});
EOF

trap 'kill $SERVER_PID 2>/dev/null || true; rm -rf "$DATA_DIR" .test_server_temp.js' EXIT

node .test_server_temp.js > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2

if ! kill -0 $SERVER_PID 2>/dev/null; then
  echo "FAIL: Server failed to start"
  exit 1
fi

BASE_URL="http://localhost:${TEST_PORT}"
PASSED=0
FAILED=0

test_api() {
  local desc="$1" method="$2" path="$3" data="$4" expect="$5"

  if [ -n "$data" ]; then
    resp=$(curl -s -w "\n%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "${BASE_URL}${path}")
  else
    resp=$(curl -s -w "\n%{http_code}" -X "$method" "${BASE_URL}${path}")
  fi

  status=$(echo "$resp" | tail -n1)
  body=$(echo "$resp" | head -n-1)

  if [ "$status" = "$expect" ]; then
    echo "✓ $desc"
    PASSED=$((PASSED + 1))
    echo "$body"
  else
    echo "✗ $desc (expected $expect, got $status)"
    FAILED=$((FAILED + 1))
  fi
}

# Run tests
test_api "GET /api/notes empty" "GET" "/api/notes" "" "200"
echo ""

CREATED=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"title":"Test","body":"Body"}' "${BASE_URL}/api/notes")
NOTE_ID=$(echo "$CREATED" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

test_api "POST valid note" "POST" "/api/notes" '{"title":"T2","body":"B2"}' "201"
echo ""

test_api "POST missing title" "POST" "/api/notes" '{"body":"B"}' "400"
echo ""

test_api "POST empty body" "POST" "/api/notes" '{"title":"T","body":""}' "400"
echo ""

if [ -n "$NOTE_ID" ]; then
  test_api "GET note by ID" "GET" "/api/notes/${NOTE_ID}" "" "200"
  echo ""
fi

test_api "GET missing note" "GET" "/api/notes/xxx" "" "404"
echo ""

if [ -n "$NOTE_ID" ]; then
  test_api "DELETE note" "DELETE" "/api/notes/${NOTE_ID}" "" "204"
  echo ""
fi

test_api "DELETE missing note" "DELETE" "/api/notes/xxx" "" "404"
echo ""

echo "Results: $PASSED passed, $FAILED failed"

if [ $FAILED -eq 0 ]; then
  echo "PASS: All API endpoints verified"
  exit 0
else
  echo "FAIL: Some tests failed"
  exit 1
fi
