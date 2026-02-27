#!/usr/bin/env bash
# Verification: Persistence module read/write operations
# PRD Reference: Data Model - JSON file persistence
# Vision Goal: JSON-file persistence with atomic writes
# Category: unit
set -euo pipefail

echo "=== Unit: Persistence Module ==="

cd "$(dirname "$0")/../.."

# Isolated test environment
DATA_DIR="${TEST_DATA_DIR:-$(mktemp -d)}"

# Convert Windows backslashes to forward slashes for Node.js
DATA_DIR_NORM="${DATA_DIR//\\//}"

trap 'rm -rf "$DATA_DIR"' EXIT

# Create test script that uses isolated data directory
cat > /tmp/test_persistence_$$.js <<EOF
const fs = require('fs');
const path = require('path');

// Override NOTES_FILE path to use test directory
const NOTES_FILE = path.join('${DATA_DIR_NORM}', 'notes.json');

// Copy persistence module and patch it for testing
const persistenceCode = fs.readFileSync('./persistence.js', 'utf-8');
const patchedCode = persistenceCode.replace(
  "const NOTES_FILE = path.join(__dirname, 'data', 'notes.json');",
  "const NOTES_FILE = path.join('${DATA_DIR_NORM}', 'notes.json');"
);

// Evaluate patched module
eval(patchedCode);

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log('✓', message);
    passed++;
  } else {
    console.log('✗', message);
    failed++;
  }
}

// Test 1: readNotes returns empty array when file missing
const empty = readNotes();
assert(Array.isArray(empty) && empty.length === 0, 'readNotes returns [] when file missing');

// Test 2: writeNotes creates valid JSON
const testNotes = [{
  id: 'test-123',
  title: 'Test Note',
  body: 'Test body content',
  createdAt: new Date().toISOString()
}];
writeNotes(testNotes);
assert(fs.existsSync(NOTES_FILE), 'writeNotes creates notes.json file');

// Test 3: readNotes returns written array
const readBack = readNotes();
assert(
  JSON.stringify(readBack) === JSON.stringify(testNotes),
  'readNotes returns written array'
);

// Test 4: readNotes handles empty file
fs.writeFileSync(NOTES_FILE, '', 'utf-8');
const emptyFile = readNotes();
assert(Array.isArray(emptyFile) && emptyFile.length === 0, 'readNotes returns [] for empty file');

// Test 5: Multiple notes persistence
const multiNotes = [
  { id: '1', title: 'First', body: 'Body 1', createdAt: '2026-01-01T00:00:00Z' },
  { id: '2', title: 'Second', body: 'Body 2', createdAt: '2026-01-02T00:00:00Z' }
];
writeNotes(multiNotes);
const multiRead = readNotes();
assert(multiRead.length === 2, 'Multiple notes persist correctly');

console.log(\`\nResults: \${passed} passed, \${failed} failed\`);
process.exit(failed > 0 ? 1 : 0);
EOF

node /tmp/test_persistence_$$.js
EXIT_CODE=$?

rm -f /tmp/test_persistence_$$.js

if [ $EXIT_CODE -eq 0 ]; then
  echo "PASS: Persistence module verified"
  exit 0
else
  echo "FAIL: Persistence module tests failed"
  exit 1
fi
