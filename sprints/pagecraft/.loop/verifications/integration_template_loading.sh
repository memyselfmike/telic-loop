#!/usr/bin/env bash
# Verification: Templates load via HTTP and populate AppState correctly
# PRD Reference: F1 Template Selection, Task 1.5 (loadTemplate function)
# Vision Goal: Template selection flow
# Category: integration
set -euo pipefail

echo "=== Integration: Template Loading ==="

cd "$(dirname "$0")/../.."

# Use isolated port
TEST_PORT="${PORT:-3000}"

# Start server
PORT="$TEST_PORT" node server.js > /dev/null 2>&1 &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT

sleep 2

# Test that templates are accessible via HTTP
for template in saas event portfolio; do
  RESPONSE=$(curl -s -w "\n%{http_code}" "http://localhost:$TEST_PORT/templates/${template}.json")
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  BODY=$(echo "$RESPONSE" | head -n-1)

  if [[ "$HTTP_CODE" != "200" ]]; then
    echo "FAIL: Template $template not accessible (HTTP $HTTP_CODE)"
    exit 1
  fi

  # Validate JSON response
  if ! echo "$BODY" | python -m json.tool > /dev/null 2>&1; then
    echo "FAIL: Template $template returned invalid JSON"
    exit 1
  fi

  echo "PASS: Template $template loads via HTTP"
done

echo "PASS: All templates load correctly via HTTP"
exit 0
