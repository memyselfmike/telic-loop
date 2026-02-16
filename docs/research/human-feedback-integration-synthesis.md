# Human Feedback Integration — Cross-Domain Research Synthesis

**Date**: 2026-02-15
**Context**: Addressing Reasoning Gap 3 from V3_REASONING_GAPS.md
**Purpose**: Synthesize independent research into an operational mechanism for human feedback during autonomous loop execution

---

## The Problem

The loop treats the human as a write-once input device. Vision + PRD go in at the start, the loop runs autonomously, and a delivery report comes out at the end. The only mid-loop human interaction is Interactive Pause — a tactical mechanism where the loop tells the human to perform a specific action (set up OAuth, create an API key) and verifies completion.

There is no channel for the human to say:
- "That feature looks wrong — here's what I actually meant"
- "Don't bother with feature X anymore, feature Y is more important"
- "This is taking too long, ship what you have"
- "Actually, I realized I need Z instead of Y"

### The Key Insight (from the project owner)

**Feedback granularity should scale with vision complexity.** A simple feature (add a logout button) needs nothing beyond the initial vision. A complex multi-phase system needs the vision decomposed into **epics** — deliverable blocks of value — with human feedback checkpoints between epics. The human confirms alignment ("this is on track, deliver the next value block") rather than directing strategy. And the checkpoint is **optional with a timeout**: if the human doesn't respond within a configured window, the loop assumes "looks good" and proceeds.

---

## Six Frameworks Surveyed

### Framework 1: Active Learning / Human-in-the-Loop ML

**Domain**: Machine Learning, Statistical Learning Theory

**Core model**: Active learning algorithms decide WHEN to query a human oracle for labels, rather than querying on every example. The goal is to maximize learning per query — ask only when the expected information gain justifies the interruption cost.

**Key findings**:
- **Uncertainty sampling**: Query the human when the model is most uncertain about the correct answer. High uncertainty = high value of human input. Low uncertainty = proceed autonomously.
- **Query by committee**: Multiple models vote; query the human when models disagree most. Disagreement is a reliable signal that human judgment would be informative.
- **Expected model change**: Query when the human's answer would cause the largest update to the model's beliefs. This directly measures the value of the feedback.
- **Information density weighting**: Weight queries by how representative the example is. Querying about an edge case teaches less than querying about a common pattern.
- **Hybrid strategies**: The best approaches combine uncertainty with diversity — don't just query about the single most uncertain example; query about uncertain examples that are also diverse (covering different parts of the problem space).

**Operationalizable techniques**:
- Trigger human feedback when the loop's confidence in its direction drops below a threshold
- Weight feedback requests by how representative the current epic is of the overall vision
- Don't ask about edge cases (tactical issues) — ask about common patterns (strategic alignment)
- Combine confidence signals: uncertainty in the plan × consequence of the decision × irreversibility

**Limitations**: Active learning assumes the oracle (human) is always correct. In practice, humans have biases, fatigue, and incomplete information. The framework doesn't model oracle quality.

---

### Framework 2: Agile Epic Decomposition & Sprint Review

**Domain**: Software Project Management, Agile Methods

**Core model**: Large initiatives are decomposed into epics — independently valuable chunks of work. Each epic delivers a coherent block of value that can be evaluated on its own. Sprint reviews at epic boundaries function as feedback loops where stakeholders inspect the increment and adapt the backlog.

**Key findings**:
- **Split by user value, not by technical layer**: Good epics are horizontal slices (user can do X end-to-end) not vertical slices (database layer done, then API layer, then UI layer). Each epic should be independently demonstrable.
- **INVEST criteria for epics**: Independent, Negotiable, Valuable, Estimable, Small enough to deliver, Testable. The "Valuable" and "Independent" criteria are most important for feedback: the human can only give meaningful feedback on something that delivers observable value.
- **Just-in-time decomposition**: Don't decompose the entire vision into epics upfront. Decompose the next 1-2 epics in detail, keep the rest at high level. Later epics will be shaped by what's learned from earlier ones.
- **SAFe Program Increments**: Large-scale agile uses "Program Increments" — time-boxed periods where multiple teams deliver an integrated increment. The PI boundary is the natural feedback point. The "Inspect & Adapt" ceremony at PI end is explicitly a system-level feedback loop.
- **Confidence vote at boundaries**: At SAFe PI planning, teams vote on their confidence (1-5 fingers). If average confidence < 3, the plan is reworked. This is a structured, low-cost way to check alignment.

**Operationalizable techniques**:
- Decompose complex visions into epics using horizontal (value) slicing, not vertical (layer) slicing
- Each epic must be independently demonstrable — the human can see and evaluate a working increment
- Decompose only the next 1-2 epics in detail; keep later epics as high-level placeholders
- At epic boundaries, present a structured summary of what was delivered + a confidence assessment

**Limitations**: Agile decomposition assumes a human product owner who actively participates. It doesn't address what happens when the human is unavailable or provides late feedback.

---

### Framework 3: Hierarchical Task Networks / Hierarchical Planning

**Domain**: AI Planning, Hierarchical Reinforcement Learning

**Core model**: Complex plans are organized in hierarchies where strategic decisions happen at the top level and tactical decisions happen at lower levels. Higher levels set goals and constraints; lower levels choose specific actions to achieve them. The Options Framework in hierarchical RL provides a formal model: an "option" is a temporally extended action with an initiation set, a policy, and a termination condition.

**Key findings**:
- **Decomposition methods encode domain knowledge**: The way a task is decomposed reflects understanding of the problem. Bad decompositions lead to inefficient or impossible execution. The decomposition itself is a strategic decision.
- **Interleaved planning and execution**: HTN planners don't plan everything upfront. They plan at the current level, begin executing, and plan the next level when needed. This matches the just-in-time decomposition principle from Agile.
- **Hierarchical abstraction reduces complexity**: By reasoning about epics (not tasks), the human operates at the right abstraction level. They don't need to understand individual code changes — they evaluate delivered value.
- **Options Framework termination conditions**: Each "option" (epic) has explicit termination conditions — criteria that determine when this option is complete and the system should return to the higher level for the next decision. This prevents both premature termination and infinite loops.
- **Semi-Markov property**: Decisions at the epic level only need to consider the current state (what was delivered, what's the vision), not the full history of how we got here. This simplifies the human's cognitive load at checkpoints.

**Operationalizable techniques**:
- The epic level is where human feedback operates; the task level is fully autonomous
- Each epic has explicit completion criteria (termination conditions) defined during decomposition
- When an epic completes, the system returns to the "epic level" for the next decision
- The human only needs to evaluate the current delivered state against the vision — not review the execution history

**Limitations**: HTN assumes the hierarchy is well-defined. In practice, the right level of decomposition for human feedback is itself a judgment call that requires domain knowledge.

---

### Framework 4: Value of Information (VOI) Theory

**Domain**: Decision Theory, Bayesian Decision Analysis

**Core model**: The Value of Information quantifies whether gathering more information (asking the human) is worth the cost (delay, interruption, cognitive load). EVPI (Expected Value of Perfect Information) is the maximum you should pay for any information. EVSI (Expected Value of Sample Information) is the value of imperfect, partial information — which is what human feedback actually is.

**Key findings**:
- **EVPI is never negative but net value can be**: Getting more information never hurts the decision itself, but the COST of getting it (delay, interruption) can exceed the benefit. Net VOI = information value − acquisition cost.
- **VOI is highest when**: (a) Uncertainty about the right path is high, (b) the consequences of the decision are large, (c) the decision is irreversible or expensive to reverse. When all three are low, feedback has near-zero value.
- **Partial information (EVPPI/EVSI) is usually sufficient**: You don't need perfect feedback from the human. A quick "looks right" or "something's off" provides enough signal to continue or investigate. Structured, simple feedback protocols outperform open-ended requests.
- **ENBS (Expected Net Benefit of Sampling)**: The formal formula: ENBS = EVSI − cost_of_sampling. Only seek feedback when ENBS > 0. This provides a principled answer to "should we ask?"
- **Diminishing returns**: The value of the Nth piece of feedback is less than the (N-1)th. Don't over-query. After initial alignment is confirmed, subsequent confirmations add less value.

**Operationalizable techniques**:
- Compute a "feedback value score" based on: uncertainty × consequence × irreversibility
- Small, simple visions → low score → skip feedback (autonomous)
- Complex, multi-epic visions → high score → checkpoint between epics
- Use simple, structured feedback (not open-ended) to minimize acquisition cost
- Decrease checkpoint frequency as confidence builds (diminishing returns)

**Limitations**: VOI assumes you can estimate uncertainty and consequences in advance. In practice, you may not know what you don't know — the most valuable feedback is often about things you didn't anticipate.

---

### Framework 5: Shared Mental Models / Team Cognition

**Domain**: Cognitive Psychology, Human-AI Teaming, Organizational Science

**Core model**: Effective teams (human-human or human-AI) maintain shared mental models — aligned understanding of goals, strategies, roles, and situation. When mental models diverge, coordination breaks down. Regular synchronization checkpoints prevent dangerous levels of drift.

**Key findings**:
- **Alignment drift is the central risk**: Without checkpoints, the human's understanding of what's being built and the loop's understanding of what the human wants diverge over time. Small misunderstandings compound. This is especially dangerous because both sides believe they're aligned.
- **Situation awareness has three levels**: Level 1 — perception (what is the current state?), Level 2 — comprehension (what does it mean?), Level 3 — projection (what will happen next?). Effective feedback checkpoints must address all three: show the human what was built (L1), explain what it means for their vision (L2), and preview what comes next (L3).
- **Transparency is necessary but not sufficient**: Showing the human everything (full logs, all code changes) doesn't create alignment — it creates information overload. Effective transparency is curated: show the RIGHT things at the RIGHT level of abstraction.
- **Bidirectional alignment**: The checkpoint should update both sides. The human updates their mental model of what the loop built. The loop updates its understanding of what the human expects (through the human's response or silence).
- **Trust calibration**: Over-trust (human assumes everything is fine and never checks) and under-trust (human micro-manages every decision) are both harmful. The checkpoint mechanism should be designed to calibrate appropriate trust — give the human just enough visibility to assess alignment without pulling them into execution details.

**Operationalizable techniques**:
- Present a curated "epic summary" at checkpoints, not raw logs — right abstraction level
- Structure the summary around: what was delivered (L1), how it maps to the vision (L2), what's planned next (L3)
- Design for bidirectional update: the loop learns from the human's response (or silence)
- Auto-proceed on timeout (with configurable window) to calibrate trust — the human CHOOSES their engagement level
- Decrease checkpoint detail as trust builds (the loop has a track record)

**Limitations**: Shared mental model theory was developed for human teams with rich communication channels. Human-AI "shared understanding" is weaker — the AI doesn't truly understand intent, and the human can't fully inspect the AI's reasoning.

---

### Framework 6: Progressive Disclosure / Stage-Gate / Real Options Theory

**Domain**: UX Design, Project Management, Financial Engineering

**Core model**: Complex commitments are structured as a series of smaller, progressively more committed steps. At each gate, the decision-maker has the option to continue, pivot, or stop — with more information than they had at the previous gate. This limits downside risk while preserving upside potential. Real Options Theory formalizes this: each gate is an "option" whose value increases with uncertainty and time.

**Key findings**:
- **Gates are tough decision meetings, not status updates**: In Cooper's Stage-Gate process, gates are Go/Kill/Hold/Recycle decisions. They should kill bad projects early, not rubber-stamp continuation. But the default should be "Go" for projects that are on track — the gate's value is in catching the off-track cases.
- **Progressive disclosure of detail**: At early gates, the decision is made with limited information (high uncertainty, low cost). At later gates, more information is available but more has been invested. This matches the epic feedback model: early epics have the most strategic uncertainty; later epics are more tactical.
- **Last Responsible Moment**: Defer decisions until they must be made — but no later. Don't ask the human to evaluate Epic 3 when you're still building Epic 1. But DO ask before committing to an irreversible architectural decision.
- **Real options underlie Agile**: Agile's iterative delivery creates real options — each iteration gives the stakeholder the option to continue, pivot, or stop. The value of this option is highest when uncertainty is highest (early in the project).
- **Staged commitment bounds loss**: The maximum loss at any stage is bounded by the investment in that stage. If Epic 1 reveals a fundamental misalignment, the cost is one epic, not the whole project. This is the primary risk management benefit.

**Operationalizable techniques**:
- Frame the between-epic checkpoint as a Go/Stop/Adjust decision (not an open-ended discussion)
- Default is "Go" (auto-proceed on timeout) — the gate catches exceptions, not normal flow
- Early epics get more scrutiny (higher uncertainty); later epics get lighter checkpoints
- Each epic bounds the maximum wasted investment if the human redirects
- Present the checkpoint with clear "what would change if you redirect" information

**Limitations**: Stage-Gate was designed for multi-month product development with significant financial investment. For a coding loop that runs in hours, the overhead of formal gates must be minimal. The framework assumes rational decision-makers with clear criteria; in practice, humans at checkpoints may be indecisive or provide vague feedback.

---

## Seven Convergence Points

These emerge independently from at least 4 of the 6 frameworks:

### 1. Not All Decisions Warrant Human Input
- **Active Learning**: Only query when uncertainty is high
- **VOI**: Only seek feedback when ENBS > 0
- **HTN**: Tactical decisions stay at the task level; only strategic decisions escalate
- **Stage-Gate**: Simple projects need fewer gates

**Design implication**: The loop must classify vision complexity and only activate epic decomposition + feedback for complex, multi-phase visions.

### 2. Feedback Value = Uncertainty × Consequence × Irreversibility
- **Active Learning**: Uncertainty sampling
- **VOI**: EVPI formula components
- **Stage-Gate**: Early gates have highest option value (highest uncertainty)
- **Real Options**: Option value increases with uncertainty and time-to-expiry

**Design implication**: The feedback mechanism should be weighted toward the first 1-2 epics (where strategic uncertainty is highest) and lighter for later epics.

### 3. Autonomous Execution Without Sync Causes Alignment Drift
- **Shared Mental Models**: Drift is silent and compounds
- **Active Learning**: Model accuracy degrades without oracle queries
- **Agile**: Sprint reviews exist precisely because stakeholder alignment erodes without inspection
- **Systems Thinking**: Reinforcing feedback loops amplify small misunderstandings

**Design implication**: Even when the loop is confident, periodic checkpoints prevent invisible drift. But the frequency should decrease as alignment is confirmed.

### 4. Feedback Belongs at Natural Value-Delivery Boundaries
- **Agile**: Sprint/PI boundaries are natural feedback points
- **HTN**: Option termination conditions mark natural hierarchy transitions
- **Stage-Gate**: Gates sit between stages, not within them
- **Progressive Disclosure**: Each disclosure level corresponds to a completed unit of work

**Design implication**: Feedback happens between epics (completed value blocks), never mid-task or mid-epic. The inner value loop is never interrupted.

### 5. Checkpoints Update Shared Understanding Bidirectionally
- **Shared Mental Models**: Both sides need to update their models
- **Agile**: Sprint review adapts BOTH the product AND the backlog
- **Active Learning**: The model updates its beliefs AND informs future queries
- **VOI**: Information reduces uncertainty on both sides

**Design implication**: The checkpoint isn't just "human reviews output." The loop also updates its understanding based on human response (or the informative signal of silence/auto-proceed).

### 6. Just-in-Time Decomposition Beats Upfront Planning
- **Agile**: Decompose only the next 1-2 epics in detail
- **HTN**: Interleaved planning and execution
- **Real Options**: Defer commitment until information improves
- **Stage-Gate**: Later stages are planned at later gates

**Design implication**: The Vision Decomposition step produces detailed plans only for Epic 1, with high-level sketches for subsequent epics. Each epic boundary refines the next epic's plan.

### 7. Checkpoint Cost Must Be Managed
- **VOI**: Net value = information value − acquisition cost
- **Active Learning**: Query budget is finite
- **Stage-Gate**: Gate overhead must be proportional to project size
- **Shared Mental Models**: Over-communication causes fatigue; under-communication causes drift

**Design implication**: The checkpoint must be fast, structured, and optional (timeout auto-proceed). No open-ended discussions. Curated summaries, not raw logs. Configurable engagement level.

---

## Operational Design: Human Feedback Integration

Based on the convergence analysis and the project owner's input, the mechanism has three components:

### Component 1: Vision Complexity Classification

Runs once, during the pre-loop, after Vision Validation.

**Input**: Validated vision document
**Output**: `single_run` or `multi_epic`

Classification criteria:
- **Deliverable count**: >3 independently valuable deliverables → multi_epic
- **Estimated task count**: >15 tasks → multi_epic
- **Dependency depth**: >2 layers of sequential dependencies → multi_epic
- **Technology breadth**: >2 distinct technology domains → multi_epic
- **Integration surface**: Multiple external systems → multi_epic

If ANY criterion triggers, classify as `multi_epic`.

Simple visions (single_run) skip epic decomposition and run the existing single-pass loop unchanged.

### Component 2: Epic Decomposition

Runs once for multi_epic visions, after complexity classification.

**Decomposition rules** (from Agile + HTN convergence):
- Each epic delivers independently demonstrable value (horizontal slicing)
- Each epic has explicit completion criteria (HTN termination conditions)
- Earlier epics are foundational; later epics build on earlier deliverables
- Detail only Epic 1 fully; sketch Epics 2+ at high level (just-in-time)
- Maximum epic count: 5 (if more, the vision is too large and should be split into separate visions)

**Output**: Ordered list of epics, each with:
```python
@dataclass
class Epic:
    epic_id: str
    title: str
    value_statement: str          # "User can X" — independently demonstrable
    deliverables: list[str]       # Specific outputs
    completion_criteria: list[str] # How to verify this epic is done
    depends_on: list[str]         # Previous epic IDs
    detail_level: str             # "full" for epic 1, "sketch" for later
```

### Component 3: Between-Epic Feedback Checkpoint

Runs between epics, after the exit gate for the current epic passes.

**Protocol**:

1. **Generate Epic Summary** (curated, not raw — from Shared Mental Models):
   - What was delivered (perception — Level 1 SA)
   - How it maps to the vision (comprehension — Level 2 SA)
   - What's planned for the next epic (projection — Level 3 SA)
   - Confidence assessment: how aligned does the loop believe execution is with vision?

2. **Present to Human** with three options:
   - **Proceed** — "Looks good, deliver the next value block" (default)
   - **Adjust** — "The direction is right but I want to change priorities/scope for the next epic"
   - **Stop** — "Ship what you have / I need to rethink the vision"

3. **Timeout with auto-proceed**:
   - Human configures timeout in LoopConfig (e.g., `epic_feedback_timeout_minutes: 30`)
   - If no response within timeout → assume "Proceed"
   - Log: "Auto-proceeded after {timeout} minutes — no human feedback received"
   - The loop is NEVER blocked indefinitely by a non-responsive human

4. **Process response**:
   - **Proceed**: Refine next epic's detail level from "sketch" to "full", begin next epic
   - **Adjust**: Human provides adjustment notes → loop incorporates into next epic's plan generation (re-runs plan generation for next epic with adjustment context)
   - **Stop**: Generate final delivery report for completed epics, exit

**Anti-patterns** (what NOT to do):
1. Don't interrupt the inner value loop — feedback only between epics
2. Don't present raw execution logs — curate at the right abstraction level
3. Don't make feedback mandatory — auto-proceed preserves autonomy
4. Don't ask open-ended questions — offer structured choices (Proceed/Adjust/Stop)
5. Don't over-query — if the human auto-proceeds on Epic 1, reduce checkpoint prominence for Epic 2
6. Don't treat human feedback as infallible — the human may be wrong, fatigued, or uninformed. Log feedback but don't blindly override loop judgment without reconciliation.

---

## Integration with Existing V3 Mechanisms

| Mechanism | Purpose | Relationship |
|-----------|---------|--------------|
| Vision Validation (Gap 1) | Challenge the vision before committing | Runs BEFORE complexity classification |
| Interactive Pause | Human performs specific tactical actions | Unchanged — tactical, within inner loop |
| Epic Feedback Checkpoint | Human confirms strategic alignment | NEW — strategic, between epics |
| Process Monitor (Gap 2) | Loop adapts its own strategy | Runs within each epic's value loop |
| Course Correction | Loop restructures its plan | Runs within each epic's value loop |
| Exit Gate | Fresh-context verification | Runs at end of each epic |

**Two-tier architecture for multi_epic visions**:
```
Pre-loop:
  Vision Validation → Complexity Classification → Epic Decomposition

Outer loop (epic level):
  For each epic:
    1. Refine epic detail (sketch → full plan)
    2. Pre-loop gates (discovery, critique, plan gen) scoped to this epic
    3. Inner value loop (autonomous — existing V3 loop)
    4. Exit gate (for this epic)
    5. Epic Feedback Checkpoint (timeout auto-proceed)

Post-loop:
  Final delivery report (across all completed epics)
```

**For single_run visions**: Skip complexity classification output entirely. The existing V3 loop runs unchanged. No epic decomposition, no between-epic checkpoints.

---

## Design Questions Answered

### Q1: When should the loop ask for feedback?
**Between epics only.** Never mid-task, never mid-epic. The inner value loop is sacrosanct.

### Q2: What form should feedback take?
**Structured choice: Proceed / Adjust / Stop.** Not open-ended. Minimal cognitive load. If "Adjust," the human provides brief adjustment notes.

### Q3: How should feedback change the loop's behavior?
**Proceed** = refine next epic, continue. **Adjust** = re-plan next epic with human's context. **Stop** = ship completed epics, exit. Feedback never retroactively changes completed epics.

### Q4: What if the human doesn't respond?
**Auto-proceed after configurable timeout.** The loop's default posture is "keep delivering." Human engagement is optional.

### Q5: How does feedback value scale with complexity?
**Simple visions skip feedback entirely.** Complex visions get between-epic checkpoints. First epic gets most scrutiny (highest uncertainty). Later epics get lighter checkpoints as alignment is confirmed.

### Q6: How does the loop detect alignment drift without human input?
**VRC serves as a continuous automated check.** If VRC detects drift, the loop's confidence drops, making the next epic checkpoint more prominent (longer timeout, more detailed summary). But VRC is within-epic; the human checkpoint is between-epic.

### Q7: How does this interact with the existing Interactive Pause?
**They are independent mechanisms.** Interactive Pause is tactical (within the inner loop, human performs an action). Epic Feedback is strategic (between epics, human confirms alignment). Both can exist in the same run without conflict.
