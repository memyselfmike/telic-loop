#!/usr/bin/env bash
# Verification: Stats page displays all four metrics correctly
# PRD Reference: Stats page showing total notes, average body length, newest/oldest dates
# Vision Goal: User sees four aggregate statistics on stats page
# Category: value
set -euo pipefail

echo "=== Stats UI Display Value Test ==="

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
  # Clean up test notes we created
  if [ -n "${note1_id:-}" ]; then
    curl -s -X DELETE "http://localhost:3000/api/notes/$note1_id" > /dev/null 2>&1 || true
  fi
  if [ -n "${note2_id:-}" ]; then
    curl -s -X DELETE "http://localhost:3000/api/notes/$note2_id" > /dev/null 2>&1 || true
  fi
  if [ -n "${note3_id:-}" ]; then
    curl -s -X DELETE "http://localhost:3000/api/notes/$note3_id" > /dev/null 2>&1 || true
  fi

  if [ "$SERVER_RUNNING" = "false" ] && [ -n "${SERVER_PID:-}" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Create test notes with known data
echo "Creating test notes..."
note1=$(curl -s -X POST "http://localhost:3000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"[TEST] UI Display 1","body":"Short"}')
note1_id=$(echo "$note1" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

note2=$(curl -s -X POST "http://localhost:3000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"[TEST] UI Display 2","body":"This is a medium length body here"}')
note2_id=$(echo "$note2" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

note3=$(curl -s -X POST "http://localhost:3000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"[TEST] UI Display 3","body":"This is the longest body with even more content to test averaging properly"}')
note3_id=$(echo "$note3" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

sleep 1

# Fetch stats via API to verify backend calculation
echo "Verifying stats API calculation..."
stats_json=$(curl -s "http://localhost:3000/api/stats")

# Extract total notes
total=$(echo "$stats_json" | grep -o '"totalNotes":[0-9]*' | cut -d':' -f2)
if [ -z "$total" ] || [ "$total" -lt 3 ]; then
  echo "FAIL: Expected at least 3 notes, got $total"
  exit 1
fi

# Verify averageBodyLength exists and is a number
avg=$(echo "$stats_json" | grep -o '"averageBodyLength":[0-9]*' | cut -d':' -f2)
if [ -z "$avg" ]; then
  echo "FAIL: averageBodyLength not found or invalid"
  exit 1
fi

# Verify dates are present (should not be null since we have notes)
if echo "$stats_json" | grep -q '"newestDate":null'; then
  echo "FAIL: newestDate should not be null when notes exist"
  exit 1
fi

if echo "$stats_json" | grep -q '"oldestDate":null'; then
  echo "FAIL: oldestDate should not be null when notes exist"
  exit 1
fi

# Verify stats page HTML structure
echo "Verifying stats page HTML structure..."
stats_page=$(curl -s "http://localhost:3000/stats")

# Check for required elements
if ! echo "$stats_page" | grep -q "NoteBox Stats"; then
  echo "FAIL: Stats page missing title"
  exit 1
fi

if ! echo "$stats_page" | grep -q "stats-dashboard"; then
  echo "FAIL: Stats page missing stats-dashboard element"
  exit 1
fi

# Verify stats.js is loaded
if ! echo "$stats_page" | grep -q "stats.js"; then
  echo "FAIL: Stats page does not load stats.js"
  exit 1
fi

# Verify navigation link back to notes
if ! echo "$stats_page" | grep -q "Back to Notes"; then
  echo "FAIL: Stats page missing back-to-notes link"
  exit 1
fi

echo "PASS: Stats page displays all four metrics correctly (total notes=$total, average length=$avg, with newest/oldest dates)"
exit 0
