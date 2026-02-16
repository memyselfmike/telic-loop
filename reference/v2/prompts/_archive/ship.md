# Ship Phase - Final Verification

## Your Role

Final verification before declaring the sprint complete and shippable.

## Context

- **Sprint**: {SPRINT}
- **VISION**: {SPRINT_DIR}/VISION.md
- **Value Checklist**: {SPRINT_DIR}/VALUE_CHECKLIST.md
- **Implementation Plan**: {SPRINT_DIR}/IMPLEMENTATION_PLAN.md

## Pre-Ship Checklist

### 1. All Tasks Complete
- [ ] Every task in IMPLEMENTATION_PLAN.md is [x] checked
- [ ] No tasks marked blocked without resolution
- [ ] No pending work items

### 2. All Value Delivered
- [ ] VALUE_CHECKLIST.md shows all [x] in VALUE column
- [ ] Every VISION deliverable verified
- [ ] User can achieve promised outcome

### 3. Quality Gates Passed
- [ ] All tests pass (no skipped)
- [ ] Lint clean
- [ ] Build succeeds
- [ ] No critical/major issues open

### 4. Integration Complete
- [ ] All features connected to system
- [ ] No island components
- [ ] End-to-end flows work

### 5. Documentation
- [ ] README updated if needed
- [ ] API changes documented
- [ ] ADRs written for significant decisions

### 6. The Final Question

> **"If the VISION user logged in right now, could they achieve
> the outcome they were promised? Would they get the value
> they expected? Would they use this TODAY?"**

If YES to all three → SHIP_READY
If YES for non-blocked deliverables → PARTIAL_SHIP (with blockers documented)
If NO to any non-blocked item → NOT_READY

### 7. Blocked Deliverables (if any)

If there are [B] blocked items in the plan:
- [ ] Blockers are documented in BLOCKERS.md
- [ ] Human actions are clearly specified
- [ ] Blocked value percentage is calculated
- [ ] Non-blocked deliverables still provide meaningful value

## Output

```
SHIP VERIFICATION
=================

Tasks: [X/X complete]
Value: [X/X verified]
Quality: [PASS/FAIL]
Integration: [PASS/FAIL]
Documentation: [PASS/FAIL]

Final Question:
- User can achieve outcome: [YES/NO]
- User gets expected value: [YES/NO]
- User would use TODAY: [YES/NO]

[If all YES:]

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ✅ SHIP_READY                                               ║
║                                                               ║
║   Sprint: {SPRINT}                                            ║
║   Deliverables: [count] verified                              ║
║   Value: DELIVERED                                            ║
║                                                               ║
║   The user can now achieve the VISION outcome.                ║
║   Ready for merge and deployment.                             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

[If YES for non-blocked, but has external blockers:]

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ⚠️  PARTIAL_SHIP                                            ║
║                                                               ║
║   Sprint: {SPRINT}                                            ║
║   Deliverables: [X/Y] verified ([Z] blocked)                  ║
║   Value Delivered: [X]%                                       ║
║   Value Blocked: [Y]%                                         ║
║                                                               ║
║   Non-blocked features deliver user value.                    ║
║   See BLOCKERS.md for required human actions.                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

BLOCKED DELIVERABLES:
1. [Deliverable] - Blocked by: [reason] - Human action: [what to do]
2. ...

[If any NO on non-blocked items:]

NOT_READY

Blocking Issues:
1. [Issue preventing ship]
2. ...

Action: Address issues and return to Phase 2
```

## Ship Summary Document

Create `{SPRINT_DIR}/SHIP_SUMMARY.md`:

```markdown
# Ship Summary

Sprint: {SPRINT}
Date: [timestamp]
Status: SHIPPED

## Value Delivered

| Deliverable | Value to User | Status |
|-------------|---------------|--------|
| [Feature 1] | [Benefit] | ✅ Verified |
| [Feature 2] | [Benefit] | ✅ Verified |
...

## User Outcome

The user described in VISION.md can now:
[Describe what they can achieve]

## Technical Summary

- Tasks completed: [count]
- Files changed: [count]
- Tests added: [count]
- Dependencies: [list new deps]

## Known Limitations

[Any scope limitations or future work]

## What's Next

[Recommendations for next sprint]
```
