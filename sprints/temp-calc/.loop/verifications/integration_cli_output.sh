#!/usr/bin/env bash
# Verification: CLI integration - stdout/stderr/exit codes work correctly
# PRD Reference: Section 2.2 (CLI Interface), Section 2.3 (Error Handling)
# Vision Goal: Clean integration into developer's shell workflow
# Category: integration
#
# This script verifies that temp_calc.py integrates properly as a CLI tool:
# - stdout contains only the converted value
# - stderr contains only errors/warnings
# - exit codes follow Unix conventions (0 = success, 1 = error)
# - can be piped, redirected, and used in scripts
set -euo pipefail

echo "=== INTEGRATION: CLI Output Streams & Exit Codes ==="
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

echo "1. Successful conversions:"
echo ""

# Test stdout contains only the result
echo "   Testing stdout isolation..."
output=$(python "$TEMP_CALC" "100" "C" "F" 2>/dev/null)
if [[ "$output" == "212.00" ]]; then
    echo "   ✓ stdout contains only result (no extra text)"
else
    echo "   ✗ FAIL: stdout contains unexpected content: '$output'"
    FAILURES=$((FAILURES + 1))
fi

# Test stderr is empty on success
stderr_output=$(python "$TEMP_CALC" "100" "C" "F" 2>&1 >/dev/null)
if [[ -z "$stderr_output" ]]; then
    echo "   ✓ stderr is empty on success"
else
    echo "   ✗ FAIL: stderr contains unexpected content: '$stderr_output'"
    FAILURES=$((FAILURES + 1))
fi

# Test exit code 0 on success
set +e
python "$TEMP_CALC" "100" "C" "F" >/dev/null 2>&1
exit_code=$?
set -e
if [[ $exit_code -eq 0 ]]; then
    echo "   ✓ exit code 0 on success"
else
    echo "   ✗ FAIL: exit code is $exit_code (expected 0)"
    FAILURES=$((FAILURES + 1))
fi

echo ""
echo "2. Error handling - no arguments:"
echo ""

# Usage goes to stdout (convention: help text goes to stdout)
stdout=$(python "$TEMP_CALC" 2>/dev/null || true)
if [[ "$stdout" =~ "Usage:" ]]; then
    echo "   ✓ usage message on stdout"
else
    echo "   ✗ FAIL: usage message not found on stdout"
    FAILURES=$((FAILURES + 1))
fi

# Exit code 1 on missing args
set +e
python "$TEMP_CALC" >/dev/null 2>&1
exit_code=$?
set -e
if [[ $exit_code -eq 1 ]]; then
    echo "   ✓ exit code 1 for missing arguments"
else
    echo "   ✗ FAIL: exit code is $exit_code (expected 1)"
    FAILURES=$((FAILURES + 1))
fi

echo ""
echo "3. Error handling - invalid input:"
echo ""

# Error messages go to stderr
stderr=$(python "$TEMP_CALC" "abc" "C" "F" 2>&1 >/dev/null || true)
if [[ "$stderr" =~ "Error:" ]]; then
    echo "   ✓ error message on stderr"
else
    echo "   ✗ FAIL: error message not found on stderr: '$stderr'"
    FAILURES=$((FAILURES + 1))
fi

# stdout is empty on error
stdout=$(python "$TEMP_CALC" "abc" "C" "F" 2>/dev/null || true)
if [[ -z "$stdout" ]]; then
    echo "   ✓ stdout is empty on error"
else
    echo "   ✗ FAIL: stdout contains unexpected content on error: '$stdout'"
    FAILURES=$((FAILURES + 1))
fi

# Exit code 1 on invalid number
set +e
python "$TEMP_CALC" "abc" "C" "F" >/dev/null 2>&1
exit_code=$?
set -e
if [[ $exit_code -eq 1 ]]; then
    echo "   ✓ exit code 1 for invalid number"
else
    echo "   ✗ FAIL: exit code is $exit_code (expected 1)"
    FAILURES=$((FAILURES + 1))
fi

echo ""
echo "4. Error handling - invalid scale:"
echo ""

# Exit code 1 on invalid scale
set +e
python "$TEMP_CALC" "100" "X" "F" >/dev/null 2>&1
exit_code=$?
set -e
if [[ $exit_code -eq 1 ]]; then
    echo "   ✓ exit code 1 for invalid scale"
else
    echo "   ✗ FAIL: exit code is $exit_code (expected 1)"
    FAILURES=$((FAILURES + 1))
fi

echo ""
echo "5. Warning handling - below absolute zero:"
echo ""

# Warning goes to stderr, result still on stdout
stdout=$(python "$TEMP_CALC" "-500" "C" "F" 2>/dev/null)
stderr=$(python "$TEMP_CALC" "-500" "C" "F" 2>&1 >/dev/null)

if [[ "$stdout" == "-868.00" ]]; then
    echo "   ✓ result on stdout despite warning"
else
    echo "   ✗ FAIL: result not on stdout: '$stdout'"
    FAILURES=$((FAILURES + 1))
fi

if [[ "$stderr" =~ "Warning:" ]]; then
    echo "   ✓ warning on stderr"
else
    echo "   ✗ FAIL: warning not on stderr: '$stderr'"
    FAILURES=$((FAILURES + 1))
fi

# Exit code 0 (warning, not error)
set +e
python "$TEMP_CALC" "-500" "C" "F" >/dev/null 2>&1
exit_code=$?
set -e
if [[ $exit_code -eq 0 ]]; then
    echo "   ✓ exit code 0 (warning is not an error)"
else
    echo "   ✗ FAIL: exit code is $exit_code (expected 0)"
    FAILURES=$((FAILURES + 1))
fi

echo ""
echo "6. Piping and scripting integration:"
echo ""

# Can pipe output
piped_result=$(python "$TEMP_CALC" "100" "C" "F" 2>/dev/null | cat)
if [[ "$piped_result" == "212.00" ]]; then
    echo "   ✓ output can be piped"
else
    echo "   ✗ FAIL: piping failed or altered output: '$piped_result'"
    FAILURES=$((FAILURES + 1))
fi

# Can use in command substitution
result=$(python "$TEMP_CALC" "32" "F" "C" 2>/dev/null)
if [[ "$result" == "0.00" ]]; then
    echo "   ✓ output can be captured in variable"
else
    echo "   ✗ FAIL: command substitution failed: '$result'"
    FAILURES=$((FAILURES + 1))
fi

# Can chain with other commands
chain_result=$(python "$TEMP_CALC" "100" "C" "F" 2>/dev/null | awk '{print $1 * 2}')
if [[ "$chain_result" == "424.00" || "$chain_result" == "424" ]]; then
    echo "   ✓ output can be chained with other tools"
else
    echo "   ✗ FAIL: chaining failed: '$chain_result'"
    FAILURES=$((FAILURES + 1))
fi

echo ""
echo "=================================================="
if [[ $FAILURES -eq 0 ]]; then
    echo "PASS: CLI integration is correct!"
    echo ""
    echo "INTEGRATION VERIFIED:"
    echo "  ✓ stdout contains only the result (clean for piping)"
    echo "  ✓ stderr contains only errors and warnings"
    echo "  ✓ exit codes follow Unix conventions (0=success, 1=error)"
    echo "  ✓ can be piped, redirected, and scripted"
    echo ""
    exit 0
else
    echo "FAIL: $FAILURES integration issue(s) found"
    echo ""
    echo "INTEGRATION BROKEN: Tool cannot be reliably used in scripts"
    echo ""
    exit 1
fi
