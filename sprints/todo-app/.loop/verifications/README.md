# Todo App - Verification Suite

This directory contains executable verification scripts that prove the todo app delivers its promised value to users.

## Purpose

These scripts verify that the user gets the complete outcome promised in the Vision:
- **Zero-setup** HTML file opens in any browser
- **Add, complete, delete** tasks work correctly
- **Filter by status** shows correct subsets
- **Tasks persist** across page reloads via localStorage
- **Mobile responsive** design (375px viewport)

## Running Verifications

### Quick Start

Run all verifications:
```bash
bash run_all.sh
```

Run specific category:
```bash
bash run_all.sh unit         # Fast regression checks
bash run_all.sh integration  # Component interaction tests
bash run_all.sh value        # User outcome verification
```

### Individual Scripts

Each script can be run independently:

```bash
# Unit tests (fast)
bash unit_html_structure.sh
bash unit_javascript_syntax.sh
python unit_edge_cases.py

# Integration tests
python integration_localstorage_flow.py

# Value tests (comprehensive)
python value_browser_acceptance.py
```

## Script Categories

### Unit Verifications (< 10s)
Fast checks for individual components. Run after every code change for regression detection.

- **unit_html_structure.sh** - Verifies HTML contains all required elements, is self-contained (no external dependencies), and includes localStorage implementation
- **unit_javascript_syntax.sh** - Validates JavaScript syntax, balanced braces/parens/brackets, and expected patterns
- **unit_edge_cases.py** - Tests edge cases: empty input, whitespace, long text, special characters, rapid operations

### Integration Verifications (< 60s)
Test how components work together. Run after related tasks complete.

- **integration_localstorage_flow.py** - Verifies complete data flow: UI action → localStorage save → page reload → data restore → UI render

### Value Verifications (variable time)
Prove the user gets the promised outcome. Run before exit gate and after milestone tasks.

- **value_browser_acceptance.py** - Tests all 7 PRD acceptance criteria:
  1. Initial page load shows input and empty list
  2. Add task via Enter key
  3. Checkbox toggles strikethrough styling
  4. Delete button removes task
  5. Filter buttons show correct subsets
  6. Tasks persist after page refresh
  7. Mobile responsive (375px viewport)

## Prerequisites

- **Python 3.14+** with playwright installed
- **Playwright browsers** installed: `playwright install chromium`
- **Bash** shell (Git Bash on Windows, native on Linux/Mac)

Install Python dependencies:
```bash
pip install pytest-playwright playwright
```

## How Tests Work

1. **HTTP Server**: Python tests start a local HTTP server (not file:// protocol) to ensure consistent localStorage behavior
2. **Headless Browser**: Tests run in Chromium headless mode for speed
3. **Clean State**: Each test clears localStorage before running to ensure isolation
4. **Real Interactions**: Tests simulate actual user actions (typing, clicking, page refresh)
5. **Visual Verification**: Tests check computed styles (strikethrough, opacity) not just DOM classes

## Exit Codes

- **0**: All tests passed - user gets promised value
- **1**: At least one test failed - value delivery incomplete

## What These Tests Prove

These are **not** just unit tests or integration tests. They are **value delivery proofs**:

✓ A developer can open index.html in any browser with zero setup
✓ The app immediately works - no install, no build, no configuration
✓ Tasks can be added, completed, deleted, and filtered
✓ Tasks survive browser refresh (localStorage persistence)
✓ The UI is usable on mobile devices (375px viewport)
✓ Edge cases are handled gracefully (empty input, special characters)

**This is exactly what the Vision promised. These tests prove the user receives that outcome.**

## Test Philosophy

> "A test that passes while the user gets no value is worse than no test at all — it creates false confidence."

Every script in this suite:
- Tests outcomes the user experiences, not implementation details
- Runs independently with no manual setup required
- Returns clear pass/fail with diagnostic output
- Handles its own setup and teardown
- Times out gracefully if services are unavailable

## Maintenance

When the PRD or Vision changes:
1. Update affected verification scripts to match new requirements
2. Add new scripts for new acceptance criteria
3. Remove scripts for removed features (don't leave zombie tests)
4. Run `bash run_all.sh` to ensure all tests still pass

## Troubleshooting

**Tests fail with "Connection refused"**
- The HTTP server may not have started. Check that ports 8765-8767 are available.

**Tests fail with "Browser not found"**
- Run `playwright install chromium` to install browsers.

**Tests hang or timeout**
- Check that index.html exists in the sprint directory.
- Verify no infinite loops in JavaScript code.

**Tests pass but app doesn't work in real browser**
- This suggests the tests are not comprehensive enough. Add more verifications.
- Check console for JavaScript errors not caught by tests.
