#!/usr/bin/env bash
# Verification: Developer can convert temperatures from command line exactly as Vision promises
# PRD Reference: Section 4 (all acceptance criteria)
# Vision Goal: "Developer can run a single command and instantly see the converted temperature"
# Category: value
#
# This script simulates the actual user workflow described in the Vision:
# A developer working on a project needs quick temperature conversions without leaving the terminal.
set -euo pipefail

echo "=== VALUE DELIVERY: User Workflow Verification ==="
echo ""
echo "Simulating developer using temp_calc.py for quick conversions..."
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPRINT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMP_CALC="$SPRINT_DIR/temp_calc.py"

# Check script exists
if [[ ! -f "$TEMP_CALC" ]]; then
    echo "FAIL: temp_calc.py not found at $TEMP_CALC"
    exit 1
fi

FAILURES=0

# Helper function to test a conversion
test_conversion() {
    local desc="$1"
    local input_val="$2"
    local from_scale="$3"
    local to_scale="$4"
    local expected="$5"

    echo "  Testing: $desc"
    echo "    Command: python temp_calc.py $input_val $from_scale $to_scale"

    output=$(python "$TEMP_CALC" "$input_val" "$from_scale" "$to_scale" 2>/dev/null || true)

    if [[ "$output" == "$expected" ]]; then
        echo "    ✓ Got expected output: $output"
        echo ""
        return 0
    else
        echo "    ✗ FAIL: Expected '$expected', got '$output'"
        echo ""
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# Helper function to test error handling
test_error() {
    local desc="$1"
    shift
    local args=("$@")

    echo "  Testing: $desc"
    echo "    Command: python temp_calc.py ${args[*]}"

    # Run command and capture exit code
    set +e
    python "$TEMP_CALC" "${args[@]}" > /dev/null 2>&1
    exit_code=$?
    set -e

    if [[ $exit_code -ne 0 ]]; then
        echo "    ✓ Correctly exited with non-zero code ($exit_code)"
        echo ""
        return 0
    else
        echo "    ✗ FAIL: Should have exited with error, but succeeded"
        echo ""
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

echo "1. Core conversions from Vision success signals:"
echo ""
test_conversion \
    "100°C to Fahrenheit (boiling point)" \
    "100" "C" "F" "212.00"

test_conversion \
    "32°F to Celsius (freezing point)" \
    "32" "F" "C" "0.00"

test_conversion \
    "0K to Celsius (absolute zero)" \
    "0" "K" "C" "-273.15"

echo "2. Case-insensitive usage (real-world developer behavior):"
echo ""
test_conversion \
    "Body temperature in lowercase" \
    "98.6" "f" "c" "37.00"

echo "3. Additional conversion directions (completeness):"
echo ""
test_conversion \
    "Celsius to Kelvin" \
    "100" "C" "K" "373.15"

test_conversion \
    "Fahrenheit to Kelvin" \
    "212" "F" "K" "373.15"

test_conversion \
    "Kelvin to Fahrenheit" \
    "273.15" "K" "F" "32.00"

echo "4. Error handling (prevents confusion):"
echo ""
test_error \
    "No arguments shows usage" \

test_error \
    "Invalid number shows error" \
    "abc" "C" "F"

test_error \
    "Invalid scale shows error" \
    "100" "X" "F"

echo "5. Edge cases (robustness):"
echo ""
test_conversion \
    "Same scale returns formatted input" \
    "100" "C" "C" "100.00"

test_conversion \
    "Negative temperature (winter)" \
    "-40" "C" "F" "-40.00"

# Test below absolute zero (should still convert but warn)
echo "  Testing: Below absolute zero (warns but converts)"
echo "    Command: python temp_calc.py -500 C F"
output=$(python "$TEMP_CALC" -500 C F 2>&1)
stdout=$(echo "$output" | grep -v "Warning" || true)
stderr=$(echo "$output" | grep "Warning" || true)

if [[ "$stdout" == "-868.00" && -n "$stderr" ]]; then
    echo "    ✓ Converted correctly and showed warning"
    echo ""
else
    echo "    ✗ FAIL: Expected conversion with warning"
    echo "      stdout: $stdout"
    echo "      stderr: $stderr"
    echo ""
    FAILURES=$((FAILURES + 1))
fi

# Summary
echo "=================================================="
if [[ $FAILURES -eq 0 ]]; then
    echo "PASS: All user workflow scenarios succeeded!"
    echo ""
    echo "VALUE DELIVERED:"
    echo "  ✓ Developer can instantly convert temperatures from command line"
    echo "  ✓ No need to open browser or interrupt workflow"
    echo "  ✓ Clear error messages prevent confusion"
    echo "  ✓ Handles all common cases (C/F/K, positive/negative, edge cases)"
    echo ""
    exit 0
else
    echo "FAIL: $FAILURES scenario(s) failed"
    echo ""
    echo "VALUE NOT DELIVERED: User cannot rely on tool for conversions"
    echo ""
    exit 1
fi
