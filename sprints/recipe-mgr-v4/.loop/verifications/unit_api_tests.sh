#!/usr/bin/bash
# Unit/API Integration Tests
# Tests all backend API endpoints with pytest

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

# Run pytest tests
echo "Running API integration tests..."
python -m pytest tests/test_api.py -v --tb=short

exit 0
