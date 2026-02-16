# CLARITY Protocol - Eliminate Ambiguity

**Role**: Opus REASONER

Apply the CLARITY protocol to eliminate ambiguity from the implementation plan.

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

## The Core Test

> **"Could two independent implementers read this and build EXACTLY the same thing?"**

If NO — there's ambiguity that must be eliminated.
If YES — move to the next concept.

## CLARITY Protocol Steps

For EACH task, apply all seven steps:

### C - CONCEPT
What are we defining? State it clearly.

- What exactly is this task asking for?
- What is the deliverable?
- What boundaries exist?

### L - LOWER BOUND
What would "too little" look like? Define the deficiency extreme.

- What's the minimum that would technically satisfy this but disappoint?
- What would a lazy implementation look like?
- Where might someone cut corners?

### A - AMBIGUITY TEST
Could two implementers still interpret this differently?

- Read the task as a pessimist — what could be misunderstood?
- Read the task as an optimist — what's assumed but not stated?
- What questions would a newcomer ask?

### R - REFINE
Sharpen boundaries until a single interpretation remains:

- Add specific numbers (not "fast" but "<200ms p95")
- Add explicit exclusions ("NOT including X, Y, Z")
- Add concrete examples ("Like A, not like B")
- Remove ALL weasel words
- Define exact data shapes, not "return user info"

### I - INTERPRETATION CHECK
Two-Implementer Test: Would they build identical implementations?

- Imagine two implementers in separate rooms
- Given only this plan and the codebase
- Would they produce the same result? Same UX? Same behavior?

### T - TRACE
Does this clarity connect to sprint success?

- How does this task deliver VALUE to the user?
- Is the connection to Vision explicit?
- Would removing this task impact the outcome?

### Y - YIELD
Output the precise specification.

- Write the unambiguous version
- Include all specifics discovered during R-step
- Document what was clarified

## Red Flag Words (Must Replace)

| Ambiguous Word | Replace With |
|----------------|--------------|
| Appropriate | Specific criteria |
| Sufficient | Exact threshold |
| Secure | List of specific controls |
| Fast | Specific ms target |
| User-friendly | Specific UX criteria |
| Scalable | Specific user/request count |
| Robust | Specific failure modes handled |
| Clean | Reference to specific standard |
| Simple | Complexity metrics |
| Properly | Exact verification steps |
| Handle | Specific behavior for each case |
| Support | List of specific capabilities |
| Flexible | Specific extension points |
| Intuitive | Specific interaction pattern |

## Non-Production-Ready Patterns

**If the Vision persona is non-technical, these patterns are AMBIGUOUS about production-readiness:**

| Non-Production-Ready | Production-Ready Clarification |
|---------------------|-------------------------------|
| "Run a CLI command to..." | "Add UI action that triggers..." |
| "Edit config file to..." | "Add configuration form that persists to..." |
| "Manual browser login required" | "Add in-app auth flow that stores session" |

**For non-technical users, ANY task requiring CLI or manual file editing is AMBIGUOUS.**

When you find such patterns:
1. Flag as requiring UI implementation
2. Use `manage_task(action="modify", ...)` to clarify with specific UI flow
3. If a new task is needed: `manage_task(action="add", ...)`

## Ambiguity Examples

### Ambiguous vs Clear

| Ambiguous | Clear |
|-----------|-------|
| "Implement user integration" | "Create endpoint that accepts {email, name}, validates, persists, returns {id, email, createdAt}" |
| "Add approval functionality" | "Approval action sets status='approved', publishes event, returns updated item" |
| "Create dashboard" | "Dashboard page with: pending count badge, status chart, last 10 items table" |
| "Handle errors properly" | "On client error: show inline message. On server error: show modal with retry. On network failure: show offline banner" |
| "Make it fast" | "Response <200ms p95. Render <100ms. No loading indicator for <50ms operations" |

## Review Process

1. Read each task in the plan
2. Apply CLARITY protocol (all 7 steps)
3. Identify ambiguous tasks
4. Use `manage_task` to fix ambiguous tasks
5. For CLI patterns with non-technical users: use `manage_task(action="add", ...)` for UI alternatives
6. Output summary of what was changed

## CRITICAL: Fix ONLY Real Ambiguity

**Only use manage_task if two implementers would ACTUALLY implement differently.**

### What IS ambiguity (MUST fix):
- Task could be interpreted two completely different ways
- Acceptance criteria is subjective ("works well", "fast enough")
- CLI pattern for NON-TECHNICAL user's RECURRING action (not one-time setup)
- Missing critical information that blocks implementation

### What is NOT ambiguity (do NOT fix):
- Task is clear enough for a competent implementer
- Minor details that don't affect outcome
- One-time developer setup tasks (CLI is fine for these)
- Tasks that already have specific acceptance criteria

### Decision Rule:
> **"If a competent implementer could implement this correctly as written, DO NOT CHANGE IT."**

When you DO find real ambiguity:
1. Use `manage_task(action="modify", ...)` to fix the specific issue
2. Mark as "**FIXED**" in output

For CLI patterns — ONLY add a task if:
- User persona is non-technical AND
- The action RECURS (session expires, needs periodic refresh) AND
- No existing task already addresses it

**If the plan is already clear, output "CLARITY_PASS" with NO changes.**

A pass with zero changes is SUCCESS, not failure.

## Output

```
CLARITY REVIEW
==============

Tasks Analyzed: [count]
Already Clear: [count]
Clarified: [count]
Red Flags Found: [count]

## Two-Implementer Test Results

| Task | Result | Notes |
|------|--------|-------|
| Task X.X | FAIL - "handle errors" vague | Fixed via manage_task |
| Task Y.Y | PASS | Already clear |

## Clarifications Applied

### Task X.X
**Original (Ambiguous):**
> "[quote from plan]"

**Clarified via manage_task:**
> manage_task(action="modify", task_id="X.X", field="description", new_value="[precise specification]")

**Boundaries:**
- INCLUDES: [explicit list]
- EXCLUDES: [explicit list]

**FIXED**

---

## Red Flags Replaced

| Task | Original | Replaced With |
|------|----------|---------------|
| X.X | "appropriate error handling" | "inline message for validation, modal for server errors" |
| Y.Y | "fast response" | "<200ms p95 response time" |

## Verification

- All tasks pass Two-Implementer Test
- All acceptance criteria have single interpretation
- All red flag words replaced
- No subjective language in critical paths

---

[If issues remain:]
Action Required: Clarify [N] remaining ambiguous tasks

[If all clear:]
CLARITY_PASS - All tasks unambiguous
Two independent implementers would build identical implementations.
Proceeding to VALIDATE.
```
