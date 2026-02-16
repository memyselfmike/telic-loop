# System Coherence Evaluation — Does the Whole Work, Not Just the Parts?

Individual features pass QC and deliver value. But do they form a coherent system? This evaluation assesses emergent properties that arise from feature interactions — problems invisible at the component level.

## Context

- **Sprint**: {SPRINT}
- **Sprint Directory**: {SPRINT_DIR}
- **Mode**: {EVAL_MODE} (quick | full)
- **Current Iteration**: {ITERATION}
- **Features Implemented**: {FEATURE_COUNT}
- **Previous Coherence Report**: {PREVIOUS_REPORT}

## The Core Principle

> **"A dashboard with 5 well-built widgets can still be unusable if the widgets don't form a coherent information hierarchy."**

Regression testing catches broken features. QC catches bad implementations. Critical Eval catches bad individual experiences. This evaluation catches emergent problems — issues that only appear when you step back and look at the whole system.

## Mode: Quick (Dimensions 1-2)

If `{EVAL_MODE}` is `quick`, evaluate only Structural Integrity and Interaction Coherence. These are the fastest to assess and catch the most urgent emergent issues.

## Mode: Full (All 7 Dimensions)

If `{EVAL_MODE}` is `full`, evaluate all seven dimensions in order. Each builds on the previous.

---

## Dimension 1: Structural Integrity

**Question**: Does the system's actual structure match its intended architecture?

**Evaluate**:
1. **Dependency health**: Are there cyclic dependencies? Hub components with excessive connections? Unstable dependencies (stable modules depending on volatile ones)?
2. **Layering compliance**: Do dependencies flow in the intended direction (e.g., routes → services → repositories, not the reverse)?
3. **Responsibility distribution**: Is responsibility spread across modules, or concentrated in a God Component? Compute evenness — is there one module doing 40%+ of the work?
4. **Trend**: Compared to `{PREVIOUS_REPORT}`, is structural integrity improving, stable, or degrading?

---

## Dimension 2: Interaction Coherence

**Question**: Do features interact correctly and without unintended side effects?

**Evaluate**:
1. **Cross-cutting concerns**: Are auth, error handling, logging, validation, and state management implemented consistently across ALL features? Flag any feature that handles a cross-cutting concern differently.
2. **Shared state safety**: For data stores, caches, and global state accessed by multiple features — are access patterns compatible? Any race conditions, stale reads, or conflicting writes?
3. **Implicit coupling**: Are there features that don't explicitly depend on each other but share global state, database tables, environment variables, or file paths?
4. **Feedback loops**: Does Feature A's output feed into Feature B which affects Feature A? Flag all circular data flows.

---

## Dimension 3: Conceptual Integrity (full mode only)

**Question**: Does the system tell a coherent conceptual story?

**Evaluate**:
1. **Terminology consistency**: Is the same concept called the same thing everywhere? Flag synonyms (different words for same concept) and homonyms (same word for different concepts) across features.
2. **Pattern consistency**: Are analogous operations implemented using the same design pattern? Flag features that deviate from the established patterns.
3. **Abstraction level consistency**: Do analogous interfaces operate at the same abstraction level? Flag mixed abstraction (one endpoint returns raw DB rows, another returns domain objects).
4. **Convention adherence**: Naming conventions (casing, plural/singular, verb/noun), file organization, code structure — are they uniform?

---

## Dimension 4: Behavioral Consistency (full mode only)

**Question**: Does the system behave predictably across analogous situations?

**Evaluate**:
1. **Error handling symmetry**: Does the same error type (network failure, validation error, auth failure, not found) get handled the same way in every feature? Same error codes, message format, recovery options?
2. **State handling consistency**: Are loading states, empty states, and error states rendered consistently across features?
3. **Validation consistency**: Are the same data types (email, date, URL) validated with the same rules everywhere?
4. **Response format uniformity**: Do APIs use the same envelope, pagination, and error shapes? Do UI components use the same layout patterns for similar data?

---

## Dimension 5: Informational Flow Integrity (full mode only)

**Question**: Does data flow through the system cleanly?

**Evaluate**:
1. **Single source of truth**: For each piece of data, is there exactly one authoritative source? Flag data that could be read from multiple conflicting sources.
2. **Flow completeness**: For each user action, trace data from input → storage → display/confirmation. Flag incomplete flows (data stored but never shown, or shown but never persisted).
3. **Dead data**: Are there computed/stored values that nothing downstream consumes?
4. **Consistency across views**: Where the same data appears in multiple views, is it always the same value and format?

---

## Dimension 6: Resilience (full mode only)

**Question**: When something goes wrong, does the system degrade gracefully?

**Evaluate**:
1. **Failure cascade analysis**: For each major component, what happens if it becomes unavailable? How many other components fail? Is the blast radius contained?
2. **Error boundary coverage**: Does every async operation, external API call, and database query have error handling?
3. **Single points of failure**: Are there components whose failure takes down the entire system?
4. **Recovery paths**: After a transient failure, can the system recover automatically?

---

## Dimension 7: Evolutionary Capacity (full mode only)

**Question**: Can the system accommodate future change?

**Evaluate**:
1. **Coupling trend**: Is inter-module coupling increasing or stable compared to `{PREVIOUS_REPORT}`?
2. **Extension cost**: When new features are added, do they require modifying existing features? What's the ratio of modified-existing-files to new-files?
3. **API stability**: Are internal module interfaces stable, or do they change frequently?
4. **Dead code**: Is unused code, abandoned feature flags, or commented-out code accumulating?

---

## Output

Report your evaluation using the `report_coherence` tool:

```
{
  "mode": "quick | full",
  "iteration": {ITERATION},
  "dimensions": {
    "structural_integrity": {
      "status": "HEALTHY | WARNING | CRITICAL",
      "findings": ["specific finding with file references"],
      "trend": "improving | stable | degrading"
    },
    "interaction_coherence": { ... },
    // full mode only:
    "conceptual_integrity": { ... },
    "behavioral_consistency": { ... },
    "informational_flow": { ... },
    "resilience": { ... },
    "evolutionary_capacity": { ... }
  },
  "overall": "HEALTHY | WARNING | CRITICAL",
  "top_findings": [
    {
      "dimension": "...",
      "severity": "info | warning | critical",
      "description": "...",
      "affected_files": ["..."],
      "suggested_action": "...",
      "leverage_level": 6  // Meadows 1-12 — higher = more structural
    }
  ],
  "comparison_to_previous": "narrative of what changed since last check"
}
```

## Triggering Actions

- **HEALTHY across all dimensions**: No action. Continue executing.
- **WARNING on any dimension**: Log findings. Include in next Course Correction consideration. Do not interrupt current task.
- **CRITICAL on any dimension**: Trigger Course Correction. Structural issues must be addressed before adding more features — building on a degraded foundation wastes effort.

## Anti-Patterns

- Do NOT run full coherence evaluation before 3+ features exist — most dimensions are meaningless with a single feature.
- Do NOT aggregate dimensions into a single score. A system that scores well on 6 and poorly on 1 has a SPECIFIC, actionable problem.
- Do NOT treat coherence findings as task blockers — finish the current task, THEN address coherence.
- Do NOT fix all findings at once — prioritize by leverage level (structural > behavioral > cosmetic).
- Do NOT assess coherence from code alone when the deliverable has a UI — read the rendered output, not just the source.
- Do NOT flag intentional inconsistencies. If a feature deliberately deviates from patterns with documented justification, that's not a coherence issue.
