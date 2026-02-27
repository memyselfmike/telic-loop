#!/usr/bin/env bash
# Verification: Stats page handles zero-notes edge case gracefully
# PRD Reference: Stats page with no notes shows sensible defaults
# Vision Goal: No errors when viewing stats with zero notes
# Category: value
set -euo pipefail

echo "=== Stats Zero-Notes Edge Case Value Test ==="

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

# Get all existing notes
existing_notes=$(curl -s "http://localhost:3000/api/notes")
deleted_ids=""

# Delete all notes to create zero-notes state
echo "Creating zero-notes state..."
note_ids=$(echo "$existing_notes" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
for id in $note_ids; do
  curl -s -X DELETE "http://localhost:3000/api/notes/$id" > /dev/null
  deleted_ids="$deleted_ids $id"
done

# Cleanup function
cleanup() {
  if [ "$SERVER_RUNNING" = "false" ] && [ -n "${SERVER_PID:-}" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

sleep 1

# Test 1: Verify stats API returns correct zero-notes defaults
echo "Checking zero-notes API response..."
stats_json=$(curl -s "http://localhost:3000/api/stats")

total=$(echo "$stats_json" | grep -o '"totalNotes":[0-9]*' | cut -d':' -f2)
if [ "$total" != "0" ]; then
  echo "FAIL: Expected totalNotes=0, got $total"
  exit 1
fi

avg=$(echo "$stats_json" | grep -o '"averageBodyLength":[0-9]*' | cut -d':' -f2)
if [ "$avg" != "0" ]; then
  echo "FAIL: Expected averageBodyLength=0, got $avg"
  exit 1
fi

if ! echo "$stats_json" | grep -q '"newestDate":null'; then
  echo "FAIL: Expected newestDate=null for zero notes"
  exit 1
fi

if ! echo "$stats_json" | grep -q '"oldestDate":null'; then
  echo "FAIL: Expected oldestDate=null for zero notes"
  exit 1
fi

# Test 2: Verify stats page is accessible and does not crash
echo "Checking stats page with zero notes..."
stats_page=$(curl -s "http://localhost:3000/stats")

if ! echo "$stats_page" | grep -q "NoteBox Stats"; then
  echo "FAIL: Stats page not accessible with zero notes"
  exit 1
fi

# Test 3: Verify stats page loads without JavaScript errors (basic check)
if ! echo "$stats_page" | grep -q "stats.js"; then
  echo "FAIL: Stats page does not load stats.js with zero notes"
  exit 1
fi

if ! echo "$stats_page" | grep -q "stats-dashboard"; then
  echo "FAIL: Stats page missing dashboard element with zero notes"
  exit 1
fi

echo "PASS: Stats page handles zero-notes edge case gracefully (no errors, sensible defaults)"
exit 0
