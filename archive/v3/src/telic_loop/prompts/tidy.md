# TIDY-FIRST - Prepare Codebase for Implementation

**Role**: Opus REASONER

Apply Kent Beck's "Tidy First?" principles to identify preparatory work needed before building new features.

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

## The Tidy First Principle

> **"Make the change easy, then make the easy change."**
> -- Kent Beck

Before implementing new features, identify structural changes that will make the implementation smoother. Tidyings are small, behavior-preserving changes that improve code structure.

## Types of Tidyings

### 1. Guard Clauses
Convert nested conditionals to early returns. Reduces nesting, clarifies logic for tasks that will add more conditions.

### 2. Dead Code Removal
Remove code that's no longer used: unused functions, commented-out blocks, unreachable paths, deprecated flags.

### 3. Normalize Symmetries
Make similar things look similar: consistent naming patterns, parameter ordering, return shapes, error handling patterns.

### 4. Extract Helper
Pull out reusable logic into named functions when the same pattern repeats in 3+ places.

### 5. Slide Statements
Group related code together. Move declarations closer to usage. Separate concerns with blank lines.

### 6. Chunk Statements
Add blank lines to separate logical groups. Makes code scannable. Creates visual paragraphs.

### 7. Reorder
Arrange code in reading order: public before private, high-level before low-level, call order matches definition order.

## When to Tidy

| Situation | Tidy First? | Reason |
|-----------|-------------|--------|
| Change is in unfamiliar code | **Yes** | Understand before changing |
| Change touches many files | **Yes** | Reduce coupling first |
| Code is hard to read | **Yes** | Clarify structure |
| Existing patterns don't fit new feature | **Yes** | Create right abstraction |
| Change is simple and localized | **No** | Just make the change |
| Tidying would be larger than change | **No** | Separate effort for tidying |
| Under time pressure for critical fix | **No** | Fix now, tidy later |

## Analysis Steps

### 1. Identify Target Files

Based on the plan, identify files that will be modified by multiple tasks. These are the highest-value tidying targets.

### 2. Assess Current State

For each target file, check:
- **Complexity**: Long functions? Deep nesting?
- **Duplication**: Repeated patterns?
- **Coupling**: Too many dependencies?
- **Readability**: Clear or confusing?
- **Tests**: Adequate coverage?

### 3. Plan Tidyings

For each issue found, assess whether it blocks planned work:

| Issue | Type | Location | Effort | Priority |
|-------|------|----------|--------|----------|
| Example: Nested ifs in validate() | Guard Clauses | service.py:45 | Small | High |
| Example: Repeated error formatting | Extract Helper | handler.py:23,56,89 | Small | Medium |

### 4. Create PREP Tasks

When tidying is genuinely needed, use `manage_task(action="add", ...)` to create PREP tasks that should run before the affected implementation tasks.

## CRITICAL: Fix ONLY When Tidying is Required

**Only add PREP tasks if code is ACTUALLY blocking implementation.**

### What REQUIRES prep (MUST fix):
- Existing code structure that BLOCKS a planned task
- Shared utility that 3+ tasks need and doesn't exist
- Technical debt that will cause task failure

### What does NOT require prep (do NOT fix):
- Code that could be "cleaner" but works
- Minor refactoring opportunities
- Nice-to-have abstractions
- Style improvements

### Decision Rule:
> **"If the tasks could be completed successfully with current code, DO NOT ADD PREP."**

When you DO find required prep:
1. Use `manage_task(action="add", task_id="PREP-X", description="...", value="...", acceptance="...", phase="0", dependencies=[...])` to create the prep task
2. Use `manage_task(action="modify", task_id="X.X", field="dependencies", new_value=[..., "PREP-X"])` to make affected tasks depend on it
3. Mark as "**FIXED**" in output

**If codebase is ready, output "TIDY_PASS" with NO changes.**

A pass with zero changes is SUCCESS, not failure.

## What to Look For

### Missing Abstractions
- Will multiple tasks need the same pattern?
- Should a shared interface be created first?
- Are there utilities to extract?

### Structural Issues
- Does current structure support planned features?
- Will tasks fight against existing patterns?
- Is refactoring needed before building?

### Technical Debt
- Does existing debt block new work?
- Should debt be paid before adding more code?
- Are there known issues to address first?

### Setup Requirements
- Database migrations needed?
- Configuration changes required?
- Dependencies to install?
- Environment variables to add?

## Output

```
TIDY-FIRST REVIEW
=================

## Summary

- **Files Analyzed**: [N]
- **Tidyings Needed**: [N]
- **PREP Tasks Added**: [N]
- **Deferred**: [N]

## Target Files

| File | Tasks Using | Issues Found | Tidy Needed |
|------|-------------|--------------|-------------|
| path/to/service | 1.1, 1.2 | Nested ifs, dead code | Yes |
| path/to/handler | 1.2, 1.3 | Repeated error handling | Yes |
| path/to/page | 2.1, 2.2 | None | No |

## PREP Tasks Added

### PREP-1: [Description]

**Type**: [Guard Clauses / Extract Helper / Dead Code / etc.]
**Reason**: [Why this blocks planned tasks]
**Affected tasks**: [which tasks benefit]

Fix:
  manage_task(action="add", task_id="PREP-1", description="...", value="...", acceptance="...", phase="0")
  manage_task(action="modify", task_id="1.1", field="dependencies", new_value=["PREP-1"])

**FIXED**

---

## Tidyings Deferred

| File | Type | Reason |
|------|------|--------|
| path/to/legacy | Major refactor | Would be larger than sprint |
| path/to/utils | Normalize | Low priority, doesn't affect sprint tasks |

## Codebase Readiness

### Before Tidying
- Blocking issues: [N] instances
- Prep work needed: [N] tasks

### After Tidying
- Blocking issues: 0 instances
- PREP tasks created: [N]

## Verification

- All prep tasks are structural only (no behavior change)
- All prep tasks are genuinely required by implementation tasks
- PREP tasks are correctly wired as dependencies

---

[If codebase needs prep:]
Action Required: [N] PREP tasks added before Phase 1

[If ready:]
TIDY_PASS - Codebase ready for implementation
No structural improvements required.
Planning phase complete.
```

## Anti-Patterns

- Changing behavior during tidying
- Large refactors instead of small tidyings
- Tidying code unrelated to sprint
- Creating PREP tasks for "nice to have" improvements
- Adding abstraction layers that aren't needed yet
