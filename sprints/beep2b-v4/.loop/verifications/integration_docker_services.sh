#!/bin/bash
# Integration: Docker services all running and healthy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

echo "=== Verifying Docker Services ==="

# Check all 3 services are running
echo "Checking services are running..."
RUNNING_COUNT=$(docker compose ps --format json | jq -r '.State' | grep -c "running" || true)

if [ "$RUNNING_COUNT" -ne 3 ]; then
  echo "FAIL: Expected 3 running services, found $RUNNING_COUNT"
  docker compose ps
  exit 1
fi

echo "✓ All 3 services running"

# Check MongoDB is healthy
echo "Checking MongoDB health..."
DB_HEALTH=$(docker compose ps db --format json | jq -r '.Health' || echo "")

if [ "$DB_HEALTH" != "healthy" ]; then
  echo "FAIL: MongoDB not healthy (status: $DB_HEALTH)"
  exit 1
fi

echo "✓ MongoDB healthy"

# Check frontend is accessible
echo "Checking frontend responds..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4321/ || echo "000")

if [ "$FRONTEND_STATUS" != "200" ]; then
  echo "FAIL: Frontend not responding (HTTP $FRONTEND_STATUS)"
  exit 1
fi

echo "✓ Frontend responding (HTTP 200)"

# Check CMS admin is accessible
echo "Checking CMS admin..."
CMS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/admin || echo "000")

if [ "$CMS_STATUS" != "200" ]; then
  echo "FAIL: CMS admin not responding (HTTP $CMS_STATUS)"
  exit 1
fi

echo "✓ CMS admin responding (HTTP 200)"

# Check CMS API is accessible
echo "Checking CMS API..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/api/posts || echo "000")

if [ "$API_STATUS" != "200" ]; then
  echo "FAIL: CMS API not responding (HTTP $API_STATUS)"
  exit 1
fi

echo "✓ CMS API responding (HTTP 200)"

echo "=== Docker Services Verification PASSED ==="
exit 0
