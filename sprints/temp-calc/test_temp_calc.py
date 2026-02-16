"""Comprehensive pytest tests for temp_calc.py CLI tool.

Tests all PRD acceptance criteria and edge cases by invoking the CLI as a subprocess.
"""

import subprocess
import sys
from pathlib import Path


# Path to the temp_calc.py script
TEMP_CALC_PATH = Path(__file__).parent / "temp_calc.py"


def run_temp_calc(*args):
    """Run temp_calc.py with given arguments and capture result.

    Args:
        *args: Command-line arguments to pass to temp_calc.py

    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    result = subprocess.run(
        [sys.executable, str(TEMP_CALC_PATH)] + list(args),
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


# PRD Acceptance Criterion 1: 100 C to F = 212.00
def test_celsius_to_fahrenheit():
    """Test C to F conversion: 100 C -> 212.00 F"""
    exit_code, stdout, stderr = run_temp_calc("100", "C", "F")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "212.00", f"Expected 212.00, got {stdout.strip()}"


# PRD Acceptance Criterion 2: 32 F to C = 0.00
def test_fahrenheit_to_celsius():
    """Test F to C conversion: 32 F -> 0.00 C"""
    exit_code, stdout, stderr = run_temp_calc("32", "F", "C")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "0.00", f"Expected 0.00, got {stdout.strip()}"


# PRD Acceptance Criterion 3: 0 K to C = -273.15
def test_kelvin_to_celsius():
    """Test K to C conversion: 0 K -> -273.15 C"""
    exit_code, stdout, stderr = run_temp_calc("0", "K", "C")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "-273.15", f"Expected -273.15, got {stdout.strip()}"


# PRD Acceptance Criterion 4: Case-insensitive scale handling
def test_case_insensitive_scales():
    """Test case-insensitive scale input: 98.6 f c -> 37.00"""
    exit_code, stdout, stderr = run_temp_calc("98.6", "f", "c")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "37.00", f"Expected 37.00, got {stdout.strip()}"


# PRD Acceptance Criterion 5: No arguments prints usage and exits with code 1
def test_no_arguments_prints_usage():
    """Test no arguments: should print usage and exit with code 1"""
    exit_code, stdout, stderr = run_temp_calc()
    assert exit_code == 1, "Should exit with code 1"
    assert "Usage:" in stdout, "Should print usage help"
    assert "temp_calc.py" in stdout, "Usage should mention script name"


# PRD Acceptance Criterion 6: Invalid number error with exit code 1
def test_invalid_number_error():
    """Test invalid number input: should print error and exit with code 1"""
    exit_code, stdout, stderr = run_temp_calc("abc", "C", "F")
    assert exit_code == 1, "Should exit with code 1"
    assert "Error:" in stderr, "Should print error message to stderr"
    assert "abc" in stderr, "Error should mention the invalid input"
    assert "not a valid number" in stderr, "Error should explain the problem"


# PRD Acceptance Criterion 7: Invalid scale error with exit code 1
def test_invalid_scale_error():
    """Test invalid scale input: should print error and exit with code 1"""
    exit_code, stdout, stderr = run_temp_calc("100", "X", "F")
    assert exit_code == 1, "Should exit with code 1"
    assert "Error:" in stderr, "Should print error message to stderr"
    assert "X" in stderr, "Error should mention the invalid scale"
    assert "not a valid scale" in stderr, "Error should explain the problem"


# Additional conversion direction tests (PRD 2.1 requires all 6 directions)
def test_celsius_to_kelvin():
    """Test C to K conversion: 0 C -> 273.15 K"""
    exit_code, stdout, stderr = run_temp_calc("0", "C", "K")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "273.15", f"Expected 273.15, got {stdout.strip()}"


def test_fahrenheit_to_kelvin():
    """Test F to K conversion: 32 F -> 273.15 K"""
    exit_code, stdout, stderr = run_temp_calc("32", "F", "K")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "273.15", f"Expected 273.15, got {stdout.strip()}"


def test_kelvin_to_fahrenheit():
    """Test K to F conversion: 273.15 K -> 32.00 F"""
    exit_code, stdout, stderr = run_temp_calc("273.15", "K", "F")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "32.00", f"Expected 32.00, got {stdout.strip()}"


# Edge case: Same-scale conversion (PRD 2.3)
def test_same_scale_celsius():
    """Test same-scale conversion: 100 C C -> 100.00"""
    exit_code, stdout, stderr = run_temp_calc("100", "C", "C")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "100.00", f"Expected 100.00, got {stdout.strip()}"


def test_same_scale_fahrenheit():
    """Test same-scale conversion: 98.6 F F -> 98.60"""
    exit_code, stdout, stderr = run_temp_calc("98.6", "F", "F")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "98.60", f"Expected 98.60, got {stdout.strip()}"


def test_same_scale_kelvin():
    """Test same-scale conversion: 300 K K -> 300.00"""
    exit_code, stdout, stderr = run_temp_calc("300", "K", "K")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "300.00", f"Expected 300.00, got {stdout.strip()}"


# Edge case: Below absolute zero warning (PRD 2.4)
def test_below_absolute_zero_celsius():
    """Test below absolute zero: -500 C F should warn but still convert"""
    exit_code, stdout, stderr = run_temp_calc("-500", "C", "F")
    assert exit_code == 0, "Should still exit successfully despite warning"
    assert "Warning:" in stderr, "Should print warning to stderr"
    assert "below absolute zero" in stderr.lower(), "Warning should mention absolute zero"
    # -500 C = -868.00 F
    assert stdout.strip() == "-868.00", f"Should still output converted value, got {stdout.strip()}"


def test_below_absolute_zero_fahrenheit():
    """Test below absolute zero: -500 F C should warn but still convert"""
    exit_code, stdout, stderr = run_temp_calc("-500", "F", "C")
    assert exit_code == 0, "Should still exit successfully despite warning"
    assert "Warning:" in stderr, "Should print warning to stderr"
    # -500 F = -295.56 C (rounded to 2 decimal places)
    result = float(stdout.strip())
    assert -295.57 < result < -295.55, f"Expected around -295.56, got {result}"


def test_below_absolute_zero_kelvin():
    """Test below absolute zero: -10 K C should warn but still convert"""
    exit_code, stdout, stderr = run_temp_calc("-10", "K", "C")
    assert exit_code == 0, "Should still exit successfully despite warning"
    assert "Warning:" in stderr, "Should print warning to stderr"
    # -10 K = -283.15 C
    assert stdout.strip() == "-283.15", f"Should still output converted value, got {stdout.strip()}"


# Edge case: Invalid scale for to_scale argument
def test_invalid_to_scale():
    """Test invalid to_scale: 100 C X should error"""
    exit_code, stdout, stderr = run_temp_calc("100", "C", "X")
    assert exit_code == 1, "Should exit with code 1"
    assert "Error:" in stderr, "Should print error message"
    assert "not a valid scale" in stderr, "Error should mention invalid scale"


# Edge case: Float input
def test_float_input():
    """Test float input: 100.5 C F -> 212.90"""
    exit_code, stdout, stderr = run_temp_calc("100.5", "C", "F")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "212.90", f"Expected 212.90, got {stdout.strip()}"


# Edge case: Negative temperatures (above absolute zero)
def test_negative_celsius_valid():
    """Test valid negative temperature: -40 C F -> -40.00 (C and F intersect)"""
    exit_code, stdout, stderr = run_temp_calc("-40", "C", "F")
    assert exit_code == 0, "Should exit successfully"
    assert stdout.strip() == "-40.00", f"Expected -40.00, got {stdout.strip()}"


# Edge case: Too many arguments
def test_too_many_arguments():
    """Test too many arguments: should print usage and exit with code 1"""
    exit_code, stdout, stderr = run_temp_calc("100", "C", "F", "extra")
    assert exit_code == 1, "Should exit with code 1"
    assert "Usage:" in stdout, "Should print usage help"


# Edge case: Too few arguments
def test_too_few_arguments():
    """Test too few arguments: should print usage and exit with code 1"""
    exit_code, stdout, stderr = run_temp_calc("100", "C")
    assert exit_code == 1, "Should exit with code 1"
    assert "Usage:" in stdout, "Should print usage help"


# Edge case: Verify output precision (2 decimal places per PRD 2.2)
def test_output_precision_two_decimals():
    """Test output is always 2 decimal places: 37 C F -> 98.60 (not 98.6)"""
    exit_code, stdout, stderr = run_temp_calc("37", "C", "F")
    assert exit_code == 0, "Should exit successfully"
    output = stdout.strip()
    # Verify exactly 2 decimal places
    assert "." in output, "Output should contain decimal point"
    decimal_part = output.split(".")[1]
    assert len(decimal_part) == 2, f"Should have exactly 2 decimal places, got {len(decimal_part)}"
    assert output == "98.60", f"Expected 98.60, got {output}"
