#!/bin/bash
# Integration test: Docker services start and respond

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Docker Services Integration Test ==="

cd "$PROJECT_DIR"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
  echo "FAIL: docker-compose.yml not found"
  exit 1
fi

# Check if services are running
echo "Checking service status..."
RUNNING_CONTAINERS=$(docker compose ps -q | wc -l)

if [ "$RUNNING_CONTAINERS" -lt 3 ]; then
  echo "FAIL: Expected 3 services, found $RUNNING_CONTAINERS running"
  exit 1
fi

echo "✓ All 3 services running"

# Test frontend responds
echo "Testing frontend..."
sleep 5  # Give services time to fully initialize
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4321 || echo "000")
if [ "$FRONTEND_RESPONSE" != "200" ]; then
  echo "FAIL: Frontend returned $FRONTEND_RESPONSE, expected 200"
  exit 1
fi
echo "✓ Frontend responding at http://localhost:4321"

# Test CMS admin responds (accept 200, 302, or 307 redirects)
echo "Testing CMS admin..."
CMS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/admin || echo "000")
if [ "$CMS_RESPONSE" != "200" ] && [ "$CMS_RESPONSE" != "302" ] && [ "$CMS_RESPONSE" != "307" ]; then
  echo "FAIL: CMS admin returned $CMS_RESPONSE, expected 200/302/307"
  exit 1
fi
echo "✓ CMS admin responding at http://localhost:3000/admin"

echo ""
echo "=== PASS: All services healthy and responding ==="
exit 0
