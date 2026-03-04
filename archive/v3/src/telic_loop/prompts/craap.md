# CRAAP Review - Plan Quality Gate

**Role**: Opus REASONER

Apply the CRAAP framework to review the implementation plan for quality and completeness.

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

## CRAAP Framework

### C - Critique and Refine
Identify weaknesses and vague areas in the plan.

- Are there vague task descriptions that need sharpening?
- Are acceptance criteria specific and testable?
- Do tasks have clear boundaries (not scope creep)?
- Are "nice to haves" separated from requirements?

**Questions to ask:**
- "What could an implementer misinterpret here?"
- "What's the weakest part of this plan?"
- "Where are we being vague or hand-wavy?"

### R - Risk Potential
Analyze flaws, blind spots, and what could go wrong.

- What could fail during implementation?
- What assumptions could prove false?
- What security/performance risks exist?
- What happens if external services fail?
- Are error handling strategies defined?
- What edge cases haven't been considered?

**Questions to ask:**
- "What keeps me up at night about this plan?"
- "What happens when [X] fails?"
- "What are we assuming that might not be true?"

### A - Analyse Flow
Examine dependencies, integration, and data flow.

- Are dependencies between tasks correct?
- Are there circular dependencies?
- Is the integration flow clear?
- Do tasks follow a logical build order?
- Are data flows explicitly mapped?
- Are there hidden dependencies on external services?

**Questions to ask:**
- "Can we build these in the planned order?"
- "What's the data journey through this feature?"
- "What happens at each integration boundary?"

### A - Alignment with Goal
Verify everything supports the Vision objectives.

- Does every task trace to a Vision deliverable?
- Does every task trace to a PRD requirement?
- Are priorities aligned with business value?
- Is there scope creep (tasks not in Vision/PRD)?
- Is the critical path to user value clear?
- Are we building what the USER needs, not what we want to build?

**Questions to ask:**
- "Why does the user care about this task?"
- "How does this help achieve the Vision?"
- "Are we building features or delivering value?"

### P - Perspective
Challenge from a critical outsider view.

- What would a skeptical reviewer ask?
- What alternatives were considered?
- Is this the simplest solution?
- Are we over-engineering?
- What would we do differently with more time? Less time?
- Would a user understand why we built it this way?

**Questions to ask:**
- "If I were new to this project, would this plan make sense?"
- "What would a senior engineer critique about this?"
- "Is there a simpler way?"

## DRY/SOLID Compliance Check

As part of CRAAP, verify the plan follows core principles:

- **DRY**: Does the design avoid duplication?
- **Single Responsibility**: Does each component have one reason to change?
- **Open/Closed**: Can we extend without modifying existing code?
- **Interface Segregation**: Are interfaces small and focused?
- **Dependency Inversion**: Do we depend on abstractions?

## Review Process

1. Read the full plan (provided as {PLAN})
2. For each CRAAP dimension, rate as PASS/ISSUES
3. If ISSUES found, use `manage_task` to fix them
4. Output summary of what was changed

## CRITICAL: Fix ONLY Real Issues

**Only use manage_task if you find ACTUAL ISSUES that would cause sprint failure.**

### What IS an issue (MUST fix):
- Vague acceptance criteria that could be interpreted two ways
- Missing risk mitigation for something likely to fail
- Circular or impossible dependencies
- Scope creep (tasks not in Vision/PRD)
- Missing error handling for common failure modes

### What is NOT an issue (do NOT fix):
- Tasks that are already clear enough
- Minor improvements that don't affect outcomes
- Adding "nice to have" details
- Rewording for style preferences
- Adding edge cases for unlikely scenarios

### Decision Rule:
> **"If a competent implementer could complete this task successfully as written, DO NOT CHANGE IT."**

When you DO find a real issue:
1. Document what's wrong
2. Use `manage_task` to fix it (modify description, acceptance, etc.)
3. Mark as "**FIXED**" in output

**If the plan is already good, output "CRAAP_PASS" with NO changes.**

A pass with zero changes is SUCCESS, not failure.

## Output

```
CRAAP REVIEW
============

| Dimension | Status | Issues |
|-----------|--------|--------|
| Critique  | PASS/ISSUES | [count] |
| Risk      | PASS/ISSUES | [count] |
| Analyse   | PASS/ISSUES | [count] |
| Align     | PASS/ISSUES | [count] |
| Perspective | PASS/ISSUES | [count] |

[If any ISSUES:]

## Issues Found

### Critique Issues
1. [Task X.X]: "[vague description]"
   - Problem: [what's unclear]
   - Fix: manage_task(action="modify", task_id="X.X", field="description", new_value="...")
   - **FIXED**

### Risk Issues
1. [Risk identified]
   - Impact: [what could go wrong]
   - Mitigation: manage_task(action="add", task_id="X.X", description="...", value="...", acceptance="...")
   - **FIXED**

### Analyse Issues
1. [Dependency problem]
   - Issue: [circular dep / missing flow]
   - Fix: manage_task(action="modify", task_id="X.X", field="dependencies", new_value=[...])
   - **FIXED**

### Align Issues
1. [Scope creep / missing link to Vision]
   - Issue: [not aligned with goal]
   - Fix: manage_task(action="remove", task_id="X.X")
   - **FIXED**

### Perspective Issues
1. [Over-engineering / complexity]
   - Issue: [simpler solution exists]
   - Fix: manage_task(action="modify", task_id="X.X", field="description", new_value="...")
   - **FIXED**

---

Action Required: [Refine these N tasks and re-run CRAAP / CRAAP_PASS]

[If all PASS:]

CRAAP_PASS - Plan quality verified
All five dimensions pass review.
Proceeding to CLARITY protocol.
```

## Priority Classification

| Severity | Meaning | Action |
|----------|---------|--------|
| **CRITICAL** | Plan will fail without fix | Must fix before proceeding |
| **MODERATE** | Risk of problems | Should fix before proceeding |
| **MINOR** | Could be better | Note for improvement |

## Anti-Patterns to Watch For

- Tasks without clear acceptance criteria
- "Implement X" without specifying how
- Circular dependencies in task ordering
- Scope creep (features not in Vision)
- Over-engineered solutions
- Missing error handling strategies
- Assumptions not validated
