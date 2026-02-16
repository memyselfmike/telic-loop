# Vision Document Validation: Cross-Framework Synthesis

## Purpose

This document synthesizes six distinct validation frameworks into actionable
techniques that an LLM can apply when reviewing a product Vision document.
The goal: catch flawed thinking *before* a team commits to building.

---

## Part 1: Framework Extractions

### 1.1 OKR Validation: Outcome vs. Activity

**Core insight:** Most vision documents describe *activities* (what we will build/do)
rather than *outcomes* (what changes in the world). Activities are controllable;
outcomes are what actually matter.

**Actionable LLM checks:**

| Check | How to Apply |
|-------|-------------|
| **The "Why" Chain** | For every stated goal, ask "why does this matter?" repeatedly. If the answer is another activity, the goal is not yet an outcome. |
| **The Value Creation Test** | Does this goal describe a change in user/business state, or completion of a task? "Launch feature X" = activity. "Users can accomplish Y 50% faster" = outcome. |
| **The Motivation Test** | Would this goal inspire a team, or merely describe their task list? "Ship 12 integrations" vs. "Any tool a user already owns works seamlessly." |
| **The Measurability Split** | Outputs are binary (done/not done). Outcomes exist on a spectrum and require measurement of *degree*. If every goal is binary, you have activities. |
| **Initiative vs. Key Result Separation** | Valid visions keep the *what changes* (outcomes) separate from the *how we cause it* (initiatives). If these are tangled, the vision conflates means with ends. |

**Red flags in a Vision document:**
- Goals phrased as "Build X", "Launch Y", "Implement Z" (all activities)
- No stated user behavior change or business metric movement
- Success criteria that are entirely within the team's control (no dependency on user adoption)

---

### 1.2 JTBD Four Forces: Push, Pull, Anxiety, Habit

**Core insight:** Users only switch to new solutions when the promoting forces
(Push + Pull) exceed the blocking forces (Anxiety + Habit). A vision that only
describes Pull (how great the new thing is) without addressing the other three
forces has a fatal blind spot.

**The Four Forces applied to Vision review:**

| Force | Question for the Vision | What to look for |
|-------|------------------------|------------------|
| **Push** (pain with status quo) | Does the vision articulate *specific* pain points users currently experience? | Vague "users want better X" vs. concrete "users currently spend 3 hours on Y because Z." If the push is not described, there may not be real demand. |
| **Pull** (magnetism of new solution) | Does the vision describe what draws users *toward* this specific solution? | The pull must be specific to this product, not generic ("AI-powered" is not a pull; "answers your question from your own documents in 3 seconds" is). |
| **Anxiety** (fear of switching) | Does the vision acknowledge what users might fear about adopting this? | Data migration, learning curve, reliability, privacy, cost. If anxiety is never mentioned, the vision has not modeled real user psychology. |
| **Habit** (inertia of current solution) | Does the vision identify what users are currently doing and why they keep doing it? | "They use spreadsheets" is insufficient. "They use spreadsheets because everyone already knows Excel and the files are portable" identifies the real habit barrier. |

**The Decision Formula check:**
> If a vision only addresses Pull and ignores Push, Anxiety, and Habit,
> the product will likely fail to achieve adoption regardless of quality.

**Red flags in a Vision document:**
- Only describes what the product does (Pull), never why users are dissatisfied now (Push)
- No mention of switching costs, learning curves, or integration pain (Anxiety)
- No acknowledgment of what users currently use and why they stay (Habit)
- Assumes users will adopt because the product is "better" without addressing the full force balance

---

### 1.3 Theory of Change: If-Then Causal Chains

**Core insight:** A valid vision contains an implicit causal chain:
"If we build X, then users will do Y, then business outcome Z results."
Each link must be independently defensible. Broken links = broken vision.

**The If-Then Chain Validation:**

```
[Input/Resource] -> [Activity] -> [Output] -> [Short-term Outcome] -> [Long-term Impact]
     IF               THEN          THEN             THEN                   THEN
```

**Actionable LLM checks:**

| Check | How to Apply |
|-------|-------------|
| **Explicit chain extraction** | Read the vision and extract every implied causal link as an "If X, then Y" statement. Are there gaps where the chain jumps from activity to impact with no intermediate mechanism? |
| **Assumption surfacing** | For each "If X, then Y" link, ask: "What must be true for this to hold?" These are the hidden assumptions. |
| **Mechanism identification** | The Theory of Change requires not just *what* happens but *why* it happens. "If we add AI search, users will find documents faster" — why? What mechanism makes this true? What if the AI hallucinates? |
| **Alternative explanation check** | For each causal link, ask: "Could Y happen without X?" and "Could X happen without leading to Y?" If yes to either, the link is weaker than claimed. |
| **Testability check** | Can each link be independently validated with data? If a link is untestable, it is an article of faith, not a plan. |

**Red flags in a Vision document:**
- Jumping from "we build it" to "users love it" with no intermediate steps
- Causal chains that depend on user behavior changes with no explanation of why users would change
- No acknowledgment that each link is an assumption that could be wrong
- Outputs (things we produce) presented as outcomes (things that change)

---

### 1.4 Assumption Mapping: Desirability, Feasibility, Viability

**Core insight:** Every vision document contains dozens of hidden assumptions.
The dangerous ones are those that are simultaneously *critical to success* and
*lacking evidence*. The framework forces explicit identification and prioritization.

**The Three Lenses:**

| Lens | Core Question | Example Assumptions |
|------|---------------|-------------------|
| **Desirability** | Do users actually want this? | Users have this problem. Users would pay/switch to solve it. The problem is frequent/painful enough to motivate action. |
| **Feasibility** | Can we actually build this? | The technology works at the needed quality/scale. We have or can acquire the skills. The timeline is realistic. Third-party dependencies are reliable. |
| **Viability** | Does this make business sense? | The market is large enough. We can acquire users at sustainable cost. Revenue exceeds cost. Competitive moat exists. Regulatory environment allows it. |

**The Prioritization Matrix:**

```
         HIGH IMPORTANCE
              |
  [Test these    [These are your
   FIRST]        known knowns —
                  validate, don't
   High risk,    assume]
   low evidence
              |
  ────────────┼────────────
              |
  [Deprioritize  [Monitor but
   these]         don't obsess]
              |
         LOW IMPORTANCE
   LOW EVIDENCE ←──→ HIGH EVIDENCE
```

**Actionable LLM checks:**

| Check | How to Apply |
|-------|-------------|
| **Assumption extraction** | For each claim in the vision, rephrase as "We believe that..." and assess: is there evidence, or is this an assumption? |
| **Category assignment** | Tag each assumption as Desirability, Feasibility, or Viability. If one category has zero assumptions, the vision has a blind spot. |
| **Importance scoring** | Ask: "If this assumption is wrong, does the entire vision fail?" If yes = high importance. |
| **Evidence scoring** | Ask: "What evidence supports this assumption?" If the answer is "intuition" or "seems obvious" = low evidence. |
| **Kill-shot identification** | Find the assumptions that are both high-importance AND low-evidence. These are the ones that could kill the product. The vision should have a plan to test them. |

**Red flags in a Vision document:**
- No explicit statement of what must be true for the vision to succeed
- All assumptions are in the Desirability category (ignoring Feasibility and Viability)
- No plan to validate high-risk assumptions before committing resources
- Treating assumptions as facts ("Users need X" stated without evidence)

---

### 1.5 Pre-Mortem: Prospective Hindsight

**Core insight:** Research shows that imagining an event has *already occurred*
increases the ability to identify causes by 30%. Instead of asking "what could
go wrong?" (which triggers optimism bias), state "it failed — why?" (which
triggers analytical thinking).

**The Pre-Mortem Process adapted for Vision review:**

1. **State the premise**: "This product launched 18 months ago and failed. It is being shut down."
2. **Generate failure reasons independently** across categories:
   - **Market failures**: No one wanted it. The problem was not painful enough. A competitor did it better/cheaper.
   - **Execution failures**: Could not build it in time. Key technology did not work. Team lacked critical skills.
   - **Adoption failures**: Users tried it but did not stick. Onboarding was too complex. Integration with existing workflows failed.
   - **Business model failures**: Could not monetize. Customer acquisition cost exceeded lifetime value. Could not scale.
   - **Timing failures**: Too early (market not ready). Too late (already commoditized).
   - **External failures**: Regulatory change. Platform dependency risk. Economic downturn.
3. **Assess plausibility** of each failure mode (not just possibility but likelihood)
4. **Check the vision** for mitigations: does it acknowledge and address the top 3-5 most plausible failure modes?

**Actionable LLM checks:**

| Check | How to Apply |
|-------|-------------|
| **Failure mode generation** | For the stated vision, generate 10-15 specific failure scenarios across the categories above. |
| **Plausibility ranking** | Rank each by likelihood (not severity). The most *likely* failures are the most important to address. |
| **Mitigation check** | Does the vision document acknowledge any of these? A vision that does not address its most likely failure modes is naive, not optimistic. |
| **Single-point-of-failure detection** | Are there failure modes where *one thing going wrong* kills the entire vision? These need explicit contingency plans. |
| **Competitive pre-mortem** | "A competitor launched the same product 6 months before us and won. Why?" This surfaces timing and differentiation risks. |

**Red flags in a Vision document:**
- Pure optimism with no acknowledgment of risks
- Risk section that lists only low-probability exotic risks (asteroid strike) rather than high-probability mundane ones (users do not adopt)
- No contingency thinking or pivot criteria
- Success depends on everything going right simultaneously

---

### 1.6 AI Alignment: Intent vs. Specification

**Core insight:** AI systems routinely achieve their *specified* objective while
completely failing to achieve the *intended* objective. This is directly
analogous to product visions: teams optimize for what is measured (specifications)
rather than what is valued (intent). The four types of Goodhart's Law provide a
precise taxonomy.

**The Goodhart Taxonomy applied to Product Visions:**

| Goodhart Type | AI Example | Product Vision Equivalent |
|---------------|-----------|--------------------------|
| **Regressional** | Optimizing a proxy selects for the proxy-goal gap | Optimizing "daily active users" selects for addictive patterns, not value delivery |
| **Extremal** | Metric correlation breaks down at extremes | "Minimize response time" works until you sacrifice accuracy for speed |
| **Causal** | Agent manipulates proxy without affecting true goal | Team games the metric (e.g., counting bot traffic as "users") without creating real value |
| **Adversarial** | Agent exploits proxy to serve its own goals | Departments optimize their KPIs at the expense of the actual product goal |

**Actionable LLM checks:**

| Check | How to Apply |
|-------|-------------|
| **Proxy detection** | For each metric in the vision, ask: "Is this the actual thing we care about, or a proxy for it?" Then ask: "How could this proxy diverge from the true goal?" |
| **Specification completeness** | List what the vision measures. Then list what the vision *values*. Are there valued things that are not measured? Those will be sacrificed when pressure mounts. |
| **Gaming scenarios** | For each success metric, ask: "How could a team technically achieve this number while completely failing to deliver value?" If it is easy to imagine, the metric is gameable. |
| **Intent articulation test** | Can you state the vision's *intent* (the spirit) separately from its *specification* (the letter)? If you cannot, the specification IS the intent, and Goodhart's Law applies. |
| **Extremal stress test** | What happens if you maximize each stated goal to its extreme? Does it still serve users? "Maximize engagement" taken to its extreme = addictive dark patterns. |

**Red flags in a Vision document:**
- Success defined entirely by proxy metrics with no validation that proxies track true goals
- No acknowledgment that metrics can be gamed or can diverge from intent
- Metrics that could be optimized in ways that harm users
- No mechanism for detecting when optimization has gone off the rails

---

## Part 2: Cross-Framework Convergence

### What Do All Six Frameworks Check?

Despite coming from completely different domains (management science, consumer
psychology, social program evaluation, design thinking, cognitive psychology,
and computer science), these frameworks converge on the same fundamental concerns:

| Convergence Point | Frameworks That Check It |
|-------------------|------------------------|
| **Are the goals real outcomes, not just activities/outputs?** | OKR Validation, Theory of Change, Assumption Mapping |
| **Is there a validated causal mechanism, not just correlation or hope?** | Theory of Change, JTBD Four Forces, AI Alignment (Causal Goodhart) |
| **Have hidden assumptions been surfaced and prioritized?** | Assumption Mapping, Theory of Change, Pre-Mortem |
| **Has the resistance to change been modeled, not just the appeal?** | JTBD (Anxiety + Habit forces), Pre-Mortem (adoption failures) |
| **Can success metrics be gamed or diverge from true intent?** | AI Alignment (all four Goodhart types), OKR Validation |
| **Have the most likely failure modes been identified and addressed?** | Pre-Mortem, Assumption Mapping (high-importance/low-evidence quadrant) |
| **Is there a feedback loop to detect when reality diverges from plan?** | Theory of Change (continuous learning), AI Alignment (anomaly detection) |

### The Universal Validation Questions

Distilled from all six frameworks, these questions form the core of any
vision validation:

1. **What changes?** (Not what do we build — what state of the world is different?)
2. **For whom?** (Who specifically experiences the change? Can we name them?)
3. **Why would they change?** (What specific pain pushes them AND what specific pull attracts them? Not "it's better" — specifically better at what, and by enough margin to overcome switching costs?)
4. **What must be true?** (What are the hidden assumptions? Which ones are critical AND unproven?)
5. **How could this fail?** (Not "what exotic disaster could strike" but "what mundane, likely thing would make this not work?")
6. **How would we know?** (What would we measure? Could that measure be gamed? Does the measure track the actual intent?)
7. **What is the causal mechanism?** (Not just "If A then B" but "If A then B *because* C, and C requires D to be true.")

---

## Part 3: Multi-Pass Validation Architecture

### Why Multi-Pass?

A single-pass review conflates different types of analysis that require
different cognitive modes:
- **Comprehension** (what does the vision say?) is different from
- **Analysis** (is what it says internally consistent?) is different from
- **Critique** (does it hold up against external reality?) is different from
- **Synthesis** (what is the overall assessment?)

Attempting all four simultaneously leads to shallow analysis. Each pass should
use a different lens and produce distinct artifacts.

### Recommended Pass Structure

#### Pass 1: Extraction (Comprehension)

**Goal:** Build a structured model of what the vision actually claims.

**Operations:**
1. Extract all stated goals and classify each as Outcome or Activity
2. Extract the implied causal chain: Input -> Activity -> Output -> Outcome -> Impact
3. Extract all success metrics and classify each as Direct or Proxy
4. Extract all stated assumptions (rare — most visions do not state them)
5. Identify the target user and their current state

**Output artifact:** A structured representation:
```
GOALS: [{goal, type: outcome|activity}]
CAUSAL_CHAIN: [{if, then, mechanism, assumption}]
METRICS: [{metric, type: direct|proxy, gameable: bool}]
STATED_ASSUMPTIONS: [...]
TARGET_USER: {who, current_state, desired_state}
```

#### Pass 2: Force Analysis (JTBD + Assumption Mapping)

**Goal:** Model the forces for and against adoption; surface hidden assumptions.

**Operations:**
1. For each goal, identify the Push (why users are dissatisfied now)
2. For each goal, identify the Pull (what specifically attracts)
3. For each goal, identify the Anxiety (what users fear about switching)
4. For each goal, identify the Habit (what keeps users doing what they do now)
5. Assess: Push + Pull > Anxiety + Habit? If not, adoption will fail.
6. Extract hidden assumptions using the "We believe that..." format
7. Categorize each assumption: Desirability / Feasibility / Viability
8. Score each: Importance (high/medium/low) x Evidence (high/medium/low)
9. Identify kill-shot assumptions (high importance, low evidence)

**Output artifact:**
```
FORCE_BALANCE: [{goal, push, pull, anxiety, habit, net_assessment}]
ASSUMPTIONS: [{assumption, category, importance, evidence, is_kill_shot}]
```

#### Pass 3: Causal Chain Audit (Theory of Change + OKR Validation)

**Goal:** Test every link in the causal chain for validity.

**Operations:**
1. For each If-Then link from Pass 1, ask:
   - What mechanism makes this true?
   - Could the "If" happen without the "Then" following?
   - Could the "Then" happen without the "If"?
   - What assumption underlies this link?
2. For each metric from Pass 1, apply Goodhart checks:
   - Is this a proxy? For what?
   - How could this be gamed?
   - At what extreme does the correlation with intent break down?
3. For each Activity-typed goal, ask: "What outcome does this serve?"
   If no answer, the goal is orphaned.
4. For each gap in the causal chain, flag it as a "leap of faith."

**Output artifact:**
```
CHAIN_AUDIT: [{link, mechanism, strength: strong|weak|missing, assumptions}]
METRIC_AUDIT: [{metric, proxy_for, gaming_scenario, extremal_risk}]
LEAPS_OF_FAITH: [{from, to, what_is_missing}]
```

#### Pass 4: Pre-Mortem (Failure Mode Analysis)

**Goal:** Assume the vision failed and identify why.

**Operations:**
1. State: "It is 18 months later. This product has been shut down."
2. Generate failure scenarios across all categories:
   - Market / Demand failures
   - Execution / Technical failures
   - Adoption / Retention failures
   - Business Model / Unit Economics failures
   - Timing / Competitive failures
   - External / Regulatory failures
3. For each scenario, assess:
   - Plausibility (likely / possible / unlikely)
   - Whether the vision addresses it
   - Whether any kill-shot assumptions from Pass 2 are involved
4. Cross-reference with Pass 2 kill-shot assumptions and Pass 3 leaps of faith.
   These are the *compounding risks*.

**Output artifact:**
```
FAILURE_MODES: [{scenario, category, plausibility, addressed_in_vision: bool}]
COMPOUNDING_RISKS: [{failure_mode, linked_assumption, linked_leap}]
```

#### Pass 5: Synthesis and Judgment

**Goal:** Produce a final assessment with specific, actionable findings.

**Operations:**
1. Aggregate findings from Passes 1-4
2. Classify overall vision health:
   - **Outcome-grounded?** (Pass 1: Are goals outcomes or activities?)
   - **Adoption-realistic?** (Pass 2: Do forces balance toward adoption?)
   - **Causally-sound?** (Pass 3: Are the chains intact or full of leaps?)
   - **Failure-aware?** (Pass 4: Does it address its most likely failure modes?)
3. Produce a prioritized list of:
   - **Critical issues**: Things that would likely cause failure if unaddressed
   - **Significant gaps**: Missing analysis that should be done before committing
   - **Improvement opportunities**: Ways to strengthen the vision
4. For each critical issue, suggest a specific validation experiment or revision

**Output artifact:**
```
OVERALL_ASSESSMENT: {
  outcome_grounded: score + evidence,
  adoption_realistic: score + evidence,
  causally_sound: score + evidence,
  failure_aware: score + evidence
}
CRITICAL_ISSUES: [{issue, evidence_from_passes, suggested_action}]
SIGNIFICANT_GAPS: [{gap, why_it_matters, how_to_fill}]
IMPROVEMENTS: [{suggestion, expected_impact}]
```

---

## Part 4: Implementation Notes for LLM-Based Validation

### Why This Must Be Multi-Pass (Not Single Prompt)

1. **Context window management**: Each pass produces structured artifacts that
   the next pass consumes. A single pass would require holding all frameworks
   in context simultaneously, leading to shallow application of each.

2. **Cognitive mode switching**: Extraction (Pass 1) requires faithful reading.
   Force analysis (Pass 2) requires adversarial thinking. Causal audit (Pass 3)
   requires logical rigor. Pre-mortem (Pass 4) requires imaginative pessimism.
   Synthesis (Pass 5) requires balanced judgment. These are genuinely different
   modes.

3. **Avoiding premature judgment**: A single pass tends to form a judgment early
   and then confirm it. Multi-pass forces the LLM to complete analysis before
   forming conclusions.

4. **Auditability**: Each pass produces an artifact that can be reviewed
   independently. If the final judgment seems wrong, you can trace back to
   which pass produced the flawed input.

### Anti-Patterns to Guard Against

| Anti-Pattern | Why It Fails | What to Do Instead |
|-------------|-------------|-------------------|
| **Applying all frameworks at once** | Shallow analysis of each | One framework per pass, full depth |
| **Generating only positive analysis** | LLMs default to agreeable tone | Pre-mortem pass explicitly requires adversarial stance |
| **Treating proxy metrics as real** | Goodhart's Law | Always ask "proxy for what?" |
| **Accepting stated assumptions as exhaustive** | Most assumptions are unstated | Force "We believe that..." extraction |
| **Skipping the force balance** | Visions over-index on Pull | Require explicit Push, Anxiety, Habit analysis |
| **Confusing outputs with outcomes** | Most common vision flaw | Apply the "Why?" chain until you reach a state change |

### Calibration Questions for the LLM

Before beginning validation, the LLM should calibrate by asking itself:

1. "Am I being asked to validate this vision, or rubber-stamp it?"
   (Validation requires willingness to find problems.)
2. "Do I have enough context about the market, users, and technology to
   assess feasibility, or should I flag my uncertainty?"
   (Honest uncertainty is better than confident nonsense.)
3. "Am I pattern-matching to similar products, or analyzing the specific
   causal claims in THIS vision?"
   (Every vision is unique; analogies can mislead.)

---

## Sources

### OKR Validation: Outcome vs. Activity
- [Output vs. Outcome: Differences & OKR Examples](https://mooncamp.com/blog/output-vs-outcome)
- [OKR Best Practices for 2026 - Synergita](https://www.synergita.com/blog/okr-best-practices/)
- [OKRs in Product Management - Monday.com](https://monday.com/blog/rnd/okrs-for-product-management/)
- [OKR Framework 2025 - Kredily](https://kredily.com/okr-framework-2025-how-to-set-goals-that-actually-work/)

### JTBD Four Forces
- [Unpacking the Progress Making Forces Diagram](https://jobstobedone.org/radio/unpacking-the-progress-making-forces-diagram/)
- [Understanding Jobs Theory and Decision Forces](https://spatialrd.com/spatial-thinking/107/jobs-theory-and-four-forces-progress)
- [The Four Forces of Progress (JTBD) - Kathirvel](https://www.kathirvel.com/four-forces-of-progress-jtbd/)
- [Mastering Customer Acquisition with JTBD Forces - Brian Rhea](https://brianrhea.com/customer-acquisition-customer-retention/)
- [Using JTBD Push & Pull Diagram - Firmhouse](https://firmhouse.com/blog/using-the-jobs-to-be-done-push-pull-forces-diagram-to-understand-your-products-potential-9cac93855ac)

### Theory of Change
- [Theory of Change: Model, Components & Diagram Guide - SoPact](https://www.sopact.com/use-case/theory-of-change)
- [Theory of Change vs Logic Model - SoPact](https://www.sopact.com/guides/theory-of-change-vs-logic-model)
- [Developing a Logic Model or Theory of Change - Community Tool Box](https://ctb.ku.edu/en/table-of-contents/overview/models-for-community-health-and-development/logic-model-development/main)

### Assumption Mapping
- [How Assumptions Mapping Can Focus Your Teams - Strategyzer](https://www.strategyzer.com/library/how-assumptions-mapping-can-focus-your-teams-on-running-experiments-that-matter)
- [Assumption Mapping: How To Test Product Assumptions - Maze](https://maze.co/blog/assumption-mapping/)
- [Assumption Prioritization Canvas - Product Compass](https://www.productcompass.pm/p/assumption-prioritization-canvas)
- [Introduction to Assumptions Mapping - Mural](https://www.mural.co/blog/intro-assumptions-mapping)

### Pre-Mortem Technique
- [Pre-Mortem - The Uncertainty Project](https://www.theuncertaintyproject.org/tools/pre-mortem)
- [Performing a Project Premortem - Gary Klein](https://www.gary-klein.com/premortem)
- [Pre-mortem: Anticipate Failure with Prospective Hindsight - Ness Labs](https://nesslabs.com/pre-mortem-anticipate-failure-with-prospective-hindsight)
- [Imagining Failure to Attain Success - Brookings](https://www.brookings.edu/articles/the-art-and-science-of-pre-mortems/)
- [Performing a Project Premortem - HBR](https://hbr.org/2007/09/performing-a-project-premortem)

### AI Alignment / Specification Gaming
- [Goal Misalignment in Agentic AI - AiSecurityDIR](https://aisecuritydir.com/goal-misalignment-in-agentic-ai-technical-analysis/)
- [Specification Gaming Examples in AI - LessWrong](https://www.lesswrong.com/posts/AanbbjYr5zckMKde7/specification-gaming-examples-in-ai-1)
- [Classifying Specification Problems as Variants of Goodhart's Law - Victoria Krakovna](https://vkrakovna.wordpress.com/2019/08/19/classifying-specification-problems-as-variants-of-goodharts-law/)
- [The Four Flavors of Goodhart's Law - Holistics](https://www.holistics.io/blog/four-types-goodharts-law/)
- [Natural Emergent Misalignment from Reward Hacking - Anthropic](https://assets.anthropic.com/m/74342f2c96095771/original/Natural-emergent-misalignment-from-reward-hacking-paper.pdf)

### Multi-Pass LLM Reasoning
- [Multi-Step Reasoning with LLMs, a Survey - ACM](https://dl.acm.org/doi/10.1145/3774896)
- [Reasoning in LLMs: From Chain-of-Thought to Massively Decomposed Agentic Processes](https://www.preprints.org/manuscript/202512.2242)
- [A Survey on Verifying Reasoning Chains Generated by LLMs](https://hal.science/hal-05448955v1/document)
