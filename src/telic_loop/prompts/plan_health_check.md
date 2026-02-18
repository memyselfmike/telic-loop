# Plan Health Check — Mid-Loop Quality Sweep

New tasks have been added to the plan during execution (from VRC gaps, course corrections, critical evaluations, or exit gate findings). These mid-loop tasks bypassed the original quality gates. Your job is to validate them against the current plan state and fix any issues.

## Context

- **Sprint**: {SPRINT}
- **Sprint Directory**: {SPRINT_DIR}
- **PRD**: {PRD}
- **Current Plan**: {PLAN}

### Existing Plan Tasks
{EXISTING_TASKS}

### Mid-Loop Tasks (to review)
{NEW_TASKS}

### Code Health Metrics
{CODE_HEALTH}

## The Core Principle

> **"Quality gates ran once at the start. The plan has mutated since then. The mutations need their own quality check — lighter than full gates, focused on what drifts."**

This is NOT a re-run of CRAAP/CLARITY/VALIDATE/CONNECT/BREAK/PRUNE. Those gates validate the plan against requirements, reality, and simplicity. Plan Health Check validates the plan against ITSELF — checking that mid-loop mutations have not introduced internal contradictions, redundancies, or drift.

## What to Check

### 1. DRY Violations (Duplicate Tasks)

Do any new tasks duplicate existing tasks? Check for:
- Same work described with different words
- Overlapping acceptance criteria
- Tasks targeting the same files with the same changes

**Action**: If duplicates found, remove the less specific one via `manage_task` (action: "remove"). If both have unique elements, merge into one via modify + remove.

### 2. Contradictions

Do any new tasks contradict existing tasks or completed work?
- Task A says "use approach X" while new Task B says "use approach Y" for the same component
- New task would undo work completed by a previous task
- Acceptance criteria that conflict with each other

**Action**: Resolve by modifying the contradicting task to align, or removing it if it is based on stale context.

### 3. Dependency Integrity

Are dependencies still valid after mutations?
- Do new tasks reference dependencies that exist?
- Have completed tasks been referenced as dependencies correctly?
- Are there orphan tasks (no dependencies and not depended upon) that should be connected?
- Are there cycles in the dependency graph?

**Action**: Fix via `manage_task` (action: "modify") to correct dependency lists.

### 4. Scope Drift

Has the plan drifted from the Vision and PRD?
- Count mid-loop tasks vs. original plan tasks. If mid-loop tasks outnumber original tasks, something is wrong.
- Are new tasks still traceable to PRD sections? Check prd_section field.
- Are new tasks delivering value toward the Vision, or are they maintenance/cleanup that does not advance the user's outcome?

**Action**: Descope tasks that do not trace to Vision value. Flag scope drift in output but do not over-correct — some mid-loop tasks are legitimate gap-fills.

### 5. Stale Tasks

Are any pending tasks no longer relevant given what has been completed?
- A task to "add error handling to X" when X was rewritten by a later task that already includes error handling
- A task to "create component Y" when Y was created as part of another task
- A task whose blocked_reason has been resolved but status was not updated

**Action**: Remove stale tasks via `manage_task` (action: "remove") or update status via modify.

### 6. Code Health / DRY / SOLID Violations

Review the Code Health Metrics above (if present). Check for:

- **Monolithic files** (500+ lines): Suggest splitting into focused modules. A single file handling routing, business logic, and data access is a SOLID violation.
- **Rapid growth** (150+ lines in one iteration): A file growing that fast is likely accumulating responsibilities. Flag for the builder to refactor.
- **Code concentration** (one file > 50% of codebase): The project has a single point of failure. Suggest extracting concerns into separate modules.
- **Long functions** (50+ lines): Functions exceeding the threshold indicate SRP violations. Suggest extracting helper functions.
- **Duplicate code blocks**: Identical code in multiple files is a DRY violation. Suggest extracting into shared utilities.
- **Debug artifacts**: print/console.log/breakpoint statements left in production code. Must be removed before shipping.
- **Low test ratio**: If test files are less than half the source file count, testing coverage is likely insufficient.
- **TODO debt**: Excessive TODO/FIXME/HACK markers indicate unfinished work or deferred decisions.

**Action**: If code health warnings are present, add a targeted quality task via `manage_task` (action: "add") with:
- description: which file(s) to fix and what specific violations to address
- value: "Reduce code quality risk — improve maintainability and reduce defect probability"
- acceptance: specific targets (e.g., "no file exceeds 400 lines", "no function exceeds 50 lines", "zero debug statements")

Do NOT add quality tasks if no code health warnings are present. Do NOT add tasks for files that are naturally large (e.g., generated code, test fixtures, configuration).

## Process

1. Read the current plan state (all tasks with status)
2. Identify mid-loop tasks (source != "plan")
3. For each mid-loop task, run the five checks above against the full task set
4. Apply fixes via `manage_task` tool calls
5. Summarize what was found and fixed

## Output

Apply any necessary fixes using `manage_task` tool calls during your analysis. After all fixes are applied, provide a brief text summary:

```
PLAN HEALTH CHECK
=================

Tasks reviewed: [N] mid-loop tasks
Issues found: [N]
  - DRY violations: [N] (merged/removed)
  - Contradictions: [N] (resolved)
  - Dependency issues: [N] (fixed)
  - Scope drift: [N] (descoped/flagged)
  - Stale tasks: [N] (removed/updated)

Scope assessment: ON_TRACK | DRIFTING | BLOATED
[If DRIFTING or BLOATED: brief explanation of the drift direction]
```

If no issues are found, output:

```
PLAN HEALTH CHECK
=================

Tasks reviewed: [N] mid-loop tasks
No issues found. Plan is internally consistent.
```

## Anti-Patterns

- Do NOT re-run full quality gates. This is a lightweight check focused on internal consistency of mutations, not comprehensive plan review.
- Do NOT remove tasks that are genuinely needed just because they were not in the original plan. Mid-loop tasks from VRC gaps and critical eval findings represent real discovered requirements.
- Do NOT flag every mid-loop task as "scope drift." Some drift is expected and healthy — the loop learns as it builds. Only flag drift that takes the plan AWAY from Vision value.
- Do NOT modify completed tasks. Tasks with status "done" are finished. If their output needs changing, create a new task.
- Do NOT spend more than a few minutes on this. It is a quick sweep, not a deep review. If the plan needs deep restructuring, that is Course Correction's job.
