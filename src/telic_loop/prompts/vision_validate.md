# Vision Validation — Is This the Right Thing to Build?

Challenge the Vision before committing to execution. Validate that it solves a real problem, has sound causal logic, and addresses its most likely failure modes.

## Context

- **Sprint**: {SPRINT}
- **Sprint Directory**: {SPRINT_DIR}
- **Vision**: {SPRINT_DIR}/VISION.md

## The Core Principle

> **"A flawed Vision, perfectly executed, delivers the wrong outcome."**

Every downstream gate validates the plan against the Vision. None validates the Vision itself. This gate does. It asks not "can we build this?" (feasibility — the PRD critique handles that) but "should we build this?" and "will building this actually deliver the promised value?"

The Vision is a set of hypotheses, not facts. This gate makes those hypotheses explicit, tests their logic, and identifies which ones could kill the entire effort if they're wrong.

## The Five Passes

Vision Validation uses five sequential passes, each applying a different cognitive mode. Single-pass validation goes shallow. These passes build on each other — each consumes the structured output of the previous.

---

### Pass 1: Extraction (Comprehension)

**Mode**: Faithful reading — no judgment yet. Understand what the Vision actually claims.

**Instructions**: Read the Vision document carefully and extract a structured model of its claims. Do not evaluate — just map what it says.

**Extract:**

1. **Goals** — Every stated goal or deliverable. Classify each:
   - **Outcome**: Describes a change in the world ("users can accomplish X faster")
   - **Activity**: Describes what will be built/done ("build a dashboard with 12 metrics")

2. **Causal chain** — The implied logic: "If we build X → then users will Y → resulting in Z." Extract every link as an explicit If→Then statement. Note where the chain has gaps (jumps from activity to impact with no intermediate step).

3. **Success metrics** — How the Vision defines success. Classify each:
   - **Direct**: Measures the actual intended outcome
   - **Proxy**: Measures something correlated with the outcome (but could diverge)

4. **Target user** — Who is described? What is their current state? What is their desired state?

5. **Stated assumptions** — Any explicit "we assume..." or "this requires..." statements. (Most Visions have few or none — the important assumptions are implicit.)

**Output structure:**
```
PASS 1: EXTRACTION
==================
GOALS:
  - [goal text] → TYPE: outcome | activity

CAUSAL_CHAIN:
  - IF [action] THEN [result] MECHANISM: [why] | MISSING
  - IF [result] THEN [next result] MECHANISM: [why] | MISSING

METRICS:
  - [metric] → TYPE: direct | proxy → PROXY_FOR: [what it stands in for]

TARGET_USER:
  - Who: [description]
  - Current state: [what they do now]
  - Desired state: [what they want to do]

STATED_ASSUMPTIONS: [list, or "none explicitly stated"]

CHAIN_GAPS: [where the causal chain jumps with no mechanism]
```

---

### Pass 2: Force Analysis (Adversarial Empathy)

**Mode**: Think like the target user. Model the forces for and against adoption.

**Consumes**: Pass 1 output (goals, target user, causal chain)

**Instructions**: For each major goal/deliverable, analyze the four forces that determine whether the target user would actually adopt and benefit from this:

1. **Push** (pain with status quo) — What specific frustration or limitation drives users away from their current approach? Not vague ("users want better X") but concrete ("users currently spend 3 hours on Y because Z"). If the push is weak or imaginary, there may be no real demand.

2. **Pull** (magnetism of new solution) — What specifically attracts users to this solution over alternatives? Must be specific to this product, not generic ("AI-powered" is not a pull; "answers your question from your own documents in 3 seconds" is).

3. **Anxiety** (fear of switching) — What would make users hesitate? Data migration, learning curve, reliability concerns, privacy, cost, integration pain. If the Vision never mentions anxiety, it hasn't modeled real user psychology.

4. **Habit** (inertia of current behavior) — What are users doing today and why do they keep doing it? Not just "they use spreadsheets" but "they use spreadsheets because everyone already knows Excel and the files are portable."

**Force balance assessment**: Push + Pull must exceed Anxiety + Habit for adoption. If not, the Vision will fail regardless of execution quality.

Then surface hidden assumptions:

5. **Assumption extraction** — For each claim in the Vision, rephrase as "We believe that..." and assess: is there evidence, or is this an assumption?

6. **Categorize** each assumption:
   - **Desirability**: Do users actually want this?
   - **Feasibility**: Can we actually build this?
   - **Viability**: Does this make business/practical sense?
   - **Usability**: Can users actually use this?

7. **Kill-shot identification** — Find assumptions that are simultaneously *critical to success* AND *lacking evidence*. These are the ones that could kill the entire effort.

**Output structure:**
```
PASS 2: FORCE ANALYSIS
======================
FORCES:
  [Goal/Deliverable]:
    PUSH: [specific pain] | STRENGTH: strong | moderate | weak | missing
    PULL: [specific attraction] | STRENGTH: strong | moderate | weak | missing
    ANXIETY: [specific fears] | STRENGTH: strong | moderate | weak | missing
    HABIT: [specific inertia] | STRENGTH: strong | moderate | weak | missing
    NET ASSESSMENT: adoption likely | uncertain | unlikely

HIDDEN_ASSUMPTIONS:
  - "We believe that [claim]" → CATEGORY: desirability | feasibility | viability | usability
    IMPORTANCE: high | medium | low
    EVIDENCE: strong | some | none
    KILL_SHOT: yes | no

KILL_SHOTS: [list of high-importance, low-evidence assumptions]
```

---

### Pass 3: Causal Audit (Logical Rigor)

**Mode**: Strict logical analysis. Test every causal link for validity.

**Consumes**: Pass 1 output (causal chain, metrics) and Pass 2 output (assumptions)

**Instructions**: Examine every If→Then link from Pass 1 and every metric. Apply three tests:

**For each causal link:**

1. **Mechanism test** — Is there a "because" explaining *why* this link holds? "If we add search, users will find documents faster" — why? What if search results are poor? Every link needs a mechanism, not just an assertion.

2. **Reversibility test** — Could the "Then" happen without the "If"? Could the "If" happen without the "Then"? If yes to either, the link is weaker than claimed.

3. **Assumption dependency** — Which assumptions from Pass 2 does this link depend on? If a kill-shot assumption underlies a critical link, that link is fragile.

**For each metric (Goodhart audit):**

4. **Proxy detection** — Is this the actual thing we care about, or a stand-in? Ask: "How could this metric improve while the actual user outcome gets worse?"

5. **Gaming scenarios** — How could an agent or team technically achieve this metric while completely failing to deliver value? If it's easy to imagine, the metric is gameable.

6. **Extremal test** — What happens if you maximize this metric to its extreme? Does it still serve users? ("Maximize engagement" taken to extreme = addictive dark patterns.)

**For activity-typed goals from Pass 1:**

7. **Orphan detection** — Can this activity be traced to a specific outcome? If not, it's an orphan activity — work without a clear "why."

**Output structure:**
```
PASS 3: CAUSAL AUDIT
====================
CHAIN_LINKS:
  - IF [X] THEN [Y]
    MECHANISM: [present | weak | missing]
    REVERSIBLE: [could Y happen without X?]
    DEPENDS_ON: [assumption IDs from Pass 2]
    STRENGTH: strong | moderate | weak | broken

METRIC_AUDIT:
  - [metric]
    PROXY_FOR: [real goal] | DIRECT
    GAMING_SCENARIO: [how it could be gamed]
    EXTREMAL_RISK: [what happens at extreme]

ORPHAN_ACTIVITIES: [activities with no traceable outcome]

LEAPS_OF_FAITH: [links where mechanism is missing AND dependent on kill-shot assumptions]
```

---

### Pass 4: Pre-Mortem (Imaginative Pessimism)

**Mode**: Prospective hindsight. Assume failure has already happened and work backwards.

**Consumes**: All previous passes (especially kill-shots from Pass 2 and leaps of faith from Pass 3)

**Instructions**:

State the premise: **"It is 18 months later. This effort has failed. The deliverable exists but was abandoned/unused/rolled back. Why?"**

Research shows imagining an event has *already occurred* increases failure identification by 30% compared to asking "what could go wrong?" This is because it bypasses optimism bias and triggers analytical thinking.

Generate failure scenarios across these categories:

1. **Market / Demand failures** — Nobody wanted it. The problem wasn't painful enough. A free alternative appeared. The target user doesn't actually exist in sufficient numbers.

2. **Solution fit failures** — The solution doesn't actually solve the stated problem. Users tried it but it didn't help them accomplish their real goal. The solution addresses a symptom, not the root cause.

3. **Execution / Technical failures** — Couldn't build it in time. Key technology didn't work at scale. Critical dependency failed. Quality was too low to be usable.

4. **Adoption / Retention failures** — Users tried it but didn't stick. Onboarding was too complex. Integration with existing workflows failed. Switching costs were higher than expected.

5. **Timing / Competitive failures** — Too early (users not ready). Too late (already commoditized). A competitor launched something better during development.

6. **External failures** — Regulatory change blocked it. Platform dependency broke. Economic conditions changed the value equation.

For each scenario:
- Assess **plausibility** (likely / possible / unlikely)
- Check whether the **Vision addresses it**
- Cross-reference with **kill-shot assumptions** (Pass 2) and **leaps of faith** (Pass 3)
- Identify **compounding risks** — failure modes that link to multiple fragile assumptions

**Output structure:**
```
PASS 4: PRE-MORTEM
==================
FAILURE_MODES:
  - [scenario]
    CATEGORY: market | solution_fit | execution | adoption | timing | external
    PLAUSIBILITY: likely | possible | unlikely
    ADDRESSED_IN_VISION: yes | partially | no
    LINKED_KILL_SHOTS: [assumption IDs]
    LINKED_LEAPS: [chain link IDs]

COMPOUNDING_RISKS: [failure modes that connect to multiple fragile points]

TOP_3_MOST_LIKELY_FAILURES: [ranked by plausibility, not severity]
```

---

### Pass 5: Synthesis (Balanced Judgment)

**Mode**: Balanced assessment. Weigh evidence from all passes. Be honest but fair.

**Consumes**: All four previous pass outputs

**Instructions**: Aggregate findings into a final assessment. Score the Vision on four dimensions:

1. **Outcome-Grounded** — Does the Vision describe outcomes (changes in the world) or just activities (things to build)? Based on Pass 1 goal classification and Pass 3 orphan detection.

2. **Adoption-Realistic** — Has the Vision modeled the full force balance (push, pull, anxiety, habit)? Is adoption likely given the forces? Based on Pass 2 force analysis.

3. **Causally-Sound** — Are the causal chains intact with valid mechanisms, or full of leaps of faith? Based on Pass 3 causal audit.

4. **Failure-Aware** — Does the Vision acknowledge and address its most likely failure modes? Based on Pass 4 pre-mortem.

**Scoring:**
- Each dimension: STRONG / ADEQUATE / WEAK / CRITICAL
- Overall: PASS / NEEDS_REVISION

**Then produce:**

5. **Strengths** — What the Vision does well. Be specific. This is required — the brief must acknowledge what's strong, not just what's wrong.

6. **Issues** — Every problem found, each classified as HARD or SOFT (see Issue Classification below). Each must reference specific evidence from previous passes and include a suggested revision.

7. **Kill criteria** — What evidence, discovered during execution, should cause the loop to stop and re-evaluate the Vision?

**Report via the `report_vision_validation` structured tool.** Do NOT use the text output structure — use the tool call with the JSON schema defined below.

---

## Issue Classification

Every issue found in Passes 1-5 must be classified by severity:

### HARD Issues (must be resolved — loop will not proceed)

Issues that make the Vision **impossible or internally contradictory**. No amount of good execution can overcome these:

- **impossible**: Requires technology that doesn't exist or can't work as described
- **contradictory**: Vision statements conflict with each other
- **no_problem**: No identifiable real user problem (solution looking for a problem)
- **all_activity**: Every goal is an activity, none are outcomes — there's nothing to validate success against
- **no_mechanism**: Causal chain has 3+ leaps of faith with zero mechanisms — the Vision is magical thinking

HARD issues require the human to revise the Vision. The loop will research alternatives and propose them, but cannot proceed until the issue is resolved.

### SOFT Issues (advisory — human can acknowledge and accept risk)

Issues that make the Vision **risky or weak**, but not impossible:

- **weak_evidence**: Causal chain has gaps but isn't impossible
- **adoption_risk**: Anxiety + habit exceed push + pull — adoption is uncertain
- **gameable_metric**: Success metrics could be gamed or don't measure the real outcome
- **unaddressed_failure**: A plausible failure mode the Vision doesn't acknowledge
- **missing_mechanism**: A causal link lacks a "because" but the link is plausible

SOFT issues are presented with clear recommendations. The human can acknowledge the risk and proceed, or revise to strengthen the Vision.

## Verdicts

| Verdict | Meaning | What Happens Next |
|---------|---------|-------------------|
| **PASS** | No HARD issues. All dimensions STRONG or ADEQUATE. | Proceed to Context Discovery |
| **NEEDS_REVISION** | HARD or SOFT issues found. | Issues presented to human. HARD issues include researched alternatives. Human revises Vision and loop re-analyzes until consensus. |

> **This is a collaborative refinement process, not a pass/fail gate.** The human is present at launch time. If the Vision has problems, the loop works WITH the human to fix them — researching alternatives, proposing revisions, iterating until both the loop's analysis and the human's intent are aligned.
>
> The loop is **advisory but forceful**: it cannot be overridden on HARD issues (impossible/contradictory). It advises strongly on SOFT issues but the human can accept the risk. The goal is **consensus**, not permission.

## Output Structure

Pass 5 must produce this structured output via the `report_vision_validation` tool:

```
{
  "verdict": "PASS | NEEDS_REVISION",
  "dimensions": {
    "outcome_grounded": "STRONG | ADEQUATE | WEAK | CRITICAL",
    "adoption_realistic": "STRONG | ADEQUATE | WEAK | CRITICAL",
    "causally_sound": "STRONG | ADEQUATE | WEAK | CRITICAL",
    "failure_aware": "STRONG | ADEQUATE | WEAK | CRITICAL"
  },
  "strengths": ["what the Vision does well — be specific"],
  "issues": [
    {
      "id": "issue_1",
      "severity": "hard | soft",
      "category": "impossible | contradictory | no_problem | all_activity | no_mechanism | weak_evidence | adoption_risk | gameable_metric | unaddressed_failure | missing_mechanism",
      "description": "clear description of the issue",
      "evidence": "which passes found this and what the evidence is",
      "suggested_revision": "specific, actionable change to the Vision"
    }
  ],
  "kill_criteria": ["observable evidence during execution that should trigger re-evaluation"],
  "reason": "brief summary of overall assessment"
}
```

## Anti-Patterns

- Do NOT rubber-stamp the Vision — validation requires willingness to find problems
- Do NOT confuse "I disagree with the approach" with "the Vision is flawed" — challenge the logic, not the preferences
- Do NOT require perfection — every Vision has assumptions and risks; the question is whether they're acknowledged and manageable
- Do NOT generate only negative findings — acknowledge what the Vision does well (strengths are required output)
- Do NOT pattern-match to similar products — analyze the specific causal claims in THIS Vision
- Do NOT evaluate feasibility here — that's the PRD Critique's job. Focus on whether the right thing is being built, not whether it can be built
- Do NOT be vague about severity — every issue must be explicitly classified as HARD or SOFT with a specific category
- Do NOT classify something as HARD unless it is genuinely impossible or contradictory — "risky" and "uncertain" are SOFT
