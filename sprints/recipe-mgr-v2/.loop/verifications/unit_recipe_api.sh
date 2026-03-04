#!/usr/bin/env bash
# Verification: Recipe API Unit Tests
# PRD Reference: Section 3.1 (Recipe CRUD Endpoints), Section 2.3 (Seed Data)
# Vision Goal: "Build a Recipe Collection" - API endpoints for CRUD operations
# Category: unit

set -euo pipefail

echo "=== Recipe API Unit Tests ==="
echo "Running pytest test suite for recipe endpoints..."

cd "$(dirname "$0")/../.."

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "FAIL: pytest not found. Install with: pip install pytest"
    exit 1
fi

# Check if backend dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "FAIL: FastAPI not installed. Install with: pip install -r backend/requirements.txt"
    exit 1
fi

# Run pytest with verbose output
pytest tests/test_api.py -v --tb=short

if [ $? -eq 0 ]; then
    echo ""
    echo "PASS: All recipe API unit tests passed"
    exit 0
else
    echo ""
    echo "FAIL: Some pytest tests failed"
    exit 1
fi
