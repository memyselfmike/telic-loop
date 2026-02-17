#!/usr/bin/env python3
"""
Verification runner: Runs all verification scripts AND the pytest suite.
Usage: python run_all.py [category]
  category: unit | integration | value | all (default: all)
             pytest   — run only the pytest suite
             full     — run all verifications + pytest suite

Returns exit code 0 if all pass, 1 if any fail.
"""

import sys
import os
import subprocess
import time
import glob

VERIF_DIR = os.path.dirname(os.path.abspath(__file__))
SPRINT_DIR = os.path.dirname(os.path.dirname(VERIF_DIR))

CATEGORIES = {
    "unit": "unit_*.py",
    "integration": "integration_*.py",
    "value": "value_*.py",
}

def run_script(path):
    """Run a single verification script, return (passed, duration_seconds, output)."""
    start = time.time()
    result = subprocess.run(
        [sys.executable, path],
        capture_output=True,
        text=True,
        timeout=120
    )
    duration = time.time() - start
    passed = result.returncode == 0
    output = result.stdout + result.stderr
    return passed, duration, output

def run_pytest():
    """Run the pytest suite and return (passed, duration, summary_line)."""
    tests_dir = os.path.join(SPRINT_DIR, "tests", "test_api.py")
    if not os.path.exists(tests_dir):
        return False, 0, "tests/test_api.py not found"

    start = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", tests_dir, "-v", "--tb=short", "--no-header"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=SPRINT_DIR
    )
    duration = time.time() - start
    passed = result.returncode == 0
    output = result.stdout + result.stderr

    # Extract summary line from pytest output (last non-empty line)
    lines = [l for l in output.strip().split('\n') if l.strip()]
    summary = lines[-1] if lines else "(no output)"

    # Print failed test details
    if not passed:
        for line in lines:
            print(f"    {line}")
    else:
        print(f"    {summary}")

    return passed, duration, summary


def main():
    category = sys.argv[1] if len(sys.argv) > 1 else "all"

    run_scripts = True
    run_tests = False

    if category == "pytest":
        run_scripts = False
        run_tests = True
        patterns = []
    elif category == "full":
        run_scripts = True
        run_tests = True
        patterns = list(CATEGORIES.values())
    elif category == "all":
        run_scripts = True
        run_tests = True  # always include pytest in full run
        patterns = list(CATEGORIES.values())
    elif category in CATEGORIES:
        patterns = [CATEGORIES[category]]
        run_tests = False
    else:
        print(f"Unknown category: {category}. Use: unit | integration | value | all | pytest | full")
        sys.exit(1)

    # Find all matching scripts
    scripts = []
    if run_scripts:
        for pattern in patterns:
            found = sorted(glob.glob(os.path.join(VERIF_DIR, pattern)))
            scripts.extend(found)

    total_label = f"{category.upper()} ({len(scripts)} scripts" + (" + pytest" if run_tests else "") + ")"
    print(f"{'='*60}")
    print(f"  VERIFICATION RUNNER — {total_label}")
    print(f"{'='*60}")
    print()

    results = []
    for script in scripts:
        name = os.path.basename(script)
        print(f">>> Running: {name}")
        try:
            passed, duration, output = run_script(script)
            # Print last few lines of output
            lines = output.strip().split('\n')
            for line in lines:
                print(f"    {line}")
            status = "PASS" if passed else "FAIL"
            print(f"    [{status}] in {duration:.1f}s")
        except subprocess.TimeoutExpired:
            passed = False
            duration = 120
            print(f"    [TIMEOUT] Script exceeded 120s")
        except Exception as e:
            passed = False
            duration = 0
            print(f"    [ERROR] {e}")

        results.append((name, passed, duration))
        print()

    # Run pytest suite
    if run_tests:
        print(f">>> Running: pytest tests/test_api.py")
        try:
            passed, duration, summary = run_pytest()
            status = "PASS" if passed else "FAIL"
            print(f"    [{status}] in {duration:.1f}s — {summary}")
        except subprocess.TimeoutExpired:
            passed = False
            duration = 120
            print(f"    [TIMEOUT] pytest exceeded 120s")
        except Exception as e:
            passed = False
            duration = 0
            print(f"    [ERROR] pytest: {e}")
        results.append(("pytest::test_api.py", passed, duration))
        print()

    if not results:
        print(f"No verification scripts found for category: {category}")
        sys.exit(0)

    # Summary
    print(f"{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    passed_count = sum(1 for _, p, _ in results if p)
    failed_count = len(results) - passed_count
    total_time = sum(d for _, _, d in results)

    for name, passed, duration in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}  {name}  ({duration:.1f}s)")

    print()
    print(f"  {passed_count}/{len(results)} passed in {total_time:.1f}s")

    if failed_count > 0:
        print()
        print(f"  FAILED ({failed_count}):")
        for name, passed, _ in results:
            if not passed:
                print(f"    - {name}")
        sys.exit(1)
    else:
        print()
        print("  ALL VERIFICATIONS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
