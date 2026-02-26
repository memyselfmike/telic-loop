#!/usr/bin/env bash
# Verification: Express server starts on configurable PORT
# PRD Reference: Architecture - server.js, Non-Functional Requirements
# Vision Goal: Infrastructure foundation
# Category: unit
set -euo pipefail

echo "=== Unit: Server Starts on Configurable PORT ==="

cd "$(dirname "$0")/../.."

# Use isolated port
TEST_PORT="${PORT:-3000}"

# Start server with isolated port
PORT="$TEST_PORT" timeout 10 node server.js &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT

# Wait for server to start
sleep 2

# Check if server is responding
if curl -sf "http://localhost:$TEST_PORT" > /dev/null; then
  echo "PASS: Server started successfully on port $TEST_PORT"
  exit 0
else
  echo "FAIL: Server did not respond on port $TEST_PORT"
  exit 1
fi
