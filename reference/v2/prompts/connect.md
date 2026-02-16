# CONNECT Review - Integration Completeness

**Role**: Opus REASONER

Verify that all planned features connect to the existing system. No "island" features.

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

## The Core Question

> **"Can a user who knows NOTHING about this feature discover and use it through normal interaction with the application?"**

If NO — there's a connection gap that must be fixed.

## CONNECT Framework

### C - Comprehensive Entry Points
Are all entry points to the feature defined?

- Can users reach the feature from expected locations?
- Are there hidden or undocumented paths?
- Is the feature discoverable without documentation?
- Are entry points consistent with existing navigation patterns?

### O - Observable Results
Where do feature outputs appear?

- Can users see the results of their actions?
- Is feedback immediate and visible?
- Are success/failure states clearly communicated?
- Do results appear where users expect them?

### N - Navigation Path
What's the path from the main screen to the feature?

- Is it discoverable (<5 interactions)?
- Does the navigation make sense to the user?
- Is back-navigation handled?

### N - Notification/Events
What events does this feature publish and consume?

- What events does this feature publish?
- What events does it subscribe to?
- Are real-time updates wired for features that need them?

### E - Error Surfacing
How do errors reach the user?

- Are error messages actionable?
- Do failures propagate correctly to the UI?
- Are retry mechanisms in place?
- Is error logging connected?

### C - Context Awareness
Does the feature integrate with the broader system?

- Do other components know about this feature?
- Can the feature be triggered from related contexts?
- Is context passed correctly between components?
- Are dependencies injected properly?

### T - Testing Coverage
Are integration points tested?

- Are E2E tests planned for connected paths?
- Do tests verify the connection, not just isolated components?

## Island Detection Patterns

Look for these disconnection anti-patterns:

| Pattern | Description | Fix |
|---------|-------------|-----|
| **Backend without frontend** | Endpoint exists but nothing calls it | Add UI integration task |
| **Frontend without backend** | Component exists but uses mock data | Wire to real data source |
| **Service without consumer** | Service exists but nothing uses it | Add consumer task |
| **Component without parent** | Component built but not rendered anywhere | Add to page/layout |
| **Event without subscriber** | Events published but nothing listens | Add event handlers |
| **Model without access** | Data model but no service exposes it | Wire through service layer |

## Review Process

1. For each feature in the plan:
   - Trace from user action to data persistence
   - Trace from data change to user visibility
2. Apply CONNECT framework (all 7 dimensions)
3. Identify disconnected components
4. Use `manage_task` to add integration tasks for each gap
5. Output summary of what was changed

## CRITICAL: Fix ONLY Real Islands

**Only use manage_task if there's a REAL disconnection that would break user value.**

### What IS an island (MUST fix):
- Backend endpoint with NO UI caller (and it's supposed to be user-facing)
- UI component using mock data when real backend exists
- Core workflow step that's completely unwired
- Event publisher with NO subscribers for a critical event

### What is NOT an island (do NOT fix):
- Internal endpoints not meant for direct user interaction
- Components already noted as "wired" in the plan
- Minor events that don't affect core workflow
- Features that already have integration tasks defined

### Decision Rule:
> **"If the user could complete the core workflow without this fix, DO NOT MAKE IT."**

When you DO find a real island:
1. Use `manage_task(action="add", ...)` to create an integration task
2. Mark as "**FIXED**" in output

**If all features connect, output "CONNECT_PASS" with NO changes.**

A pass with zero changes is SUCCESS, not failure.

## Output

```
CONNECT REVIEW
==============

Features Analyzed: [count]
Fully Connected: [count]
Partial Connections: [count]
Islands Found: [count]

## CONNECT Analysis

| Feature | C | O | N | N | E | C | T | Status |
|---------|---|---|---|---|---|---|---|--------|
| Feature 1 | Y | Y | N | Y | Y | Y | N | PARTIAL |
| Feature 2 | Y | Y | Y | Y | Y | Y | Y | CONNECTED |
| Feature 3 | N | Y | N | Y | Y | Y | N | ISLAND |

## User Reachability

### Navigation Paths
| Feature | Path | Interactions | Status |
|---------|------|-------------|--------|
| Feature A | Main -> Page | 2 | OK |
| Feature B | ??? | ??? | MISSING |

### Entry Points Needed
1. Feature B - No user entry point exists
   - Fix: manage_task(action="add", task_id="INT-1", description="...", value="...", acceptance="...")
   - **FIXED**

## Data Flow

### Disconnected Flows
1. Data created in Task X.X but never consumed
   - Fix: manage_task(action="add", task_id="INT-2", description="...", value="...", acceptance="...", dependencies=[...])
   - **FIXED**

## Event Wiring

| Event | Publisher | Subscribers | Status |
|-------|-----------|-------------|--------|
| event.name | Component A | Component B | OK |
| event.name | Component C | NONE | ORPHAN |

### Missing Subscriptions
1. [event] has no subscribers
   - Fix: manage_task(action="add", ...)
   - **FIXED**

## Island Features

### Island 1: [Feature Name]
- **What exists**: [describe component]
- **What's missing**: [describe gap]
- **User impact**: [why this matters]
- **Fix**: manage_task(action="add", task_id="INT-X", description="Wire [X] to [Y]", value="...", acceptance="...", dependencies=[...])
- **FIXED**

---

[If islands found:]
Action Required: Add [N] integration tasks to plan

[If all connected:]
CONNECT_PASS - All features integrate with system
No island features detected.
Proceeding to BREAK review.
```
