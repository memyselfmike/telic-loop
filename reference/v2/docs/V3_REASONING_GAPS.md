# V3 Reasoning Gaps — What the Loop Still Can't Think About

**Date**: 2026-02-15
**Context**: Identified during iterative refinement of V3 planning documents (V3_ARCHITECTURE.md, V3_PHASE1-3_PLAN.md)
**Status**: All 4 gaps addressed.

---

## How We Got Here

During the V3 planning process, we ran 10 quality gates (CRAAP, CLARITY, VALIDATE, CONNECT, BREAK, PRUNE, Blockers, VRC, plus repeat passes) and discovered 30+ issues — wrong API syntax, broken kill chains, missing guardrails, scope drift, duplicate logic. Every round of review uncovered things the previous round missed.

The pattern was consistent: each gate validated the plan against a specific concern (consistency, coverage, integration, reality, simplicity), and each one found real issues. But after all gates passed, a harder question surfaced:

> **"What forms of reasoning does the loop still lack?"**

The gates validate what the plan *says*. They don't address what the plan *doesn't think about*. The four gaps below are not missing features — they are missing **modes of reasoning** that prevent the loop from being a true value-delivering algorithm.

---

## The Four Reasoning Gaps

### Gap 1: Vision Validation — "Are we solving the right problem?"

**The gap**: Every gate validates the plan against the Vision. The Vision is treated as infallible. But the Vision itself is never validated against the user's actual problem.

**What the loop does now**:
- PRD Critique asks "is this *feasible*?" (can we build it?)
- VALIDATE asks "does the plan cover all Vision deliverables?" (are we building all of it?)
- VRC asks "does the deliverable match the Vision?" (did we build what was asked?)

**What the loop doesn't do**:
- "Does this Vision actually solve the problem it claims to solve?"
- "Is there a simpler way to achieve the stated outcome?"
- "Are any deliverables low-value distractions from the core outcome?"
- "Does the Vision contain internal contradictions about who the user is or what they need?"

**Why it matters**: A flawed Vision poisons every downstream decision. The loop could pass every gate, deliver every feature, and still fail because it perfectly built the wrong thing. The most expensive failure is delivering something nobody needed.

**Real-world example**: Vision says "build a dashboard with 12 metrics." User's actual problem is "know when something goes wrong." The right solution might be 3 metrics and an alert system — half the work, twice the value. Without Vision validation, the loop builds all 12 metrics and declares success.

**How this was discovered**: By reasoning about what sits *upstream* of the plan. All gates operate plan-level or below. Nothing operates Vision-level. The assumption "the Vision is correct" is the largest unstated assumption in the entire algorithm.

---

### Gap 2: Process Meta-Reasoning — "Is my process working?"

**The gap**: The loop reasons about the *deliverable* (is it correct? does it deliver value?) but never about its own *process* (is my approach effective? am I improving? should I change how I work?).

**What the loop does now**:
- Course Correction asks "why am I stuck on this *task/deliverable*?" and restructures the plan
- VRC tracks value delivery progress over time
- Budget tracking prevents runaway spending

**What the loop doesn't do**:
- "Am I getting diminishing returns? (spending more effort for less improvement)"
- "Are my fix attempts converging or just churning? (same failures recurring)"
- "Is my test generation consistently wrong for this type of feature?"
- "Am I spending 60% of budget on 10% of value?"
- "Should I change *how* I'm working, not just *what* I'm working on?"

**Why it matters**: Without meta-reasoning, the loop can't adapt its process — only its plan. It could spend 40 iterations on a problem that a human would recognize in 2 iterations as "wrong approach, start over." Course correction changes the plan; meta-reasoning would change the strategy.

**Real-world example**: The loop's test generation consistently fails for async API endpoints. After each failure, course correction adds new tasks or restructures. But the root cause is that the test *approach* is wrong (testing async code synchronously). The loop never asks "why do my tests for this category always fail?" — it only asks "what should I do next?"

**How this was discovered**: By distinguishing between reasoning about the deliverable and reasoning about the reasoning process itself. Every existing mechanism (VRC, course correction, critical eval) reasons about the output. Nothing reasons about the loop's own effectiveness patterns.

---

### Gap 3: Human Feedback Integration — "The human is a write-once input device."

**The gap**: The human provides Vision + PRD at the start and handles Interactive Pauses mid-loop. But there's no channel for the human to provide *feedback* on work in progress — to steer, correct, reprioritize, or refine their intent based on what they see being built.

**What the loop does now**:
- Human provides Vision + PRD (input at start)
- Interactive Pause asks human to perform actions (OAuth, API keys, etc.)
- Delivery Report shows final output

**What the loop doesn't do**:
- "I've seen what you've built so far and I want to change direction"
- "That feature looks wrong — here's what I actually meant"
- "Don't bother with feature X anymore, feature Y is more important"
- "This is taking too long, can you ship what you have?"
- "Actually, I realized I need Z instead of Y"

**Why it matters**: Building software is a conversation, not a specification. Humans refine their understanding of what they want by seeing intermediate output. The loop's one-directional communication (input at start, pause instructions mid-loop) means it can never benefit from the human's evolving understanding.

This is especially critical for non-technical users (the V3 Vision's target persona). They often can't fully specify what they want upfront — they know it when they see it. A loop that can't receive "that's not what I meant" feedback will deliver technically correct but practically wrong outcomes.

**Real-world example**: Human asks for "a project management tool." Loop builds a Kanban board. Human sees it and realizes "actually, I needed a Gantt chart — I think in timelines, not columns." Without a feedback channel, the loop delivers a polished Kanban board that the human never uses.

**How this was discovered**: By asking "who talks to whom, and in which direction?" The loop talks *at* humans (pause instructions) but never listens *to* humans (feedback). The communication channel is one-way during execution.

---

### Gap 4: Emergent System Coherence — "The whole is different from the sum of its parts."

**The gap**: Features are validated individually (QC checks each feature, critical eval experiences individual flows), but when multiple features interact, emergent problems appear that no individual check catches.

**What the loop does now**:
- QC verifies individual features work (tests, linting, type checks)
- Critical Eval experiences the deliverable as a user (periodic, every 3 tasks)
- Exit Gate does a fresh-context final verification
- Regression checks that existing features still pass after new changes

**What the loop doesn't do**:
- "Do features A and B create a confusing interaction when used together?"
- "Does the accumulated UI complexity overwhelm the user?"
- "Are there inconsistent patterns across features? (one uses modals, another uses inline)"
- "Does the system's architecture remain coherent as features accumulate?"
- "Is the cognitive load for a new user growing faster than the value?"

**Why it matters**: Regression testing catches broken features. Critical eval catches bad individual experiences. But neither catches emergent problems — the kind that only appear when you step back and look at the whole system. A dashboard with 5 well-built widgets can still be unusable if the widgets don't form a coherent information hierarchy.

This is especially dangerous because each individual task passes QC, passes critical eval, and delivers its stated value. The problem is invisible at the task level and only visible at the system level.

**Real-world example**: Loop builds a chat UI, then an email UI, then a calendar UI. Each passes individually. But the chat uses a sidebar layout, email uses a split-pane layout, and calendar uses a full-page layout. The app feels like three different products stitched together. No individual feature is wrong, but the whole is incoherent.

**How this was discovered**: By asking "what can't be caught by checking parts individually?" Regression is part-level. QC is part-level. Even critical eval, while holistic in intent, runs periodically on recent changes, not on the accumulated system. The exit gate is the closest to holistic, but it runs at the end when architectural decisions are baked in.

---

## Relationship Between the Gaps

These gaps are not independent — they form a reasoning stack:

```
Gap 1: Vision Validation          "Are we solving the RIGHT problem?"
  │
  │  feeds into
  ▼
Gap 3: Human Feedback             "Does the human agree with our direction?"
  │
  │  feeds into
  ▼
Gap 4: Emergent Coherence         "Does the whole SYSTEM work, not just the parts?"
  │
  │  feeds into
  ▼
Gap 2: Process Meta-Reasoning     "Is our PROCESS effective at delivering value?"
```

- **Vision Validation** is upstream — if the Vision is wrong, everything downstream is wasted
- **Human Feedback** closes the loop between delivered output and human intent
- **Emergent Coherence** catches system-level issues that part-level checks miss
- **Process Meta-Reasoning** is the highest-order reasoning — reasoning about the loop's own effectiveness

---

## Impact Assessment

| Gap | Impact if Unaddressed | Difficulty to Address | Current Partial Coverage |
|-----|----------------------|----------------------|--------------------------|
| 1. Vision Validation | Highest — can invalidate entire sprint | Moderate — can be a pre-loop gate | PRD Critique (feasibility only, not value) |
| 2. Process Meta-Reasoning | High — wastes budget on ineffective approaches | High — requires tracking process metrics over time | Course Correction (plan-level only), budget tracking (crude) |
| 3. Human Feedback | High — delivers wrong thing despite technical success | Moderate — needs a feedback protocol, not just a gate | Interactive Pause (action requests only, not feedback) |
| 4. Emergent Coherence | Moderate-High — death by a thousand cuts | Moderate — can extend critical eval or add system-level check | Critical Eval (periodic, task-scoped), Exit Gate (end-only) |

---

## Addressing the Gaps

Each gap needs a different mechanism — not all are quality gates:

| Gap | Mechanism Type | When It Runs |
|-----|---------------|--------------|
| 1. Vision Validation | Pre-loop gate (before plan generation) | Once, at start — challenge the Vision before committing |
| 2. Process Meta-Reasoning | Continuous monitor (inside value loop) | Every N iterations — analyze process metrics and adapt strategy |
| 3. Human Feedback | Protocol extension (new interaction mode) | On-demand — human can inject feedback at any iteration |
| 4. Emergent Coherence | Periodic evaluation (inside value loop) | After major milestones — holistic system review, not just feature review |

---

## Progress

### Gap 1: Vision Validation — ADDRESSED
- **Prompt**: `loop-v2/prompts/vision_validate.md` (5-pass: Extraction, Force Analysis, Causal Audit, Pre-Mortem, Synthesis)
- **Plan integration**: `refine_vision()` — pre-loop step 2, interactive refinement loop before context discovery
- **Research**: `docs/research/vision-validation-synthesis.md` (6 frameworks: OKR, JTBD, Theory of Change, Assumption Mapping, Pre-Mortem, AI Alignment)
- **Validation run**: Ran on V3_VISION.md → NEEDS_REVISION → 6 revisions applied → re-run → PASS
- **Key design update**: Changed from pass/fail gate to interactive collaborative refinement. Issues classified HARD (must resolve) vs SOFT (can acknowledge). Loop researches alternatives for HARD issues, negotiates with human until consensus. Never exits silently.

### Gap 2: Process Meta-Reasoning — ADDRESSED
- **Prompt**: `loop-v2/prompts/process_monitor.md` (Strategy Reasoner — invoked on RED triggers only)
- **Plan integration**: §11.2 Process Monitor (3 layers: metric collectors, trigger evaluation, strategy reasoner)
- **Research**: `docs/research/process-meta-reasoning-synthesis.md` (Reflexion, LATS, Self-Refine, CRITIC, SPC/CUSUM, Multi-Armed Bandits)
- **Architecture**: Layered design — Layers 0-1 are free (arithmetic every iteration), Layer 2 is Opus (2-4 per sprint, ~$3-6, <5% overhead)
- **Key distinction**: Course Correction changes the PLAN (what to work on). Process Monitor changes the STRATEGY (how to work).

### Gap 3: Human Feedback Integration — ADDRESSED
- **Research synthesis**: `docs/research/human-feedback-integration-synthesis.md` (6 frameworks: Active Learning, Agile Epics, HTN, VOI, Shared Mental Models, Stage-Gate)
- **Prompts**: `loop-v2/prompts/epic_decompose.md` (vision → value blocks), `loop-v2/prompts/epic_feedback.md` (curated between-epic summary)
- **Plan integration**: V3_PHASE3_PLAN.md §5 (classify → decompose → feedback checkpoint → epic loop)
- **Architecture**: Two-tier loop for multi_epic visions. Inner value loop autonomous. Outer epic loop with feedback gates.
- **Key design**: Feedback granularity scales with vision complexity. Simple visions skip entirely. Between-epic gate is optional with configurable timeout auto-proceed. Human confirms alignment ("on track?"), doesn't direct strategy.
- **7 convergence points** from 6 independent frameworks: (1) Not all decisions warrant human input, (2) Value = uncertainty × consequence × irreversibility, (3) Autonomous execution without sync causes drift, (4) Feedback at natural value boundaries, (5) Bidirectional checkpoint updates, (6) Just-in-time decomposition, (7) Checkpoint cost must be managed.

### Gap 4: Emergent System Coherence — ADDRESSED
- **Research synthesis**: `docs/research/emergent-system-coherence-synthesis.md` (6 frameworks: Systems Thinking, ATAM/Fitness Functions, Gestalt/UX, Combinatorial Testing, Architectural Smells, Ecological Assessment)
- **Prompt**: `loop-v2/prompts/coherence_eval.md` (7-dimension system evaluation)
- **Plan integration**: Phase 2 adds Quick Coherence (Dim 1-2, automated). Phase 3 adds Full Coherence (all 7 dimensions, Opus).
- **7 evaluation dimensions**: Structural Integrity, Interaction Coherence, Conceptual Integrity, Behavioral Consistency, Informational Flow, Resilience, Evolutionary Capacity.
- **Key design**: Quick mode (automated, no LLM, every N tasks) catches structural issues. Full mode (Opus, at epic/exit boundaries) catches semantic issues. CRITICAL findings trigger Course Correction. Multi-dimensional — never a single score.
- **7 convergence points** from 6 independent frameworks: (1) Whole ≠ sum of parts, (2) Interactions are where problems hide, (3) Drift is silent and cumulative, (4) Structure determines behavior, (5) Both static + dynamic analysis needed, (6) Health requires multiple indicators, (7) Assessment must be continuous.

---

## Appendix: How Each Gap Maps to Existing Gate Coverage

To confirm these are genuine gaps and not duplicates of existing gates:

| Existing Gate | What It Checks | Gap 1 | Gap 2 | Gap 3 | Gap 4 |
|---------------|---------------|-------|-------|-------|-------|
| CRAAP | Plan internal consistency | -- | -- | -- | -- |
| CLARITY | Plan ambiguity | -- | -- | -- | -- |
| VALIDATE | Requirements coverage | -- | -- | -- | -- |
| CONNECT | Component integration | -- | -- | -- | -- |
| BREAK | Plan vs reality | -- | -- | -- | -- |
| PRUNE | Plan simplicity | -- | -- | -- | -- |
| VRC | Value delivery | -- | -- | -- | Partial |
| Critical Eval | User experience | -- | -- | -- | Partial |
| Course Correct | Plan restructuring | -- | Partial | -- | -- |
| Interactive Pause | Human actions | -- | -- | Partial | -- |
| **Vision Validation** | **Vision quality** | **FULL** | -- | -- | -- |
| **Process Monitor** | **Execution strategy** | -- | **FULL** | -- | -- |
| **Epic Feedback** | **Human alignment** | -- | -- | **FULL** | -- |
| **Coherence Eval** | **System-level health** | -- | -- | -- | **FULL** |

All four gaps are now addressed by dedicated mechanisms.
