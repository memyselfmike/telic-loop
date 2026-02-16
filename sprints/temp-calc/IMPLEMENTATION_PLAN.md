# Implementation Plan (rendered from state)

Generated: 2026-02-16T12:52:43.069030


## Core

- [x] **1.1**: Build temp_calc.py with all conversion logic (C/F/K, all 6 directions), CLI argument parsing (value, from_scale, to_scale), output formatting (rounded to 2 decimal places), error handling (no args shows usage + exit 1, invalid number shows error + exit 1, invalid scale shows error + exit 1, same-scale returns input), and below-absolute-zero warning. Pure Python, single file, case-insensitive scale input.
  - Value: Enables the developer to run a single command and instantly get a converted temperature, eliminating the need to open a browser and break their workflow.
  - Acceptance: 1) python temp_calc.py 100 C F outputs 212.00. 2) python temp_calc.py 32 F C outputs 0.00. 3) python temp_calc.py 0 K C outputs -273.15. 4) python temp_calc.py 98.6 f c outputs 37.00. 5) No args prints usage and exits 1. 6) python temp_calc.py abc C F prints error about invalid number and exits 1. 7) python temp_calc.py 100 X F prints error about invalid scale and exits 1. 8) Below-absolute-zero input (e.g. -500 C F) prints warning to stderr and still outputs the converted value to stdout, formatted to 2 decimal places. 9) Same-scale input (e.g. 100 C C) outputs the input value formatted to 2 decimal places (e.g. 100.00), not the raw input string.


## Verification

- [ ] **2.1**: Write comprehensive pytest tests in test_temp_calc.py covering all 7 PRD acceptance criteria plus edge cases: all 6 conversion directions with known values, case-insensitive scale input, no-args usage output with exit code 1, invalid number error with exit code 1, invalid scale error with exit code 1, same-scale no-op, below-absolute-zero warning. Tests should invoke temp_calc.py as a subprocess to validate actual CLI behavior (exit codes, stdout output).
  - Value: Provides automated regression protection so the developer can trust the tool works correctly now and after any future changes.
  - Acceptance: 1) pytest test_temp_calc.py passes with all tests green. 2) Tests cover all 7 acceptance criteria from PRD Section 4. 3) Tests verify exit codes, stdout content, and edge case behavior. 4) Tests are runnable with just pytest (no extra dependencies).
  - Deps: 1.1
