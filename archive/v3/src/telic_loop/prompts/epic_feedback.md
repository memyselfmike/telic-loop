# Epic Feedback Checkpoint — Generating the Human Review Summary

An epic has been completed and passed its exit gate. Your job is to generate a curated summary for the human at the right level of abstraction — not raw logs, not code diffs, but a clear picture of what was delivered and how it maps to the vision.

## Context

- **Sprint**: {SPRINT}
- **Sprint Directory**: {SPRINT_DIR}
- **Vision**: {SPRINT_DIR}/VISION.md
- **Completed Epic**: {EPIC_TITLE} (Epic {EPIC_NUMBER} of {EPIC_TOTAL})
- **Epic Value Statement**: {EPIC_VALUE_STATEMENT}
- **Epic Completion Criteria**: {EPIC_COMPLETION_CRITERIA}

## The Core Principle

> **"The human confirms alignment, not directs strategy. Show them what was delivered and let them decide if it's on track."**

This is NOT a status report. It's NOT a request for instructions. It's a confirmation gate: "Here's what was delivered. If this is on track, we'll proceed to the next value block."

## Three Levels of Situation Awareness

Structure the summary around what the human needs to understand at each level:

### Level 1: Perception — What was delivered?
- List the concrete deliverables from this epic
- Show what the user can now do that they couldn't before
- Reference specific files, endpoints, or UI screens if applicable

### Level 2: Comprehension — How does it map to the vision?
- Explain how this epic advances the overall vision
- Show which vision deliverables are now complete, partially complete, or upcoming
- Highlight any adjustments made during execution (descoped items, course corrections) and why

### Level 3: Projection — What comes next?
- Preview the next epic's value statement and key deliverables
- Note any risks or open questions for the next epic
- State the loop's confidence in alignment with the vision (HIGH / MEDIUM / LOW with brief rationale)

## VRC Integration

Include the most recent VRC snapshot:
- **Value Score**: {VRC_VALUE_SCORE}
- **Deliverables Verified**: {VRC_VERIFIED} / {VRC_TOTAL}
- **Gaps**: {VRC_GAPS}

## Output

Report your summary using the `report_epic_summary` tool:

```
{
  "epic_id": "{EPIC_ID}",
  "epic_number": {EPIC_NUMBER},
  "summary": {
    "delivered": ["what was built — concrete, demonstrable outputs"],
    "vision_progress": "how this advances the overall vision",
    "adjustments": ["any scope changes or course corrections made, with rationale"],
    "next_epic": {
      "title": "...",
      "value_statement": "...",
      "key_deliverables": ["...", "..."],
      "risks": ["..."]
    },
    "confidence": "HIGH | MEDIUM | LOW",
    "confidence_rationale": "why"
  },
  "vrc_snapshot": {
    "value_score": 0.0,
    "deliverables_verified": 0,
    "deliverables_total": 0,
    "gaps": []
  }
}
```

## Anti-Patterns

- Do NOT dump execution logs, task lists, or code diffs. The human doesn't need implementation details.
- Do NOT ask open-ended questions like "what should we do next?" — the loop knows what's next.
- Do NOT be vague. "Made good progress" is not a summary. Name specific deliverables.
- Do NOT hide problems. If something was descoped or a course correction happened, say so clearly and explain why.
- Do NOT include technical jargon unless the vision is itself technical. Match the abstraction level of the vision document.
