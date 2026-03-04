#!/bin/bash
# Unit verification: Run pytest test suite
# Tests all backend API endpoints with comprehensive coverage

set -e
cd "$(dirname "$0")/../.."

echo "Running pytest test suite..."
python -m pytest tests/test_api.py -v --tb=short

echo "✓ All backend API tests passing"
exit 0
