#!/usr/bin/env bash
# Verification: Notes CRUD API endpoints
# PRD Reference: API Endpoints - GET/POST/GET/:id/DELETE/:id
# Vision Goal: Create, view, and delete notes via REST API
# Category: integration
set -euo pipefail

echo "=== Integration: Notes CRUD API ==="

cd "$(dirname "$0")/../.."

# Run the existing Jest API tests which use Supertest (no server startup needed)
# This tests all 4 CRUD endpoints: GET /api/notes, POST /api/notes,
# GET /api/notes/:id, DELETE /api/notes/:id
npx jest tests/api.test.js --verbose --forceExit 2>&1
JEST_EXIT=$?

if [ $JEST_EXIT -eq 0 ]; then
  echo ""
  echo "PASS: All API endpoints verified"
  exit 0
else
  echo ""
  echo "FAIL: Some tests failed"
  exit 1
fi
