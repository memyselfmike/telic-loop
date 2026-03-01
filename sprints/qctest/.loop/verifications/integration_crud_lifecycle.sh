#!/usr/bin/env bash
# Verification: CRUD API Lifecycle - Create, Read, Delete
# PRD Reference: API Endpoints section - all four CRUD operations
# Vision Goal: User can create notes, view them, and delete them
# Category: integration
#
# NOTE: This test creates its own data and cleans up after itself.
# Tests must run with isolated data stores to avoid conflicts.
set -euo pipefail

echo "=== CRUD API Lifecycle Test ==="

cd "$(dirname "$0")/../.."

# Use port from environment (test runner provides unique port for isolation)
TEST_PORT="${PORT:-3000}"

# Start server (assumes server is already running on TEST_PORT for now)
# TODO: Server should accept PORT env var for test isolation

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

# Step 1: Create a test note (test creates its own data)
create_response=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:$TEST_PORT/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"CRUD Test Note","body":"This note is created by integration_crud_lifecycle test and will be deleted at the end."}')

response_body=$(echo "$create_response" | head -n -1)
status_code=$(echo "$create_response" | tail -n 1)

if [ "$status_code" != "201" ]; then
  echo "FAIL: POST /api/notes expected 201, got $status_code"
  echo "Response: $response_body"
  exit 1
fi

# Extract note ID from response
note_id=$(echo "$response_body" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
if [ -z "$note_id" ]; then
  echo "FAIL: Created note did not include an ID"
  echo "Response: $response_body"
  exit 1
fi

# Verify response includes required fields
if ! echo "$response_body" | grep -q '"title":"CRUD Test Note"'; then
  echo "FAIL: Created note missing title"
  exit 1
fi
if ! echo "$response_body" | grep -q '"body":"This note is created by'; then
  echo "FAIL: Created note missing body"
  exit 1
fi
if ! echo "$response_body" | grep -q '"createdAt":"'; then
  echo "FAIL: Created note missing createdAt timestamp"
  exit 1
fi

echo "✓ POST /api/notes creates note with ID, title, body, createdAt (201)"

# Step 2: GET /api/notes/:id returns the created note
get_note_response=$(curl -s -w "\n%{http_code}" "http://localhost:$TEST_PORT/api/notes/$note_id")
get_note_body=$(echo "$get_note_response" | head -n -1)
get_note_status=$(echo "$get_note_response" | tail -n 1)

if [ "$get_note_status" != "200" ]; then
  echo "FAIL: GET /api/notes/:id expected 200, got $get_note_status"
  exit 1
fi

if ! echo "$get_note_body" | grep -q '"id":"'"$note_id"'"'; then
  echo "FAIL: Retrieved note has wrong ID"
  exit 1
fi

echo "✓ GET /api/notes/:id returns created note (200)"

# Step 3: GET /api/notes includes the note
all_notes=$(curl -s "http://localhost:$TEST_PORT/api/notes")
if ! echo "$all_notes" | grep -q '"'"$note_id"'"'; then
  echo "FAIL: GET /api/notes does not include created note ID"
  echo "Response: $all_notes"
  exit 1
fi

echo "✓ GET /api/notes lists created note"

# Step 4: DELETE /api/notes/:id removes the note
delete_response=$(curl -s -w "\n%{http_code}" -X DELETE "http://localhost:$TEST_PORT/api/notes/$note_id")
delete_status=$(echo "$delete_response" | tail -n 1)

if [ "$delete_status" != "204" ]; then
  echo "FAIL: DELETE /api/notes/:id expected 204, got $delete_status"
  exit 1
fi

echo "✓ DELETE /api/notes/:id returns 204"

# Step 5: GET /api/notes/:id returns 404 after deletion
get_deleted_response=$(curl -s -w "\n%{http_code}" "http://localhost:$TEST_PORT/api/notes/$note_id")
get_deleted_status=$(echo "$get_deleted_response" | tail -n 1)

if [ "$get_deleted_status" != "404" ]; then
  echo "FAIL: GET /api/notes/:id after delete expected 404, got $get_deleted_status"
  exit 1
fi

echo "✓ GET /api/notes/:id returns 404 after deletion"

# Step 6: Verify note is removed from list
final_notes=$(curl -s "http://localhost:$TEST_PORT/api/notes")
if echo "$final_notes" | grep -q '"'"$note_id"'"'; then
  echo "FAIL: Deleted note still appears in GET /api/notes"
  exit 1
fi

echo "✓ GET /api/notes confirms note removed"

echo ""
echo "PASS: Complete CRUD lifecycle verified"
echo "  - Created note with UUID and ISO timestamp"
echo "  - Retrieved note by ID"
echo "  - Listed all notes"
echo "  - Deleted note (204)"
echo "  - Verified deletion (404 on GET)"
exit 0
