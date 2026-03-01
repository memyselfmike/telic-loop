#!/usr/bin/env bash
# Verification: Server Serves Static Files and Responds to HTTP Requests
# PRD Reference: Tech Stack - Node.js + Express on port 3000
# Vision Goal: User opens http://localhost:3000 in browser and sees the app
# Category: value
set -euo pipefail

echo "=== Server and Static Files Test ==="

cd "$(dirname "$0")/../.."

# Use port from environment
TEST_PORT="${PORT:-3000}"

# Wait for server to be ready
echo "Waiting for server on port $TEST_PORT..."
for i in {1..10}; do
  if curl -s "http://localhost:$TEST_PORT/" > /dev/null 2>&1; then
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

# Test 1: Server responds to root path
root_response=$(curl -s -w "\n%{http_code}" "http://localhost:$TEST_PORT/")
root_body=$(echo "$root_response" | head -n -1)
root_status=$(echo "$root_response" | tail -n 1)

if [ "$root_status" != "200" ]; then
  echo "FAIL: GET / expected 200, got $root_status"
  exit 1
fi
echo "✓ GET / returns 200"

# Test 2: Root path serves HTML
if ! echo "$root_body" | grep -q "<!DOCTYPE html>"; then
  echo "FAIL: GET / does not return HTML (missing DOCTYPE)"
  exit 1
fi

if ! echo "$root_body" | grep -q "<html"; then
  echo "FAIL: GET / does not return valid HTML (missing <html> tag)"
  exit 1
fi
echo "✓ GET / returns valid HTML"

# Test 3: HTML includes NoteBox title
if ! echo "$root_body" | grep -q "NoteBox"; then
  echo "FAIL: HTML does not contain 'NoteBox' branding"
  exit 1
fi
echo "✓ HTML includes NoteBox branding"

# Test 4: API endpoint is accessible
api_response=$(curl -s -w "\n%{http_code}" "http://localhost:$TEST_PORT/api/notes")
api_status=$(echo "$api_response" | tail -n 1)

if [ "$api_status" != "200" ]; then
  echo "FAIL: GET /api/notes expected 200, got $api_status"
  exit 1
fi
echo "✓ GET /api/notes accessible (200)"

# Test 5: API returns JSON array
api_body=$(echo "$api_response" | head -n -1)
if ! echo "$api_body" | grep -qE '^\[.*\]$'; then
  echo "FAIL: API does not return JSON array"
  echo "Response: $api_body"
  exit 1
fi
echo "✓ GET /api/notes returns JSON array"

# Test 6: Server accepts POST requests with JSON (creates test data and cleans up)
post_response=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:$TEST_PORT/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"Server Test","body":"Testing JSON parsing and response"}')
post_status=$(echo "$post_response" | tail -n 1)

if [ "$post_status" != "201" ]; then
  echo "FAIL: POST /api/notes expected 201, got $post_status"
  exit 1
fi
echo "✓ POST /api/notes accepts JSON (201)"

# Verify express.json() middleware works by checking response echoes data
post_body=$(echo "$post_response" | head -n -1)
if ! echo "$post_body" | grep -q '"title":"Server Test"'; then
  echo "FAIL: POST response does not echo back JSON correctly"
  exit 1
fi

# Clean up test note
test_note_id=$(echo "$post_body" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$test_note_id" ]; then
  curl -s -X DELETE "http://localhost:$TEST_PORT/api/notes/$test_note_id" > /dev/null
fi

echo "✓ express.json() middleware active (parses request body)"

# Test 7: Static file serving works (index.html accessible)
index_response=$(curl -s -w "\n%{http_code}" "http://localhost:$TEST_PORT/index.html")
index_status=$(echo "$index_response" | tail -n 1)

if [ "$index_status" != "200" ]; then
  echo "FAIL: GET /index.html expected 200, got $index_status"
  exit 1
fi
echo "✓ Static files served from public/ directory"

echo ""
echo "PASS: Server and static file serving verified"
echo "  - Server runs and responds on port $TEST_PORT"
echo "  - Root path (/) serves HTML with NoteBox branding"
echo "  - API endpoints accessible and return JSON"
echo "  - JSON parsing middleware active"
echo "  - Static files served from public/ directory"
exit 0
