#!/usr/bin/env bash
# Verification: API Input Validation and Error Handling
# PRD Reference: API Endpoints - POST validation requirements
# Vision Goal: System handles invalid input gracefully
# Category: integration
#
# NOTE: This test creates and deletes its own test data.
set -euo pipefail

echo "=== API Input Validation Test ==="

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

# Test 1: POST with missing title
response1=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:$TEST_PORT/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"body":"Note without title"}')
status1=$(echo "$response1" | tail -n 1)

if [ "$status1" != "400" ]; then
  echo "FAIL: POST without title expected 400, got $status1"
  exit 1
fi
echo "✓ POST without title returns 400"

# Test 2: POST with missing body
response2=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:$TEST_PORT/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"Note without body"}')
status2=$(echo "$response2" | tail -n 1)

if [ "$status2" != "400" ]; then
  echo "FAIL: POST without body expected 400, got $status2"
  exit 1
fi
echo "✓ POST without body returns 400"

# Test 3: POST with empty title
response3=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:$TEST_PORT/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"","body":"Body text"}')
status3=$(echo "$response3" | tail -n 1)

if [ "$status3" != "400" ]; then
  echo "FAIL: POST with empty title expected 400, got $status3"
  exit 1
fi
echo "✓ POST with empty title returns 400"

# Test 4: POST with empty body
response4=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:$TEST_PORT/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"Title","body":""}')
status4=$(echo "$response4" | tail -n 1)

if [ "$status4" != "400" ]; then
  echo "FAIL: POST with empty body expected 400, got $status4"
  exit 1
fi
echo "✓ POST with empty body returns 400"

# Test 5: POST with whitespace-only title
response5=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:$TEST_PORT/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"   ","body":"Body text"}')
status5=$(echo "$response5" | tail -n 1)

if [ "$status5" != "400" ]; then
  echo "FAIL: POST with whitespace-only title expected 400, got $status5"
  exit 1
fi
echo "✓ POST with whitespace-only title returns 400"

# Test 6: GET with non-existent ID
fake_id="00000000-0000-0000-0000-000000000000"
response6=$(curl -s -w "\n%{http_code}" "http://localhost:$TEST_PORT/api/notes/$fake_id")
status6=$(echo "$response6" | tail -n 1)

if [ "$status6" != "404" ]; then
  echo "FAIL: GET non-existent note expected 404, got $status6"
  exit 1
fi
echo "✓ GET non-existent note returns 404"

# Test 7: DELETE with non-existent ID
response7=$(curl -s -w "\n%{http_code}" -X DELETE "http://localhost:$TEST_PORT/api/notes/$fake_id")
status7=$(echo "$response7" | tail -n 1)

if [ "$status7" != "404" ]; then
  echo "FAIL: DELETE non-existent note expected 404, got $status7"
  exit 1
fi
echo "✓ DELETE non-existent note returns 404"

# Test 8: DELETE the same note twice (idempotency check)
# Create a note for this test
create_response=$(curl -s -X POST "http://localhost:$TEST_PORT/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"Validation Test - Delete Me","body":"This note tests double-delete behavior"}')
note_id=$(echo "$create_response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$note_id" ]; then
  echo "FAIL: Failed to create test note for delete-twice test"
  exit 1
fi

# First delete (should succeed)
delete1=$(curl -s -w "\n%{http_code}" -X DELETE "http://localhost:$TEST_PORT/api/notes/$note_id")
delete1_status=$(echo "$delete1" | tail -n 1)

if [ "$delete1_status" != "204" ]; then
  echo "FAIL: First DELETE expected 204, got $delete1_status"
  exit 1
fi

# Second delete (should return 404)
delete2=$(curl -s -w "\n%{http_code}" -X DELETE "http://localhost:$TEST_PORT/api/notes/$note_id")
delete2_status=$(echo "$delete2" | tail -n 1)

if [ "$delete2_status" != "404" ]; then
  echo "FAIL: Second DELETE expected 404, got $delete2_status"
  exit 1
fi
echo "✓ DELETE twice returns 204 then 404"

echo ""
echo "PASS: All API validation and error cases handled correctly"
echo "  - Missing/empty/whitespace title/body → 400"
echo "  - Non-existent note GET/DELETE → 404"
echo "  - Double delete → 404 on second attempt"
exit 0
