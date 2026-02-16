#!/usr/bin/env python3
"""Temperature converter CLI tool.

Converts temperatures between Celsius (C), Fahrenheit (F), and Kelvin (K).
"""

import sys


# Absolute zero thresholds for each scale
ABSOLUTE_ZERO = {
    'C': -273.15,
    'F': -459.67,
    'K': 0.0
}


def convert_temperature(value, from_scale, to_scale):
    """Convert temperature from one scale to another.

    Args:
        value: Numeric temperature value
        from_scale: Source scale (C, F, or K)
        to_scale: Target scale (C, F, or K)

    Returns:
        Converted temperature value
    """
    from_scale = from_scale.upper()
    to_scale = to_scale.upper()

    # Same scale - return input value
    if from_scale == to_scale:
        return value

    # First convert to Celsius as intermediate
    if from_scale == 'C':
        celsius = value
    elif from_scale == 'F':
        celsius = (value - 32) * 5 / 9
    elif from_scale == 'K':
        celsius = value - 273.15
    else:
        raise ValueError(f"Invalid source scale: {from_scale}")

    # Then convert from Celsius to target scale
    if to_scale == 'C':
        return celsius
    elif to_scale == 'F':
        return celsius * 9 / 5 + 32
    elif to_scale == 'K':
        return celsius + 273.15
    else:
        raise ValueError(f"Invalid target scale: {to_scale}")


def is_below_absolute_zero(value, scale):
    """Check if temperature is below absolute zero for the given scale.

    Args:
        value: Numeric temperature value
        scale: Temperature scale (C, F, or K)

    Returns:
        True if below absolute zero, False otherwise
    """
    scale = scale.upper()
    return value < ABSOLUTE_ZERO.get(scale, float('-inf'))


def print_usage():
    """Print usage help message."""
    print("Usage: python temp_calc.py <value> <from_scale> <to_scale>")
    print()
    print("  value:      A numeric temperature (integer or float)")
    print("  from_scale: Source scale (C, F, or K)")
    print("  to_scale:   Target scale (C, F, or K)")
    print()
    print("Examples:")
    print("  python temp_calc.py 100 C F")
    print("  python temp_calc.py 32 F C")
    print("  python temp_calc.py 0 K C")


def main():
    """Main entry point for the CLI tool."""
    # Check argument count
    if len(sys.argv) != 4:
        print_usage()
        sys.exit(1)

    # Parse arguments
    value_str = sys.argv[1]
    from_scale = sys.argv[2]
    to_scale = sys.argv[3]

    # Validate and parse numeric value
    try:
        value = float(value_str)
    except ValueError:
        print(f"Error: '{value_str}' is not a valid number", file=sys.stderr)
        sys.exit(1)

    # Validate scales
    from_scale_upper = from_scale.upper()
    to_scale_upper = to_scale.upper()

    if from_scale_upper not in ['C', 'F', 'K']:
        print(f"Error: '{from_scale}' is not a valid scale. Use C, F, or K", file=sys.stderr)
        sys.exit(1)

    if to_scale_upper not in ['C', 'F', 'K']:
        print(f"Error: '{to_scale}' is not a valid scale. Use C, F, or K", file=sys.stderr)
        sys.exit(1)

    # Check for below absolute zero and warn if necessary
    if is_below_absolute_zero(value, from_scale):
        print(f"Warning: Temperature {value} {from_scale_upper} is below absolute zero", file=sys.stderr)

    # Perform conversion
    result = convert_temperature(value, from_scale, to_scale)

    # Output result rounded to 2 decimal places
    print(f"{result:.2f}")


if __name__ == '__main__':
    main()
