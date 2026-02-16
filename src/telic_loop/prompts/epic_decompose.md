# Epic Decomposition — Breaking a Complex Vision into Deliverable Value Blocks

The Vision has been validated and classified as `multi_epic` — it is too complex for a single loop run. Your job is to decompose it into **epics**: independently valuable, sequentially deliverable blocks of work.

## Context

- **Sprint**: {SPRINT}
- **Sprint Directory**: {SPRINT_DIR}
- **Vision**: {SPRINT_DIR}/VISION.md
- **Vision Validation Result**: {VISION_VALIDATION_RESULT}

## The Core Principle

> **"Each epic delivers value the human can see and evaluate. If it doesn't, it's not an epic — it's a layer."**

Epics are horizontal slices (user can do X end-to-end), NOT vertical slices (database done, then API, then UI). Each epic, when complete, produces something the human can confirm is on track toward the full vision.

## Complexity Signals

The Vision was classified as `multi_epic` because it triggered one or more of:
- **Deliverable count**: >3 independently valuable deliverables
- **Estimated task count**: >15 tasks
- **Dependency depth**: >2 layers of sequential dependencies
- **Technology breadth**: >2 distinct technology domains
- **Integration surface**: Multiple external systems

## Decomposition Rules

### 1. Horizontal Value Slicing
Each epic must deliver something independently demonstrable. "The database schema is set up" is NOT an epic. "Users can create and view their profile" IS an epic.

### 2. Foundation First
Epic 1 should establish the minimum working foundation that all subsequent epics build on. It includes core infrastructure, the primary happy path, and basic data model.

### 3. Detail Gradient
- **Epic 1**: Full detail — specific deliverables, completion criteria, task-level breakdown
- **Epics 2-3**: Moderate detail — deliverables and completion criteria, but tasks are indicative not exhaustive
- **Epics 4-5**: Sketch only — value statement and key deliverables, details deferred until prior epics complete

### 4. Maximum 5 Epics
If the decomposition requires more than 5 epics, the vision is too large. Recommend splitting into separate visions.

### 5. Each Epic Has Explicit Completion Criteria
Borrowed from the Options Framework: each epic needs clear termination conditions so the loop knows when this epic is done and it's time for the feedback checkpoint.

## Instructions

Read the Vision document and the Vision Validation result. Then produce an ordered sequence of epics.

For each epic, provide:

```
EPIC {N}: {TITLE}
====================
VALUE_STATEMENT: "{User can X}" — one sentence, what the human can see and evaluate
DELIVERABLES:
  - [specific output 1]
  - [specific output 2]
COMPLETION_CRITERIA:
  - [verifiable condition 1]
  - [verifiable condition 2]
DEPENDS_ON: [epic IDs, or "none" for epic 1]
DETAIL_LEVEL: full | moderate | sketch
KEY_RISKS: [what could go wrong in this epic specifically]
```

For Epic 1 only, also provide:
```
TASK_SKETCH:
  - [task 1 — brief description]
  - [task 2 — brief description]
  ...
ESTIMATED_TASK_COUNT: N
```

## Output

Report your decomposition using the `report_epic_decomposition` tool:

```
{
  "epic_count": N,
  "epics": [
    {
      "epic_id": "epic_1",
      "title": "...",
      "value_statement": "...",
      "deliverables": ["...", "..."],
      "completion_criteria": ["...", "..."],
      "depends_on": [],
      "detail_level": "full",
      "key_risks": ["..."],
      "task_sketch": ["...", "..."],  // epic 1 only
      "estimated_task_count": N       // epic 1 only
    },
    ...
  ],
  "vision_too_large": false,  // true if >5 epics needed → recommend vision split
  "rationale": "Brief explanation of why this decomposition was chosen"
}
```

## Anti-Patterns

- Do NOT create vertical-slice epics (all backend, then all frontend, then all tests). Each epic must deliver end-to-end value.
- Do NOT detail all epics equally. Just-in-time decomposition: later epics will be shaped by learnings from earlier ones.
- Do NOT create epics with no demonstrable output. If you can't show the human something, it's not an epic boundary.
- Do NOT front-load all infrastructure into Epic 1. Include only the infrastructure needed for Epic 1's value delivery. Later infrastructure can be added when needed.
- Do NOT create one-task epics. If an epic has only 1-2 tasks, it should be merged with an adjacent epic.
