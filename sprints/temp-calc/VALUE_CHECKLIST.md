# Value Checklist: temp-calc
Generated: 2026-02-16T13:04:38.878337

## VRC Status
- Value Score: 100%
- Verified: 3/3
- Blocked: 0
- Recommendation: SHIP_READY
- Summary: FULL VRC at iteration 3: ALL 3 deliverables VERIFIED with live CLI execution. ALL tasks complete (2/2). (1) Temperature conversion: all 6 directions correct and precise to 2 decimal places — 100 C F=212.00, 32 F C=0.00, 0 K C=-273.15, 98.6 f c=37.00, 100 C K=373.15, 100 F K=310.93, 300 K F=80.33, same-scale 100 C C=100.00. (2) CLI interface: single-command invocation works instantly, no-args prints clear usage help with examples and exits code 1. (3) Input validation: invalid number gives clear error+exit 1, invalid scale gives clear error+exit 1, below-absolute-zero warns on stderr while outputting converted result to stdout, case-insensitive scales work. (4) Regression protection: 22 pytest tests ALL PASSING covering all acceptance criteria, all 6 conversion directions, edge cases, error handling, and exit codes. Value score 3/3. The developer can RIGHT NOW run a single command and instantly get converted temperatures, exactly as the VISION promised. No gaps, no regressions. Both tasks done. Recommending SHIP_READY.

## Tasks
- [x] **1.1**: Build temp_calc.py with all conversion logic (C/F/K, all 6 directions), CLI argument parsing (value, from_scale, to_scale), output formatting (rounded to 2 decimal places), error handling (no args shows usage + exit 1, invalid number shows error + exit 1, invalid scale shows error + exit 1, same-scale returns input), and below-absolute-zero warning. Pure Python, single file, case-insensitive scale input.
- [x] **2.1**: Write comprehensive pytest tests in test_temp_calc.py covering all 7 PRD acceptance criteria plus edge cases: all 6 conversion directions with known values, case-insensitive scale input, no-args usage output with exit code 1, invalid number error with exit code 1, invalid scale error with exit code 1, same-scale no-op, below-absolute-zero warning. Tests should invoke temp_calc.py as a subprocess to validate actual CLI behavior (exit codes, stdout output).

## Verifications