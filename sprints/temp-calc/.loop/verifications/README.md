# Verification Scripts for temp-calc Sprint

This directory contains comprehensive verification scripts that prove the temperature converter CLI delivers its promised value.

## Overview

These scripts verify three levels of correctness:

1. **Unit** - Individual components work correctly (fast, run after every change)
2. **Integration** - Components work together correctly (medium speed, run after related changes)
3. **Value** - The user gets the promised outcome (variable speed, run before exit)

## Scripts

### Unit Tests

**`unit_test_temp_calc.py`** (pytest)
- **Runtime**: ~2 seconds
- **Coverage**: 28 comprehensive tests
- **What it verifies**:
  - All 6 conversion directions (C↔F↔K)
  - Case-insensitive scale handling
  - Output formatting (2 decimal places)
  - Same-scale no-op conversions
  - Error handling (no args, invalid number, invalid scale)
  - Below-absolute-zero warnings
  - Edge cases (floats, negative temps, very large numbers)
- **PRD Coverage**: All of Section 2 (Requirements) and Section 4 (Acceptance Criteria)
- **Run with**: `pytest unit_test_temp_calc.py -v` or `python unit_test_temp_calc.py`

### Integration Tests

**`integration_cli_output.sh`**
- **Runtime**: ~5 seconds
- **What it verifies**:
  - stdout contains only the result (clean for piping)
  - stderr contains only errors and warnings (proper stream separation)
  - Exit codes follow Unix conventions (0=success, 1=error)
  - Can be piped, redirected, and used in scripts
  - Command substitution works correctly
  - Can chain with other CLI tools
- **PRD Coverage**: Section 2.2 (CLI Interface), Section 2.3 (Error Handling)
- **Run with**: `bash integration_cli_output.sh`

### Value Delivery Tests

**`value_user_workflow.sh`**
- **Runtime**: ~10 seconds
- **What it verifies**:
  - Developer can convert temperatures exactly as Vision promises
  - All Vision success signals are verified
  - Common conversion scenarios work (boiling/freezing points, absolute zero)
  - Case-insensitive usage (real developer behavior)
  - Error handling prevents confusion
  - Edge cases are robust
- **Vision Goals**: "Developer can run a single command and instantly see the converted temperature"
- **Run with**: `bash value_user_workflow.sh`

**`value_quick_reference.sh`**
- **Runtime**: ~5 seconds
- **What it verifies**:
  - Developer can figure out usage without reading docs
  - Usage message is helpful and complete
  - Error messages are clear and actionable
  - Output is clean and scriptable
  - Tool is forgiving with input (case-insensitive, handles decimals)
- **Vision Goals**: "Quickly convert temperatures without interrupting workflow"
- **Run with**: `bash value_quick_reference.sh`

## Running Verifications

### Quick Commands

**Fast verification (unit tests only - ~2 seconds):**
```bash
bash run_fast.sh
```
Use this during development for rapid regression checking.

**Complete verification (all tests - ~20 seconds):**
```bash
bash run_all.sh
```
Use this before committing or marking tasks complete.

### Individual Test Suites

**Run unit tests only:**
```bash
pytest unit_test_temp_calc.py -v
# or
python unit_test_temp_calc.py
```

**Run integration tests only:**
```bash
bash integration_cli_output.sh
```

**Run value delivery tests only:**
```bash
bash value_user_workflow.sh
bash value_quick_reference.sh
```

## Success Criteria

All scripts must pass for the sprint to be considered complete. Each script:
- ✅ Runs independently (no setup required)
- ✅ Returns exit code 0 on pass, non-zero on fail
- ✅ Prints clear output explaining what passed/failed
- ✅ Tests actual user-facing behavior, not implementation details
- ✅ References which PRD section or Vision goal it verifies

## What These Scripts Prove

When all scripts pass, we have verified:

1. **Functional correctness**: All conversions produce mathematically correct results
2. **Input validation**: Invalid inputs are caught with clear error messages
3. **Output formatting**: Results are consistently formatted to 2 decimal places
4. **CLI integration**: The tool follows Unix conventions and can be scripted
5. **Usability**: A developer can use the tool immediately without reading docs
6. **Value delivery**: The promised outcome from the Vision is actually delivered

These scripts provide:
- **Regression protection**: Future changes can't break existing functionality
- **Confidence**: We know the tool works correctly before shipping
- **Documentation**: Scripts show exactly what behavior is expected
- **Debugging aid**: When tests fail, they clearly show what broke

## Coverage Summary

| PRD Section | Verified By |
|-------------|-------------|
| 2.1 Core Conversion | unit_test_temp_calc.py (TestConversionAccuracy) |
| 2.2 CLI Interface | unit_test_temp_calc.py, integration_cli_output.sh, value_* |
| 2.3 Error Handling | unit_test_temp_calc.py (TestErrorHandling), integration_cli_output.sh |
| 2.4 Edge Cases | unit_test_temp_calc.py (TestBelowAbsoluteZero, TestEdgeCases) |
| 4.1-4.7 Acceptance | All scripts verify specific acceptance criteria |

| Vision Goal | Verified By |
|-------------|-------------|
| "Run a single command and instantly see converted temperature" | value_user_workflow.sh |
| "No need to open browser or interrupt workflow" | value_quick_reference.sh |
| "Clear error messages for bad input" | All scripts |

## Design Philosophy

These scripts follow the core principle:

> **"A test that passes while the user gets no value is worse than no test at all—it creates false confidence."**

Every script tests what the user actually experiences, not just whether internal functions return values. The unit tests invoke the CLI as a subprocess to verify the complete user interaction, not just isolated function calls.
