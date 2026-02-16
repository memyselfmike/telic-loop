# PRD: Temperature Converter CLI

## 1. Overview

Build a Python command-line tool (`temp_calc.py`) that converts temperatures between Celsius (C), Fahrenheit (F), and Kelvin (K).

## 2. Requirements

### 2.1 Core Conversion

The tool must support all 6 conversion directions:
- C → F: `F = C * 9/5 + 32`
- C → K: `K = C + 273.15`
- F → C: `C = (F - 32) * 5/9`
- F → K: `K = (F - 32) * 5/9 + 273.15`
- K → C: `C = K - 273.15`
- K → F: `F = (K - 273.15) * 9/5 + 32`

### 2.2 CLI Interface

Usage: `python temp_calc.py <value> <from_scale> <to_scale>`

- `value`: A numeric temperature (integer or float)
- `from_scale`: Source scale (C, F, or K, case-insensitive)
- `to_scale`: Target scale (C, F, or K, case-insensitive)

Output: The converted value as a number, rounded to 2 decimal places.

### 2.3 Error Handling

- No arguments: Print usage help and exit with code 1
- Invalid number: Print "Error: '<value>' is not a valid number" and exit with code 1
- Invalid scale: Print "Error: '<scale>' is not a valid scale. Use C, F, or K" and exit with code 1
- Same scale: Just print the input value (no-op conversion)

### 2.4 Edge Cases

- Temperatures below absolute zero (below -273.15°C / -459.67°F / 0K) should print a warning but still convert.

## 3. Technical Constraints

- Pure Python, no external dependencies
- Single file: `temp_calc.py` in the sprint directory
- Must work with Python 3.11+

## 4. Acceptance Criteria

1. `python temp_calc.py 100 C F` → outputs `212.00`
2. `python temp_calc.py 32 F C` → outputs `0.00`
3. `python temp_calc.py 0 K C` → outputs `-273.15`
4. `python temp_calc.py 98.6 f c` → outputs `37.00` (case-insensitive)
5. `python temp_calc.py` → prints usage, exits 1
6. `python temp_calc.py abc C F` → prints error, exits 1
7. `python temp_calc.py 100 X F` → prints error about invalid scale, exits 1
