#!/usr/bin/env bash
# Verification: User can navigate between notes list and stats pages
# PRD Reference: Navigation links between pages
# Vision Goal: Switch to a stats page and back to notes list
# Category: value
set -euo pipefail

echo "=== Stats UI Navigation Value Test ==="

cd "$(dirname "$0")/../.."

# Check if server is already running
if curl -s "http://localhost:3000/" > /dev/null 2>&1; then
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
    if curl -s "http://localhost:3000/" > /dev/null 2>&1; then
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
  if [ "$SERVER_RUNNING" = "false" ] && [ -n "${SERVER_PID:-}" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Test 1: Verify notes list page (/) is accessible
echo "Checking notes list page..."
notes_page=$(curl -s "http://localhost:3000/")
if ! echo "$notes_page" | grep -q "NoteBox"; then
  echo "FAIL: Notes list page not accessible or missing title"
  exit 1
fi

# Test 2: Verify notes page has link to stats
echo "Checking for Stats link on notes page..."
if ! echo "$notes_page" | grep -qi "stats"; then
  echo "FAIL: Notes page missing link to stats"
  exit 1
fi

# Test 3: Verify stats page (/stats) is accessible
echo "Checking stats page..."
stats_page=$(curl -s "http://localhost:3000/stats")
if ! echo "$stats_page" | grep -q "NoteBox Stats"; then
  echo "FAIL: Stats page not accessible or missing title"
  exit 1
fi

# Test 4: Verify stats page has back-to-notes link
echo "Checking for back-to-notes link on stats page..."
if ! echo "$stats_page" | grep -q "Back to Notes"; then
  echo "FAIL: Stats page missing back-to-notes link"
  exit 1
fi

# Test 5: Verify stats page references stats.js
echo "Checking stats page loads stats.js..."
if ! echo "$stats_page" | grep -q "stats.js"; then
  echo "FAIL: Stats page does not load stats.js"
  exit 1
fi

echo "PASS: User can navigate between notes list and stats pages"
exit 0
