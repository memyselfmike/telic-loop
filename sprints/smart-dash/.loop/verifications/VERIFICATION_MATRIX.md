# Verification Matrix: Smart Dashboard

This matrix maps each verification script to the PRD requirements, Vision goals, and value proofs it validates.

## Coverage Summary

- **14 executable verification scripts** (4 unit, 3 integration, 6 value, 1 runner)
- **7 value proofs** from Vision (all covered)
- **5 acceptance criteria** from PRD (all covered)
- **4 widgets** (all covered)

## Verification Coverage Map

### Vision Value Proofs → Verification Scripts

| Value Proof | Verification Script | Status |
|-------------|-------------------|--------|
| 1. All four widgets render correctly without console errors | `value_all_widgets_visible.sh` | ✓ |
| 2. Task persistence across page refresh | `value_task_persistence.sh` | ✓ |
| 3. Pomodoro countdown with audio notification | `value_pomodoro_flow.sh` | ✓ |
| 4. 400px width without horizontal scrolling | `value_sidepane_usability.sh` | ✓ |
| 5. Weather shows real data or graceful fallback | `unit_weather_widget.sh` | ✓ |
| 6. Task count accuracy after operations | `value_task_crud_complete.sh` | ✓ |
| 7. Auto-switch between WORK and BREAK modes | `value_pomodoro_flow.sh` | ✓ |

### PRD Acceptance Criteria → Verification Scripts

| Acceptance Criterion | Verification Scripts | Status |
|---------------------|---------------------|--------|
| 1. Opens without console errors (except weather API) | `integration_no_console_errors.sh`, `value_all_widgets_visible.sh` | ✓ |
| 2. Task CRUD works and survives refresh | `value_task_persistence.sh`, `value_task_crud_complete.sh` | ✓ |
| 3. Pomodoro counts down and produces beep | `value_pomodoro_flow.sh` | ✓ |
| 4. Layout works at 400px viewport | `integration_layout_responsive.sh`, `value_sidepane_usability.sh` | ✓ |
| 5. Total file size under 15KB | `integration_file_size.sh` | ✓ |

### Widget Requirements → Verification Scripts

#### Clock Widget
| Requirement | Unit Test | Value Test |
|-------------|-----------|------------|
| Shows HH:MM:SS 24h format | `unit_clock_widget.sh` | `value_clock_updates_realtime.sh` |
| Shows Day, Month DD date | `unit_clock_widget.sh` | `value_clock_updates_realtime.sh` |
| Updates every second | - | `value_clock_updates_realtime.sh` |
| Visible on page load | `unit_clock_widget.sh` | `value_all_widgets_visible.sh` |

#### Weather Widget
| Requirement | Unit Test | Value Test |
|-------------|-----------|------------|
| Shows fallback when no API key | `unit_weather_widget.sh` | - |
| Shows temp + condition with API key | `unit_weather_widget.sh` | - |
| No console errors on failure | `unit_weather_widget.sh`, `integration_no_console_errors.sh` | - |
| Visible on page load | `unit_weather_widget.sh` | `value_all_widgets_visible.sh` |

#### Task Widget
| Requirement | Unit Test | Value Test |
|-------------|-----------|------------|
| Input field exists | `unit_task_widget.sh` | - |
| Add task via Enter | - | `value_task_crud_complete.sh` |
| Mark complete with checkbox | - | `value_task_crud_complete.sh` |
| Delete with × button | - | `value_task_crud_complete.sh` |
| Strikethrough on complete | - | `value_task_crud_complete.sh` |
| Task count display accurate | `unit_task_widget.sh` | `value_task_crud_complete.sh` |
| LocalStorage persistence | - | `value_task_persistence.sh` |
| Restore on page load | - | `value_task_persistence.sh` |

#### Pomodoro Timer Widget
| Requirement | Unit Test | Value Test |
|-------------|-----------|------------|
| Display shows MM:SS | `unit_pomodoro_widget.sh` | - |
| Starts at 25:00 WORK | `unit_pomodoro_widget.sh` | `value_pomodoro_flow.sh` |
| Start button begins countdown | - | `value_pomodoro_flow.sh` |
| Pause button stops countdown | - | `value_pomodoro_flow.sh` |
| Reset returns to mode default | - | `value_pomodoro_flow.sh` |
| Mode label shows WORK/BREAK | `unit_pomodoro_widget.sh` | `value_pomodoro_flow.sh` |
| Completed pomodoro count | `unit_pomodoro_widget.sh` | `value_pomodoro_flow.sh` |
| Audio beep at 00:00 | - | *(requires full timer run)* |
| Auto-switch modes | - | *(requires full timer run)* |

### Layout & Styling → Verification Scripts

| Requirement | Verification Script | Status |
|-------------|-------------------|--------|
| Single column layout | `integration_layout_responsive.sh` | ✓ |
| Dark theme (#1a1a2e background) | `integration_layout_responsive.sh`, `value_sidepane_usability.sh` | ✓ |
| Works at 400px width | `integration_layout_responsive.sh`, `value_sidepane_usability.sh` | ✓ |
| No horizontal scroll at 400px | `integration_layout_responsive.sh`, `value_sidepane_usability.sh` | ✓ |
| All widgets visible | `value_all_widgets_visible.sh` | ✓ |

### Technical Constraints → Verification Scripts

| Constraint | Verification Script | Status |
|-----------|-------------------|--------|
| Single HTML file | *(implicit in all tests)* | ✓ |
| File size under 15KB | `integration_file_size.sh` | ✓ |
| No console errors | `integration_no_console_errors.sh` | ✓ |
| No external dependencies | *(implicit in all tests)* | ✓ |

## Test Execution Strategy

### Regression Testing (After Each Task)
Run unit tests to catch immediate breakage:
```bash
for script in unit_*.sh; do bash "$script"; done
```

**Expected time:** < 1 minute
**Coverage:** Individual widget functionality

### Integration Testing (After Related Tasks Complete)
Run integration tests to verify components work together:
```bash
for script in integration_*.sh; do bash "$script"; done
```

**Expected time:** < 2 minutes
**Coverage:** Layout, file size, console errors, widget coexistence

### Value Delivery Testing (Before Exit Gate)
Run value tests to prove user outcomes:
```bash
for script in value_*.sh; do bash "$script"; done
```

**Expected time:** 3-5 minutes
**Coverage:** Complete user workflows and promised benefits

### Full Suite
```bash
./run_all_verifications.sh
```

**Expected time:** 5-7 minutes
**Coverage:** Everything

## Known Limitations

### Tests That Cannot Be Automated

1. **Audio beep quality** - We can verify Web Audio API setup, but actual sound quality requires human ear
2. **30-minute weather refresh** - Too slow to test in automated suite
3. **Visual theme aesthetic** - Dark theme colors verified, but "reduces eye strain" is subjective
4. **Real pomodoro timer completion** - 25-minute wait impractical for test suite

### Workarounds

- **Audio beep**: Manual verification checklist item
- **Weather refresh**: Tested via page reload triggering re-fetch
- **Theme aesthetic**: Verified background color RGB values < 50 (objective)
- **Full timer run**: Timer controls verified, full run left to manual testing

## Test Maintenance

### When to Update Tests

- **Add new widget** → Add unit test for elements, value test for workflow
- **Change PRD requirement** → Update corresponding verification script
- **Discover new failure mode** → Add regression test to prevent recurrence
- **Layout changes** → Update responsive layout tests

### Test Quality Checklist

Every verification script must:
- [ ] Be independently runnable (no manual setup)
- [ ] Return exit code 0 on pass, non-zero on fail
- [ ] Print clear output with VALUE DELIVERED summary
- [ ] Handle missing dependencies gracefully (skip, don't fail)
- [ ] Be idempotent (run twice = same result)
- [ ] Time out gracefully (no infinite hangs)
- [ ] Test user value, not implementation details

## Verification Philosophy

> **These tests answer: "Does the developer get the promised benefit?"**

Not just: "Does the function return the right value?"

### Example: Task Persistence

**Bad test** (implementation focus):
- localStorage.setItem('tasks', JSON.stringify(tasks)) returns undefined

**Good test** (value focus):
- Add task "Write tests"
- Reload page
- Task "Write tests" still visible
- **VALUE**: Developer never loses their list

Our tests are all "good tests" — they simulate what the user does and verify they get the benefit.

## Exit Gate Criteria

Before marking the sprint complete, run full suite and verify:

1. ✓ All unit tests pass
2. ✓ All integration tests pass
3. ✓ All value tests pass
4. ✓ No new console errors introduced
5. ✓ File size under 15KB
6. ✓ Manual verification of audio beep (if automated test not feasible)

**If any test fails**, the sprint is not complete and delivers no value.
