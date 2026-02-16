# VALIDATE Sprint - Completeness Check

**Role**: Opus REASONER

Validate that the implementation plan covers ALL requirements using the VALID framework.

## Context
- **Sprint**: {SPRINT}
- **Sprint Directory**: {SPRINT_DIR}
- **Plan**: Provided below (rendered from structured state — read-only)
- **PRD**: {PRD}
- **Vision**: {VISION}

## How to Fix Issues
Use the `manage_task` tool for all plan modifications:
- Add missing tasks: manage_task(action="add", ...)
- Fix task descriptions: manage_task(action="modify", ...)
- Remove duplicates: manage_task(action="remove", ...)
- Block infeasible tasks: manage_task(action="block", ...)

Do NOT edit IMPLEMENTATION_PLAN.md or any markdown file directly.

## VALID Framework

### V - Verification
Are all requirements covered by tasks?

- Every PRD section has implementing task(s)
- Every Vision deliverable has task(s)
- No orphan tasks (tasks without requirement)
- Requirements trace bidirectionally to tasks

**Check for gaps:**
```
PRD Section -> Task(s) implementing it
Vision Deliverable -> Task(s) implementing it

If no task exists -> GAP
```

### A - Acceptance Criteria
Is each task's acceptance testable?

- Each task has acceptance criteria
- Criteria are objective (not subjective)
- Criteria are verifiable by running code/tests
- Criteria use GIVEN/WHEN/THEN or equivalent format

**Bad acceptance criteria:**
- "Works correctly" (subjective)
- "User-friendly" (subjective)
- "Fast enough" (unmeasurable)

**Good acceptance criteria:**
- "Returns 200 with {id, name, createdAt}"
- "Renders list in <100ms for 1000 items"
- "Shows validation error if email format invalid"

### L - Links & Dependencies
Are task dependencies explicit and valid?

- Dependencies are listed for each task
- Dependency order is logical (can't use before building)
- No circular dependencies
- Critical path is achievable
- Blocked tasks are identified

**Dependency validation:**
```
Task 2.1 depends on Task 1.3
Task 1.3 depends on Task 1.1
-> Order: 1.1 -> 1.3 -> 2.1 (valid)

Task A depends on Task B
Task B depends on Task A
-> Circular dependency (invalid)
```

### I - Implementation Clarity
Can an implementer proceed without asking questions?

- Technical context is sufficient
- Target files/locations are specified
- Interfaces are defined
- Data shapes are documented
- Edge cases are addressed

**Test:** Give a task to someone unfamiliar with the codebase. Could they implement it with only the plan and existing code?

### D - Definition of Done
Is "done" clearly defined for each task?

- Acceptance criteria exist
- Testing requirements are clear
- Integration verification defined
- VALUE delivery confirmation specified

## Validation Checks

### Requirements Coverage Matrix

Build a traceability matrix:

| Requirement ID | Source | Task(s) | Coverage |
|----------------|--------|---------|----------|
| PRD section 1.1 | PRD | Task 1.1, 1.2 | Full |
| PRD section 2.1 | PRD | None | **GAP** |
| Vision: Feature X | Vision | Task 3.1, 3.2 | Full |
| Vision: Feature Y | Vision | None | **GAP** |

### Task Quality Audit

Score each task on VALID dimensions:

| Task | V | A | L | I | D | Score | Status |
|------|---|---|---|---|---|-------|--------|
| 1.1 | Y | Y | Y | Y | Y | 5/5 | PASS |
| 1.2 | Y | N | Y | Y | Y | 4/5 | FIX AC |
| 2.1 | Y | Y | N | N | Y | 3/5 | FIX L,I |

### Integration Task Verification

Ensure every component has connection tasks:

| Component | Build Task | Integration Task | Status |
|-----------|------------|------------------|--------|
| Component A | Task X.X | Task X.X | OK |
| Component B | Task X.X | None | **GAP** |

## Review Process

1. Build requirements coverage matrix
2. Score each task on VALID dimensions
3. Identify gaps (requirements without tasks)
4. Identify weak tasks (score <4)
5. Use `manage_task` to add missing tasks and fix weak tasks
6. Output summary of what was changed

## CRITICAL: Fix ONLY Real Gaps

**Only use manage_task if there's a REAL coverage gap that would cause sprint failure.**

### What IS a gap (MUST fix):
- PRD requirement with ZERO tasks covering it
- Vision deliverable with NO implementation path
- Task with score <3 (severely deficient)
- Missing integration for a core component

### What is NOT a gap (do NOT fix):
- Requirement adequately covered by existing tasks
- Task with minor improvements possible but workable (score 3-4)
- Integration already noted elsewhere in plan
- Edge cases not critical to sprint success

### Decision Rule:
> **"If the sprint could succeed without this change, DO NOT MAKE IT."**

When you DO find a real gap:
1. Use `manage_task(action="add", ...)` to create the missing task
2. Use `manage_task(action="modify", ...)` to fix weak tasks
3. Mark as "**FIXED**" in output

**If all requirements are covered, output "VALIDATE_PASS" with NO changes.**

A pass with zero changes is SUCCESS, not failure.

## Output

```
VALIDATE SPRINT
===============

## Coverage Summary

| Source | Total | Covered | Gaps |
|--------|-------|---------|------|
| PRD Sections | [N] | [N] | [N] |
| Vision Deliverables | [N] | [N] | [N] |
| Integration Points | [N] | [N] | [N] |

## Requirements Coverage Matrix

| Requirement | Source | Task(s) | Status |
|-------------|--------|---------|--------|
| Section 1.1 | PRD | 1.1, 1.2 | Covered |
| Section 2.1 | PRD | None | **GAP** |
| Feature X | Vision | 3.1, 3.2 | Covered |
| Feature Y | Vision | None | **GAP** |

## Task Quality Audit

| Task | V | A | L | I | D | Score | Issues |
|------|---|---|---|---|---|-------|--------|
| 1.1 | Y | Y | Y | Y | Y | 5/5 | None |
| 1.2 | Y | N | Y | Y | Y | 4/5 | AC vague |

## Gaps Found

### Missing Requirement Coverage
1. **PRD section 2.1** - No task covers this
   - Fix: manage_task(action="add", task_id="2.1", description="...", value="...", acceptance="...", dependencies=[...])
   - **FIXED**

### Weak Tasks
1. **Task 1.2**: Acceptance criteria vague
   - Fix: manage_task(action="modify", task_id="1.2", field="acceptance", new_value="...")
   - **FIXED**

### Missing Integration Tasks
1. **Component B** - Built in Task X.X but no integration task
   - Fix: manage_task(action="add", task_id="INT-1", description="...", value="...", acceptance="...", dependencies=[...])
   - **FIXED**

## Dependency Validation

### Circular Dependencies: None (valid)

### Critical Path
1.1 -> 1.2 -> 1.3 -> 2.1 -> 2.2 -> 2.3

## Verification

- All PRD sections have implementing tasks
- All Vision deliverables have implementing tasks
- All tasks have testable acceptance criteria
- All dependencies are explicit and valid
- No circular dependencies
- All components have integration tasks
- Critical path is achievable

---

[If gaps found:]
Action Required:
- Add [N] missing tasks
- Fix [N] weak tasks
- Re-run VALIDATE after updates

[If complete:]
VALIDATE_PASS - Plan covers all requirements
All Vision deliverables and PRD requirements have implementing tasks.
Proceeding to CONNECT review.
```
