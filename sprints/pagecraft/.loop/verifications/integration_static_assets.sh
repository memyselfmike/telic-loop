#!/usr/bin/env bash
# Verification: All static assets (CSS, JS) are served correctly
# PRD Reference: Architecture - Express serves static files
# Vision Goal: Asset delivery
# Category: integration
set -euo pipefail

echo "=== Integration: Static Assets Served ==="

cd "$(dirname "$0")/../.."

# Use isolated port
TEST_PORT="${PORT:-3000}"

# Start server
PORT="$TEST_PORT" node server.js > /dev/null 2>&1 &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT

sleep 2

FAIL=0

# Check CSS files
for css in app.css templates.css; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$TEST_PORT/css/$css")
  if [[ "$HTTP_CODE" != "200" ]]; then
    echo "FAIL: CSS file $css not accessible (HTTP $HTTP_CODE)"
    FAIL=1
  else
    echo "PASS: CSS file $css served correctly"
  fi
done

# Check JS files
for js in app.js templates.js; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$TEST_PORT/js/$js")
  if [[ "$HTTP_CODE" != "200" ]]; then
    echo "FAIL: JS file $js not accessible (HTTP $HTTP_CODE)"
    FAIL=1
  else
    echo "PASS: JS file $js served correctly"
  fi
done

# Check index.html
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$TEST_PORT/")
if [[ "$HTTP_CODE" != "200" ]]; then
  echo "FAIL: index.html not accessible (HTTP $HTTP_CODE)"
  FAIL=1
else
  echo "PASS: index.html served correctly"
fi

if [[ $FAIL -eq 0 ]]; then
  echo "PASS: All static assets served correctly"
  exit 0
else
  exit 1
fi
