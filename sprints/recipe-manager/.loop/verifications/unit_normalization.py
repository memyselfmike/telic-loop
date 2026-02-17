#!/usr/bin/env python3
"""
Verification: Unit normalization engine correctness
PRD Reference: Section 2.2 (Unit Normalization)
Vision Goal: "Generate a Shopping List" - ingredients with compatible units are merged
Category: unit

Tests the pure normalization function in isolation.
"""

import sys
import os

# Add the backend directory to path
SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== Unit Normalization Engine ===")
print(f"Sprint dir: {SPRINT_DIR}")

failures = []

try:
    from routes.shopping import normalize_and_aggregate
    print("OK: normalize_and_aggregate function imported")
except ImportError as e:
    print(f"FAIL: Cannot import normalize_and_aggregate from routes.shopping: {e}")
    sys.exit(1)


def run_case(description, inputs, expected_items):
    """
    inputs: list of (item, quantity, unit, grocery_section) — matches normalize_and_aggregate signature
    expected_items: list of (quantity, unit, item, grocery_section) after normalization
    """
    result = normalize_and_aggregate(inputs)
    # normalize_and_aggregate returns (item_display, qty, unit, section)
    result_set = {(round(r[1], 1), r[2], r[0].lower(), r[3]) for r in result}
    expected_set = {(round(e[0], 1), e[1], e[2].lower(), e[3]) for e in expected_items}
    if result_set == expected_set:
        print(f"  PASS: {description}")
        return True
    else:
        print(f"  FAIL: {description}")
        print(f"    Expected: {sorted(expected_set)}")
        print(f"    Got:      {sorted(result_set)}")
        failures.append(description)
        return False


print()
print("--- Volume normalization ---")

# 2 cups + 1 cup = 3 cups
run_case(
    "2 cups + 1 cup = 3 cups (same unit, no conversion needed)",
    [("flour", 2, "cup", "pantry"), ("flour", 1, "cup", "pantry")],
    [(3.0, "cup", "flour", "pantry")]
)

# 2 tsp + 1 tsp = 1 tbsp (3 tsp = 1 tbsp, exact threshold)
run_case(
    "2 tsp + 1 tsp = 1 tbsp (exact upconversion threshold)",
    [("salt", 2, "tsp", "pantry"), ("salt", 1, "tsp", "pantry")],
    [(1.0, "tbsp", "salt", "pantry")]
)

# 4 tsp -> 1 tbsp + 1 tsp (upconvert to largest unit >= 1, keep remainder)
run_case(
    "4 tsp -> 1 tbsp + 1 tsp (remainder decomposition)",
    [("pepper", 4, "tsp", "pantry")],
    [(1.0, "tbsp", "pepper", "pantry"), (1.0, "tsp", "pepper", "pantry")]
)

# 2 tbsp stays as 2 tbsp (0.125 cups < 1, do not upconvert)
run_case(
    "2 tbsp stays as 2 tbsp (0.125 cups < 1, never upconvert to fractional < 1)",
    [("oil", 2, "tbsp", "pantry")],
    [(2.0, "tbsp", "oil", "pantry")]
)

print()
print("--- Weight normalization ---")

# 8 oz + 8 oz = 1 lb (16 oz = 1 lb)
run_case(
    "8 oz + 8 oz = 1 lb (exact threshold)",
    [("chicken", 8, "oz", "meat"), ("chicken", 8, "oz", "meat")],
    [(1.0, "lb", "chicken", "meat")]
)

# 4 oz stays as 4 oz (0.25 lb < 1)
run_case(
    "4 oz stays as 4 oz (0.25 lb < 1, no upconversion)",
    [("cheese", 4, "oz", "dairy")],
    [(4.0, "oz", "cheese", "dairy")]
)

print()
print("--- Count normalization ---")

# "whole", "piece", "each" are equivalent
run_case(
    "1 whole + 1 piece = 2 whole (count equivalents)",
    [("egg", 1, "whole", "dairy"), ("egg", 1, "piece", "dairy")],
    [(2.0, "whole", "egg", "dairy")]
)

# 2 each + 1 whole = 3 whole
run_case(
    "2 each + 1 whole = 3 whole",
    [("apple", 2, "each", "produce"), ("apple", 1, "whole", "produce")],
    [(3.0, "whole", "apple", "produce")]
)

print()
print("--- Incompatible units (separate lines) ---")

# cups flour + grams flour = 2 separate lines (incompatible units)
run_case(
    "2 cups flour + 100g flour = 2 separate lines (incompatible units)",
    [("flour", 2, "cup", "pantry"), ("flour", 100, "g", "pantry")],
    [(2.0, "cup", "flour", "pantry"), (100.0, "g", "flour", "pantry")]
)

print()
print("--- Aggregation across different items ---")

# Different items never merge
run_case(
    "Different items (flour vs sugar) stay separate even with same unit",
    [("flour", 1, "cup", "pantry"), ("sugar", 1, "cup", "pantry")],
    [(1.0, "cup", "flour", "pantry"), (1.0, "cup", "sugar", "pantry")]
)

print()
print("--- Decimal precision ---")

# Two 1/3 lb portions = 0.666 lb, which is < 1 lb, so stays in oz: 0.666*16 = 10.656 -> 10.7 oz
run_case(
    "Two 1/3 lb portions aggregate to 10.7 oz (decimal precision in oz)",
    [("beef", 0.333, "lb", "meat"), ("beef", 0.333, "lb", "meat")],
    [(10.7, "oz", "beef", "meat")]
)

# 5 tsp + 1 tsp = 6 tsp = 2 tbsp exactly (no remainder)
run_case(
    "5 tsp + 1 tsp = 6 tsp = 2 tbsp (exact upconversion, no remainder)",
    [("vanilla", 5, "tsp", "pantry"), ("vanilla", 1, "tsp", "pantry")],
    [(2.0, "tbsp", "vanilla", "pantry")]
)

print()
print("--- Never downconvert ---")

# 1 cup should NOT be converted to 16 tbsp
result = normalize_and_aggregate([("water", 1, "cup", "other")])
downconverted = False
for r in result:
    if r[2] == "tbsp":
        print(f"  FAIL: Never downconvert - 1 cup was converted to tbsp")
        failures.append("Never downconvert: 1 cup should not become tbsp")
        downconverted = True
    elif r[2] == "tsp":
        print(f"  FAIL: Never downconvert - 1 cup was converted to tsp")
        failures.append("Never downconvert: 1 cup should not become tsp")
        downconverted = True
if not downconverted:
    print(f"  PASS: Never downconvert - 1 cup stays as cup (got {result})")

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} test(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("RESULT: PASS - All unit normalization cases correct")
    sys.exit(0)
