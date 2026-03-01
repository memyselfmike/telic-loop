#!/usr/bin/env bash
# Verification: JSON File Persistence Across Operations
# PRD Reference: Data Model - JSON file storage in data/notes.json
# Vision Goal: User restarts server and all notes are still present
# Category: unit
#
# NOTE: This test verifies that data persists by creating notes,
# then reading them back. Full restart testing requires server
# to accept PORT and DATA_DIR env vars for isolation.
set -euo pipefail

echo "=== Persistence Test ==="

cd "$(dirname "$0")/../.."

# Use port from environment
TEST_PORT="${PORT:-3000}"

# Wait for server to be ready
echo "Waiting for server on port $TEST_PORT..."
for i in {1..10}; do
  if curl -s "http://localhost:$TEST_PORT/api/notes" > /dev/null 2>&1; then
    break
  fi
  if [ $i -eq 10 ]; then
    echo "FAIL: Server not responding on port $TEST_PORT"
    echo "Hint: Start server with: node server.js"
    exit 1
  fi
  sleep 0.5
done

echo "✓ Server responding on port $TEST_PORT"

# Create note 1
create1=$(curl -s -X POST "http://localhost:$TEST_PORT/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"Persistence Test 1","body":"First test note for persistence verification"}')
note1_id=$(echo "$create1" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$note1_id" ]; then
  echo "FAIL: Failed to create first note"
  exit 1
fi
echo "✓ Created note 1: $note1_id"

# Create note 2
create2=$(curl -s -X POST "http://localhost:$TEST_PORT/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"Persistence Test 2","body":"Second test note for persistence verification"}')
note2_id=$(echo "$create2" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$note2_id" ]; then
  echo "FAIL: Failed to create second note"
  exit 1
fi
echo "✓ Created note 2: $note2_id"

# Verify both notes are immediately retrievable (write + read)
note1_retrieved=$(curl -s "http://localhost:$TEST_PORT/api/notes/$note1_id")
if ! echo "$note1_retrieved" | grep -q '"id":"'"$note1_id"'"'; then
  echo "FAIL: Note 1 not retrievable immediately after creation"
  exit 1
fi
if ! echo "$note1_retrieved" | grep -q '"title":"Persistence Test 1"'; then
  echo "FAIL: Note 1 content incorrect"
  exit 1
fi
echo "✓ Note 1 readable immediately after write"

note2_retrieved=$(curl -s "http://localhost:$TEST_PORT/api/notes/$note2_id")
if ! echo "$note2_retrieved" | grep -q '"id":"'"$note2_id"'"'; then
  echo "FAIL: Note 2 not retrievable immediately after creation"
  exit 1
fi
echo "✓ Note 2 readable immediately after write"

# Verify both notes appear in list
all_notes=$(curl -s "http://localhost:$TEST_PORT/api/notes")
if ! echo "$all_notes" | grep -q '"'"$note1_id"'"'; then
  echo "FAIL: Note 1 not in full list"
  exit 1
fi
if ! echo "$all_notes" | grep -q '"'"$note2_id"'"'; then
  echo "FAIL: Note 2 not in full list"
  exit 1
fi
echo "✓ Both notes appear in GET /api/notes"

# Verify data file exists and contains notes
if [ ! -f "data/notes.json" ]; then
  echo "FAIL: data/notes.json file not created"
  exit 1
fi

if ! grep -q "$note1_id" "data/notes.json"; then
  echo "FAIL: Note 1 ID not found in data/notes.json"
  exit 1
fi
if ! grep -q "$note2_id" "data/notes.json"; then
  echo "FAIL: Note 2 ID not found in data/notes.json"
  exit 1
fi
echo "✓ Notes persisted to data/notes.json file"

# Delete note 1 and verify persistence of deletion
delete_response=$(curl -s -w "\n%{http_code}" -X DELETE "http://localhost:$TEST_PORT/api/notes/$note1_id")
delete_status=$(echo "$delete_response" | tail -n 1)

if [ "$delete_status" != "204" ]; then
  echo "FAIL: DELETE expected 204, got $delete_status"
  exit 1
fi
echo "✓ Deleted note 1"

# Verify note 1 is gone, note 2 remains
if grep -q "$note1_id" "data/notes.json"; then
  echo "FAIL: Deleted note still in data/notes.json"
  exit 1
fi
if ! grep -q "$note2_id" "data/notes.json"; then
  echo "FAIL: Note 2 missing from data/notes.json after note 1 deletion"
  exit 1
fi
echo "✓ Deletion persisted to disk (note 1 removed, note 2 remains)"

# Clean up note 2
curl -s -X DELETE "http://localhost:$TEST_PORT/api/notes/$note2_id" > /dev/null

echo ""
echo "PASS: Persistence verified"
echo "  - Notes written to data/notes.json"
echo "  - Notes readable immediately after write"
echo "  - Deletions persist to disk"
echo ""
echo "NOTE: Full restart persistence test requires server to accept"
echo "      PORT and DATA_DIR environment variables for test isolation."
exit 0
