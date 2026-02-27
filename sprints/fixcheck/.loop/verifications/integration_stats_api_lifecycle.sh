#!/usr/bin/env bash
# Verification: Stats API reflects note CRUD operations correctly
# PRD Reference: GET /api/stats responds to note creation/deletion
# Vision Goal: Stats update dynamically as notes change
# Category: integration
# NOTE: This test modifies shared data - runs sequentially, not in parallel
set -euo pipefail

echo "=== Stats API Lifecycle Integration Test ==="

cd "$(dirname "$0")/../.."

# Check if server is already running
if curl -s "http://localhost:3000/api/stats" > /dev/null 2>&1; then
  SERVER_RUNNING=true
  echo "Using existing server on port 3000"
else
  SERVER_RUNNING=false
  echo "Starting server on port 3000"
  node server.js > /dev/null 2>&1 &
  SERVER_PID=$!

  # Wait for server to be ready
  max_attempts=10
  attempt=0
  while [ $attempt -lt $max_attempts ]; do
    if curl -s "http://localhost:3000/api/stats" > /dev/null 2>&1; then
      break
    fi
    attempt=$((attempt + 1))
    sleep 1
  done

  if [ $attempt -eq $max_attempts ]; then
    echo "FAIL: Server failed to start"
    exit 1
  fi
fi

# Cleanup function
cleanup() {
  # Clean up test notes
  if [ -n "${note1_id:-}" ]; then
    curl -s -X DELETE "http://localhost:3000/api/notes/$note1_id" > /dev/null 2>&1 || true
  fi
  if [ -n "${note2_id:-}" ]; then
    curl -s -X DELETE "http://localhost:3000/api/notes/$note2_id" > /dev/null 2>&1 || true
  fi

  # Stop server if we started it
  if [ "$SERVER_RUNNING" = "false" ] && [ -n "${SERVER_PID:-}" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Get initial stats
initial_response=$(curl -s "http://localhost:3000/api/stats")
initial_total=$(echo "$initial_response" | grep -o '"totalNotes":[0-9]*' | cut -d':' -f2)

echo "Initial note count: $initial_total"

# Create first note
echo "Creating first note..."
note1=$(curl -s -X POST "http://localhost:3000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"[TEST] Lifecycle Note 1","body":"Short body"}')
note1_id=$(echo "$note1" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$note1_id" ]; then
  echo "FAIL: Failed to create first note"
  exit 1
fi

# Verify stats increased by 1
stats1=$(curl -s "http://localhost:3000/api/stats")
total1=$(echo "$stats1" | grep -o '"totalNotes":[0-9]*' | cut -d':' -f2)
expected1=$((initial_total + 1))
if [ "$total1" != "$expected1" ]; then
  echo "FAIL: Expected totalNotes=$expected1 after first note, got $total1"
  exit 1
fi

# Create second note
echo "Creating second note..."
note2=$(curl -s -X POST "http://localhost:3000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"[TEST] Lifecycle Note 2","body":"This is a much longer body to change the average significantly"}')
note2_id=$(echo "$note2" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$note2_id" ]; then
  echo "FAIL: Failed to create second note"
  exit 1
fi

# Verify stats increased by 1 again
stats2=$(curl -s "http://localhost:3000/api/stats")
total2=$(echo "$stats2" | grep -o '"totalNotes":[0-9]*' | cut -d':' -f2)
expected2=$((initial_total + 2))
if [ "$total2" != "$expected2" ]; then
  echo "FAIL: Expected totalNotes=$expected2 after second note, got $total2"
  exit 1
fi

# Delete first note
echo "Deleting first note..."
delete_response=$(curl -s -w "%{http_code}" -o /dev/null -X DELETE "http://localhost:3000/api/notes/$note1_id")

if [ "$delete_response" != "204" ]; then
  echo "FAIL: Failed to delete first note (HTTP $delete_response)"
  exit 1
fi

# Verify stats decreased by 1
stats3=$(curl -s "http://localhost:3000/api/stats")
total3=$(echo "$stats3" | grep -o '"totalNotes":[0-9]*' | cut -d':' -f2)
expected3=$((initial_total + 1))
if [ "$total3" != "$expected3" ]; then
  echo "FAIL: Expected totalNotes=$expected3 after first deletion, got $total3"
  exit 1
fi

# Delete second note
echo "Deleting second note..."
delete_response2=$(curl -s -w "%{http_code}" -o /dev/null -X DELETE "http://localhost:3000/api/notes/$note2_id")

if [ "$delete_response2" != "204" ]; then
  echo "FAIL: Failed to delete second note (HTTP $delete_response2)"
  exit 1
fi

# Verify stats returned to initial state
stats4=$(curl -s "http://localhost:3000/api/stats")
total4=$(echo "$stats4" | grep -o '"totalNotes":[0-9]*' | cut -d':' -f2)
if [ "$total4" != "$initial_total" ]; then
  echo "FAIL: Expected totalNotes=$initial_total after all deletions, got $total4"
  exit 1
fi

echo "PASS: Stats API correctly reflects note creation and deletion lifecycle"
exit 0
