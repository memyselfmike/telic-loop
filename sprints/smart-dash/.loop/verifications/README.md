# Smart Dashboard Verification Suite

This directory contains executable verification scripts that prove the dashboard delivers its promised value.

## Philosophy

> **"A test that passes while the user gets no value is worse than no test at all — it creates false confidence."**

These scripts verify that the **user gets the promised outcome**, not just that functions return values.

## Script Categories

### Unit Verifications (Fast: < 10s)
Run after every task completion to catch regressions early.

- `unit_clock_widget.sh` - Clock displays time in correct format
- `unit_weather_widget.sh` - Weather widget shows fallback or real data
- `unit_task_widget.sh` - Task list elements exist and are interactive
- `unit_pomodoro_widget.sh` - Timer controls and display elements present

### Integration Verifications (Medium: < 60s)
Run after related tasks complete to verify components work together.

- `integration_layout_responsive.sh` - 400px layout works without scrolling
- `integration_file_size.sh` - Total file size under 15KB constraint
- `integration_no_console_errors.sh` - Page loads without JavaScript errors

### Value Delivery Verifications (Variable)
Run after milestone tasks and before exit gate to prove user value.

- `value_all_widgets_visible.sh` - All four widgets visible in one view (consolidation goal)
- `value_clock_updates_realtime.sh` - Clock updates every second (no more alt-tabbing to check time)
- `value_task_persistence.sh` - Tasks survive page reload (never lose task list)
- `value_task_crud_complete.sh` - Full task management workflow (add, complete, delete, count)
- `value_pomodoro_flow.sh` - Timer controls work (work-break cadence)
- `value_sidepane_usability.sh` - Dashboard usable at 400px width (fits beside editor)

## Running Verifications

### Run all verifications
```bash
./run_all_verifications.sh
```

### Run by category
```bash
# Unit tests only
for script in unit_*.sh; do bash "$script"; done

# Integration tests only
for script in integration_*.sh; do bash "$script"; done

# Value tests only
for script in value_*.sh; do bash "$script"; done
```

### Run individual test
```bash
./value_task_persistence.sh
```

## Requirements

- Node.js with Playwright installed
- Scripts automatically skip if dependencies are missing

## Understanding Results

### Exit Codes
- `0` = PASS - Feature works and delivers value
- `1` = FAIL - Feature broken or doesn't deliver value
- `0` with "SKIP" message = Dependencies missing (not a failure)

### Output Format
Each script prints:
1. What it's checking
2. Step-by-step progress
3. **VALUE DELIVERED** summary explaining user benefit
4. Clear pass/fail with actionable error messages

## Value Proofs from Vision

These scripts verify the 7 value proofs from the Vision:

1. ✓ All four widgets render correctly (value_all_widgets_visible.sh)
2. ✓ Task persistence across page refresh (value_task_persistence.sh)
3. ✓ Pomodoro timer countdown and notification (value_pomodoro_flow.sh)
4. ✓ 400px side-pane without scrolling (value_sidepane_usability.sh)
5. ✓ Weather shows real data or graceful fallback (unit_weather_widget.sh)
6. ✓ Task count accuracy (value_task_crud_complete.sh)
7. ✓ Auto-switch between WORK and BREAK modes (value_pomodoro_flow.sh)

## Anti-Patterns Avoided

- ❌ Tests that only check "no crash" — we assert actual values and behaviors
- ❌ Testing implementation details — we test user experience
- ❌ Manual setup requirements — scripts are self-contained
- ❌ Tests that pass trivially — we verify real functionality
- ❌ Tests that modify production data — we use clean test contexts

## Adding New Verifications

When adding a new verification script:

1. Use the category prefix: `unit_*`, `integration_*`, or `value_*`
2. Include a header comment with:
   - Verification purpose
   - PRD reference
   - Vision goal
   - Category
3. Make the script executable: `chmod +x script_name.sh`
4. Return exit code 0 on pass, non-zero on fail
5. Print clear output explaining what passed/failed
6. Handle missing dependencies gracefully (skip, don't fail)
7. **Focus on USER VALUE**, not just technical correctness

## Example: Reading Test Output

```bash
$ ./value_task_persistence.sh

=== Value: Task Persistence Across Reloads ===

Added task: Test task 1708123456789
✓ Task added successfully
✓ Task saved to localStorage
✓ Task persisted across reload
✓ Task completion persisted across reload

PASS: Task persistence works correctly
VALUE DELIVERED: Developer never loses their task list when browser closes
  ✓ Tasks saved to localStorage
  ✓ Tasks restored on page reload
  ✓ Task completion state persists
```

This output tells you:
1. **What was tested** - Task persistence
2. **How it was tested** - Added task, reloaded, verified presence
3. **Why it matters** - Developer never loses task list
4. **User benefit** - No server needed, works offline

## Technical Notes

- Scripts use Playwright for browser automation
- Scripts create temporary test files in `/tmp/`
- Each script is self-contained and idempotent
- Dark theme and responsive design verified via computed styles
- localStorage operations use clean test contexts
- Network errors for weather API are expected and acceptable
