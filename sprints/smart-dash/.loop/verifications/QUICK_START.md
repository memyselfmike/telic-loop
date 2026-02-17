# Quick Start: Running Verifications

## TL;DR

```bash
# Run everything
cd sprints/smart-dash/.loop/verifications
./run_all_verifications.sh

# Or run by category
for script in unit_*.sh; do bash "$script"; done          # Fast unit tests
for script in integration_*.sh; do bash "$script"; done   # Integration tests
for script in value_*.sh; do bash "$script"; done         # Value delivery tests
```

## What These Tests Prove

✅ **Clock Widget** - Shows current time updating every second (no more alt-tabbing)  
✅ **Weather Widget** - Shows weather or graceful fallback (plan breaks without leaving page)  
✅ **Task Widget** - Full CRUD + localStorage persistence (never lose your list)  
✅ **Pomodoro Timer** - Start/Pause/Reset controls work (healthy work-break cadence)  
✅ **Layout** - Works at 400px width without scrolling (fits beside editor)  
✅ **File Size** - Under 15KB constraint (lightweight single file)  
✅ **No Errors** - Page loads without console errors (clean experience)  

## What Success Looks Like

```
════════════════════════════════════════════════════════════════
  Smart Dashboard - Complete Verification Suite
════════════════════════════════════════════════════════════════

═══ UNIT VERIFICATIONS ═══
Running: unit_clock_widget
✓ PASSED

Running: unit_weather_widget
✓ PASSED

Running: unit_task_widget
✓ PASSED

Running: unit_pomodoro_widget
✓ PASSED

═══ INTEGRATION VERIFICATIONS ═══
Running: integration_file_size
✓ PASSED

Running: integration_layout_responsive
✓ PASSED

Running: integration_no_console_errors
✓ PASSED

═══ VALUE DELIVERY VERIFICATIONS ═══
Running: value_all_widgets_visible
✓ PASSED

Running: value_clock_updates_realtime
✓ PASSED

Running: value_pomodoro_flow
✓ PASSED

Running: value_sidepane_usability
✓ PASSED

Running: value_task_crud_complete
✓ PASSED

Running: value_task_persistence
✓ PASSED

════════════════════════════════════════════════════════════════
  VERIFICATION SUMMARY
════════════════════════════════════════════════════════════════

  Passed:  13
  Failed:  0
  Skipped: 0
  Total:   13

All verifications passed!
```

## If Tests Fail

Each test prints clear diagnostic output:

```
FAIL: Clock did not update after 2 seconds
  This means the developer cannot see real-time updates
```

**Read the error message** - it tells you exactly what broke and why it matters to the user.

## Requirements

- **Node.js** with Playwright installed
- Tests auto-skip if dependencies missing (not counted as failures)

## More Info

- `README.md` - Full test documentation
- `VERIFICATION_MATRIX.md` - Coverage map (PRD → Tests → Value)

## Exit Gate Checklist

Before marking sprint complete:

- [ ] Run `./run_all_verifications.sh`
- [ ] All tests pass (0 failures)
- [ ] File size under 15KB
- [ ] Manual test: Start timer, wait for beep at 00:00 (if not automated)

**If anything fails, the sprint is not done.** A passing test suite is the only proof of value delivery.
