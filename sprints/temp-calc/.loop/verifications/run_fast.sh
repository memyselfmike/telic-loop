#!/usr/bin/env bash
# Fast verification runner - executes only unit tests for quick regression checks
# Use this during development for rapid feedback
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== FAST VERIFICATION: Unit Tests Only ==="
echo ""
echo "Running comprehensive unit tests (28 test cases)..."
echo "This provides fast regression protection during development."
echo ""

python unit_test_temp_calc.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Fast verification passed!"
    echo "All 28 unit tests are green. Core functionality intact."
    echo ""
    echo "For complete verification (integration + value), run: bash run_all.sh"
    echo ""
    exit 0
else
    echo ""
    echo "❌ Fast verification failed!"
    echo "Fix unit test failures before proceeding."
    echo ""
    exit 1
fi
