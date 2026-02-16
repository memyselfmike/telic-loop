#!/usr/bin/env bash
# Verification: Developer can use tool as quick reference without memorization
# PRD Reference: Section 2.2 (CLI Interface)
# Vision Goal: "Quickly convert temperatures without interrupting workflow"
# Category: value
#
# This script verifies the tool is intuitive and helpful for a developer
# who doesn't remember the exact syntax - they should be able to figure it out
# quickly without reading documentation.
set -euo pipefail

echo "=== VALUE DELIVERY: Quick Reference Usability ==="
echo ""
echo "Testing that a developer can figure out how to use the tool easily..."
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPRINT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMP_CALC="$SPRINT_DIR/temp_calc.py"

# Check script exists
if [[ ! -f "$TEMP_CALC" ]]; then
    echo "FAIL: temp_calc.py not found at $TEMP_CALC"
    exit 1
fi

echo "1. Running with no args shows helpful usage:"
echo "   Command: python temp_calc.py"
echo ""

output=$(python "$TEMP_CALC" 2>&1 || true)

# Check for key elements of helpful usage
if [[ "$output" =~ "Usage:" ]]; then
    echo "   ✓ Shows 'Usage:' header"
else
    echo "   ✗ FAIL: No 'Usage:' header found"
    exit 1
fi

if [[ "$output" =~ "value" && "$output" =~ "from_scale" && "$output" =~ "to_scale" ]]; then
    echo "   ✓ Explains required arguments"
else
    echo "   ✗ FAIL: Doesn't explain arguments"
    exit 1
fi

if [[ "$output" =~ "Examples:" ]]; then
    echo "   ✓ Provides examples"
else
    echo "   ✗ FAIL: No examples provided"
    exit 1
fi

if [[ "$output" =~ "C" && "$output" =~ "F" && "$output" =~ "K" ]]; then
    echo "   ✓ Shows which scales are supported (C, F, K)"
else
    echo "   ✗ FAIL: Doesn't show supported scales"
    exit 1
fi

echo ""
echo "2. Error messages are clear and actionable:"
echo ""

# Test invalid number
echo "   Testing invalid number error..."
error_output=$(python "$TEMP_CALC" "not-a-number" "C" "F" 2>&1 || true)

if [[ "$error_output" =~ "Error:" && "$error_output" =~ "not a valid number" ]]; then
    echo "   ✓ Invalid number produces clear error"
else
    echo "   ✗ FAIL: Invalid number error not clear"
    echo "      Got: $error_output"
    exit 1
fi

# Test invalid scale
echo "   Testing invalid scale error..."
error_output=$(python "$TEMP_CALC" "100" "X" "F" 2>&1 || true)

if [[ "$error_output" =~ "Error:" && "$error_output" =~ "not a valid scale" ]]; then
    echo "   ✓ Invalid scale produces clear error"
else
    echo "   ✗ FAIL: Invalid scale error not clear"
    echo "      Got: $error_output"
    exit 1
fi

if [[ "$error_output" =~ "C, F, or K" || "$error_output" =~ "C" && "$error_output" =~ "F" && "$error_output" =~ "K" ]]; then
    echo "   ✓ Error message shows valid scales"
else
    echo "   ✗ FAIL: Error doesn't show valid scales"
    echo "      Got: $error_output"
    exit 1
fi

echo ""
echo "3. Output is clean and parseable:"
echo ""

# Test that output is just the number (can be piped, used in scripts)
output=$(python "$TEMP_CALC" "100" "C" "F" 2>/dev/null)

if [[ "$output" == "212.00" ]]; then
    echo "   ✓ Output is clean (no extra text, just the number)"
else
    echo "   ✗ FAIL: Output contains extra text or wrong value"
    echo "      Got: '$output'"
    exit 1
fi

# Verify output can be used in math
if python -c "import sys; sys.exit(0 if float('$output') > 200 else 1)" 2>/dev/null; then
    echo "   ✓ Output is numeric and can be used in calculations"
else
    echo "   ✗ FAIL: Output is not properly numeric"
    exit 1
fi

echo ""
echo "4. Tool is forgiving with input:"
echo ""

# Case insensitivity
output_lower=$(python "$TEMP_CALC" "100" "c" "f" 2>/dev/null)
output_upper=$(python "$TEMP_CALC" "100" "C" "F" 2>/dev/null)

if [[ "$output_lower" == "$output_upper" ]]; then
    echo "   ✓ Case-insensitive (c and C both work)"
else
    echo "   ✗ FAIL: Case-sensitive (forces developer to remember exact case)"
    exit 1
fi

# Floats work
output=$(python "$TEMP_CALC" "98.6" "F" "C" 2>/dev/null)
if [[ "$output" == "37.00" ]]; then
    echo "   ✓ Accepts decimal values"
else
    echo "   ✗ FAIL: Doesn't handle decimal inputs correctly"
    exit 1
fi

echo ""
echo "=================================================="
echo "PASS: Tool is intuitive and helpful!"
echo ""
echo "VALUE DELIVERED:"
echo "  ✓ Developer can figure out usage without docs (helpful usage message)"
echo "  ✓ Error messages are clear and guide the user"
echo "  ✓ Output is clean and scriptable"
echo "  ✓ Tool is forgiving with input (case-insensitive, handles decimals)"
echo ""
echo "This means: Developer can use tool immediately without context switching"
echo ""
exit 0
