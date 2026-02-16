#!/usr/bin/env python3
"""Unit tests for temp_calc.py

Verification: All conversion logic, input validation, and error handling work correctly
PRD Reference: All of Section 2 (Requirements) and Section 4 (Acceptance Criteria)
Vision Goal: Developer can convert temperatures quickly and accurately from command line
Category: unit

This test file covers:
- All 6 conversion directions (C/F/K bidirectional)
- Case-insensitive scale input
- Error handling (no args, invalid number, invalid scale)
- Same-scale no-op
- Below-absolute-zero warning
- Output formatting (2 decimal places)
- Exit codes
"""

import subprocess
import sys
from pathlib import Path

# Path to the temp_calc.py script
SCRIPT_PATH = Path(__file__).parent.parent.parent / "temp_calc.py"


def run_temp_calc(*args):
    """Run temp_calc.py with given arguments and capture output.

    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)] + list(args),
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestConversionAccuracy:
    """Test all conversion formulas produce correct results."""

    def test_celsius_to_fahrenheit(self):
        """C → F: 100°C = 212°F (PRD 4.1)"""
        code, stdout, stderr = run_temp_calc("100", "C", "F")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "212.00", f"Expected '212.00', got '{stdout}'"

    def test_fahrenheit_to_celsius(self):
        """F → C: 32°F = 0°C (PRD 4.2)"""
        code, stdout, stderr = run_temp_calc("32", "F", "C")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "0.00", f"Expected '0.00', got '{stdout}'"

    def test_kelvin_to_celsius(self):
        """K → C: 0K = -273.15°C (PRD 4.3)"""
        code, stdout, stderr = run_temp_calc("0", "K", "C")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "-273.15", f"Expected '-273.15', got '{stdout}'"

    def test_celsius_to_kelvin(self):
        """C → K: 0°C = 273.15K"""
        code, stdout, stderr = run_temp_calc("0", "C", "K")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "273.15", f"Expected '273.15', got '{stdout}'"

    def test_fahrenheit_to_kelvin(self):
        """F → K: 32°F = 273.15K"""
        code, stdout, stderr = run_temp_calc("32", "F", "K")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "273.15", f"Expected '273.15', got '{stdout}'"

    def test_kelvin_to_fahrenheit(self):
        """K → F: 273.15K = 32°F"""
        code, stdout, stderr = run_temp_calc("273.15", "K", "F")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "32.00", f"Expected '32.00', got '{stdout}'"


class TestCaseInsensitivity:
    """Test case-insensitive scale handling (PRD 4.4)."""

    def test_lowercase_scales(self):
        """98.6°f = 37°c with lowercase scales"""
        code, stdout, stderr = run_temp_calc("98.6", "f", "c")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "37.00", f"Expected '37.00', got '{stdout}'"

    def test_mixed_case_scales(self):
        """Mixed case should work: F → c"""
        code, stdout, stderr = run_temp_calc("212", "F", "c")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "100.00", f"Expected '100.00', got '{stdout}'"


class TestOutputFormatting:
    """Test output is always rounded to 2 decimal places (PRD 2.2)."""

    def test_rounding_two_decimal_places(self):
        """Result should be rounded to exactly 2 decimal places"""
        code, stdout, stderr = run_temp_calc("98.6", "F", "C")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "37.00", f"Expected '37.00', got '{stdout}'"
        # Verify format: should have exactly 2 digits after decimal
        parts = stdout.split('.')
        assert len(parts) == 2, f"Expected decimal number, got '{stdout}'"
        assert len(parts[1]) == 2, f"Expected 2 decimal places, got {len(parts[1])}"

    def test_same_scale_formatting(self):
        """Same-scale conversion should also format to 2 decimal places (PRD 2.3)"""
        code, stdout, stderr = run_temp_calc("100", "C", "C")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "100.00", f"Expected '100.00', got '{stdout}'"


class TestSameScaleConversion:
    """Test same-scale conversions are no-ops (PRD 2.3)."""

    def test_celsius_to_celsius(self):
        """C → C: Should return input value formatted"""
        code, stdout, stderr = run_temp_calc("100", "C", "C")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "100.00", f"Expected '100.00', got '{stdout}'"

    def test_fahrenheit_to_fahrenheit(self):
        """F → F: Should return input value formatted"""
        code, stdout, stderr = run_temp_calc("98.6", "F", "F")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "98.60", f"Expected '98.60', got '{stdout}'"

    def test_kelvin_to_kelvin(self):
        """K → K: Should return input value formatted"""
        code, stdout, stderr = run_temp_calc("273.15", "K", "K")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "273.15", f"Expected '273.15', got '{stdout}'"


class TestErrorHandling:
    """Test error conditions produce correct messages and exit codes (PRD 2.3)."""

    def test_no_arguments(self):
        """No args: Print usage and exit 1 (PRD 4.5)"""
        code, stdout, stderr = run_temp_calc()
        assert code == 1, f"Expected exit code 1, got {code}"
        assert "Usage:" in stdout, f"Expected usage message in stdout, got: {stdout}"

    def test_invalid_number(self):
        """Invalid number: Print error and exit 1 (PRD 4.6)"""
        code, stdout, stderr = run_temp_calc("abc", "C", "F")
        assert code == 1, f"Expected exit code 1, got {code}"
        assert "Error:" in stderr, f"Expected error message in stderr, got: {stderr}"
        assert "abc" in stderr, f"Expected 'abc' in error message, got: {stderr}"
        assert "not a valid number" in stderr, f"Expected 'not a valid number' in error, got: {stderr}"

    def test_invalid_from_scale(self):
        """Invalid from_scale: Print error and exit 1 (PRD 4.7)"""
        code, stdout, stderr = run_temp_calc("100", "X", "F")
        assert code == 1, f"Expected exit code 1, got {code}"
        assert "Error:" in stderr, f"Expected error message in stderr, got: {stderr}"
        assert "X" in stderr, f"Expected 'X' in error message, got: {stderr}"
        assert "not a valid scale" in stderr, f"Expected 'not a valid scale' in error, got: {stderr}"

    def test_invalid_to_scale(self):
        """Invalid to_scale: Print error and exit 1"""
        code, stdout, stderr = run_temp_calc("100", "C", "Z")
        assert code == 1, f"Expected exit code 1, got {code}"
        assert "Error:" in stderr, f"Expected error message in stderr, got: {stderr}"
        assert "Z" in stderr, f"Expected 'Z' in error message, got: {stderr}"
        assert "not a valid scale" in stderr, f"Expected 'not a valid scale' in error, got: {stderr}"

    def test_too_few_arguments(self):
        """Too few args: Print usage and exit 1"""
        code, stdout, stderr = run_temp_calc("100", "C")
        assert code == 1, f"Expected exit code 1, got {code}"
        assert "Usage:" in stdout, f"Expected usage message, got: {stdout}"

    def test_too_many_arguments(self):
        """Too many args: Print usage and exit 1"""
        code, stdout, stderr = run_temp_calc("100", "C", "F", "extra")
        assert code == 1, f"Expected exit code 1, got {code}"
        assert "Usage:" in stdout, f"Expected usage message, got: {stdout}"


class TestBelowAbsoluteZero:
    """Test below-absolute-zero warning (PRD 2.4)."""

    def test_below_absolute_zero_celsius(self):
        """Below absolute zero in Celsius: Warn but still convert"""
        code, stdout, stderr = run_temp_calc("-500", "C", "F")
        assert code == 0, f"Expected exit code 0 (conversion succeeds), got {code}"
        assert "Warning:" in stderr, f"Expected warning in stderr, got: {stderr}"
        assert "-500" in stderr, f"Expected '-500' in warning, got: {stderr}"
        assert "below absolute zero" in stderr.lower(), f"Expected 'below absolute zero' in warning, got: {stderr}"
        # Should still output the converted value
        assert stdout == "-868.00", f"Expected '-868.00', got '{stdout}'"

    def test_below_absolute_zero_fahrenheit(self):
        """Below absolute zero in Fahrenheit: Warn but still convert"""
        code, stdout, stderr = run_temp_calc("-500", "F", "C")
        assert code == 0, f"Expected exit code 0 (conversion succeeds), got {code}"
        assert "Warning:" in stderr, f"Expected warning in stderr, got: {stderr}"
        assert "-500" in stderr, f"Expected '-500' in warning, got: {stderr}"
        # Should still output the converted value
        assert stdout == "-295.56", f"Expected '-295.56', got '{stdout}'"

    def test_below_absolute_zero_kelvin(self):
        """Below absolute zero in Kelvin (negative): Warn but still convert"""
        code, stdout, stderr = run_temp_calc("-10", "K", "C")
        assert code == 0, f"Expected exit code 0 (conversion succeeds), got {code}"
        assert "Warning:" in stderr, f"Expected warning in stderr, got: {stderr}"
        assert "-10" in stderr, f"Expected '-10' in warning, got: {stderr}"
        # Should still output the converted value
        assert stdout == "-283.15", f"Expected '-283.15', got '{stdout}'"

    def test_at_absolute_zero_no_warning(self):
        """At absolute zero: No warning"""
        code, stdout, stderr = run_temp_calc("-273.15", "C", "K")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stderr == "", f"Expected no warning at absolute zero, got: {stderr}"
        assert stdout == "0.00", f"Expected '0.00', got '{stdout}'"

    def test_above_absolute_zero_no_warning(self):
        """Above absolute zero: No warning"""
        code, stdout, stderr = run_temp_calc("100", "C", "F")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stderr == "", f"Expected no warning for normal temperatures, got: {stderr}"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_float_input(self):
        """Accept float values"""
        code, stdout, stderr = run_temp_calc("98.6", "F", "C")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "37.00", f"Expected '37.00', got '{stdout}'"

    def test_negative_temperature_valid(self):
        """Negative temperatures above absolute zero should work"""
        code, stdout, stderr = run_temp_calc("-40", "C", "F")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "-40.00", f"Expected '-40.00', got '{stdout}'"
        # -40°C = -40°F (fun fact: they meet at -40!)

    def test_zero_temperature(self):
        """Zero should work in all scales"""
        code, stdout, stderr = run_temp_calc("0", "C", "F")
        assert code == 0, f"Expected exit code 0, got {code}"
        assert stdout == "32.00", f"Expected '32.00', got '{stdout}'"

    def test_very_large_temperature(self):
        """Very large temperatures should work"""
        code, stdout, stderr = run_temp_calc("1000000", "C", "F")
        assert code == 0, f"Expected exit code 0, got {code}"
        # Should convert correctly even for huge numbers
        # 1000000°C = 1000000 * 9/5 + 32 = 1800032°F
        assert stdout == "1800032.00", f"Expected '1800032.00', got '{stdout}'"


if __name__ == '__main__':
    # Run pytest if available, otherwise provide helpful message
    try:
        import pytest
        sys.exit(pytest.main([__file__, '-v']))
    except ImportError:
        print("pytest not found. Install with: pip install pytest")
        print("Or run individual test methods manually.")
        sys.exit(1)
