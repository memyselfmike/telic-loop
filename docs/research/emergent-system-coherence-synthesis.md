# Emergent System Coherence — Cross-Domain Research Synthesis

**Date**: 2026-02-15
**Context**: Addressing Reasoning Gap 4 from V3_REASONING_GAPS.md
**Purpose**: Synthesize independent research into an operational mechanism for detecting and managing emergent system-level issues that part-level checks miss

---

## The Problem

The loop validates features individually: QC checks each feature (tests, linting, types), Critical Eval experiences individual flows as a user, regression checks that existing features still pass. But nobody checks whether the WHOLE SYSTEM is coherent.

A dashboard with 5 well-built widgets can still be unusable if the widgets don't form a coherent information hierarchy. A codebase where every module passes its tests can still be architecturally degraded — cyclic dependencies, God Components, inconsistent patterns. These are emergent problems: they arise from interactions between parts, not from any individual part being wrong.

---

## Six Frameworks Surveyed

### Framework 1: Systems Thinking / Emergent Properties

**Domain**: Systems Dynamics, Complexity Science (Donella Meadows, Jay Forrester, INCOSE)

**Core model**: Emergence occurs when a system exhibits macro-level behaviors that cannot be predicted from component properties alone. Systems are characterized by stocks, flows, and feedback loops. The topology of feedback loops — not the properties of individual components — determines system behavior.

**Key findings**:
- **Traditional analysis fails at emergence** because it analyzes subsystems separately and aggregates linearly. Emergent properties are non-linear and arise from interactions.
- **Meadows' 12 leverage points** rank intervention points: most fixes happen at levels 12-9 (parameter tweaks), but highest-leverage interventions are at levels 3-1 (goals, paradigms). An evaluator that only checks parameters works at the lowest leverage.
- **Feedback loops are the signature of system behavior**: Reinforcing loops amplify (virtuous/vicious cycles); balancing loops resist change. Undetected reinforcing loops compound silently until a tipping point.
- **Behavior-over-time is the diagnostic tool**: A system that looks healthy at any single point can be on an unsustainable trajectory visible only over multiple observations.

**Operationalizable techniques**:
- Map feedback loops: trace where Feature A's output becomes Feature B's input which affects Feature A
- Classify interventions by leverage level — prefer structural fixes over parameter tweaks
- Track metrics across iterations, not just current snapshot — trajectory matters more than position

---

### Framework 2: Software Architecture Evaluation (ATAM + Fitness Functions)

**Domain**: Software Engineering (Carnegie Mellon SEI, Thoughtworks)

**Core model**: ATAM evaluates architecture by identifying sensitivity points, tradeoff points, and risks at the system level. Fitness functions are automated "unit tests for architecture" that detect drift, debt, and degradation continuously.

**Key findings**:
- **Quality attributes trade off invisibly**: A system can satisfy performance and security individually while they're fundamentally in tension. Tradeoffs only appear when evaluating multiple attributes simultaneously.
- **ATAM produces four outputs**: Risks, non-risks, sensitivity points (small change → large effect), tradeoff points (decision affects multiple attributes in opposing ways).
- **Holistic fitness functions catch emergent issues**: Atomic functions test one characteristic; holistic functions test combinations across the whole system (e.g., "1000 concurrent users while maintaining sub-200ms response times").
- **Architecture reflexion modeling** compares intended vs. actual architecture — divergences, convergences, absences.
- **Fitness functions prevent silent erosion** by making architectural constraints executable and testable.

**Operationalizable techniques**:
- Define holistic fitness functions: dependency cycle detection, layering violations, API consistency, naming uniformity
- Run architecture reflexion: extract actual dependency graph, compare against intended layers, flag divergences
- Track fitness function violations over time — a trend of increasing violations = architectural erosion

---

### Framework 3: Gestalt Psychology / UX Holistic Evaluation

**Domain**: Perceptual Psychology, UX Design (Wertheimer, Nielsen, Norman)

**Core model**: "The whole is other than the sum of the parts." Human perception organizes elements into wholes using innate principles: proximity, similarity, continuity, closure, common fate. Users perceive coherence or incoherence instantly, even if they cannot articulate why. Nielsen's 10 heuristics provide a systematic checklist with Heuristic #4 (Consistency and Standards) directly addressing system-level coherence.

**Key findings**:
- **Gestalt principles detect emergent perception problems**: Individual UI elements that each pass review can fail as a whole if they violate proximity (unrelated elements appear grouped), similarity (related elements across features look different), or continuity (visual flow breaks at feature boundaries).
- **Internal consistency (H4) is invisible at component level**: Each component is internally consistent; the inconsistency only appears when comparing across components.
- **Coherence = information hierarchy**: A UI fails when widgets don't form a coherent hierarchy of what matters most, what relates to what, and what to do next.
- **The aesthetic-usability effect**: Visually consistent interfaces are PERCEIVED as more usable, even when objective usability is identical. Inconsistency creates a "something is off" feeling.
- **Heuristic eval + cognitive walkthrough are complementary**: Heuristic evaluation does breadth (system-wide sweep); cognitive walkthrough does depth (specific task flows).

**Operationalizable techniques**:
- Apply Nielsen's heuristics at system level (not per-feature): consistent status visibility, error prevention, information density across features
- Gestalt audit across feature boundaries: visual groupings, similarity of related elements, visual flow continuity
- Cross-feature cognitive walkthrough: trace user journeys that span multiple features, check for jarring transitions
- Terminology drift detection: find concepts referred to by different names in different features
- Interaction pattern consistency: catalog patterns (filtering, deletion, submission, errors) and verify uniformity

---

### Framework 4: Combinatorial Interaction Testing

**Domain**: Software Testing (NIST Combinatorial Testing Program)

**Core model**: Most defects arise from interactions between parameters/features, not from individual components. Systematically testing all t-way combinations (typically t=2, pairwise) catches the vast majority of interaction defects. You don't need exhaustive testing — pairwise coverage is sufficient.

**Key findings**:
- **70-80% of defects are triggered by two-parameter interactions** (NIST empirical data across multiple domains). Three-parameter interactions add ~10%. Four+ add <5%.
- **Cross-cutting concerns are the most dangerous interaction surfaces**: Auth, error handling, logging, caching, validation — they touch every feature and create implicit coupling.
- **Pairwise testing reduces test suites by 85-95%** while maintaining interaction coverage.
- **Feature interaction testing in product lines** specifically addresses features that work correctly alone but fail when combined. Prioritization strategies focus on most likely interaction failures first.

**Operationalizable techniques**:
- Build a feature interaction matrix: classify each pair as independent, data-sharing, state-affecting, or conflicting
- Audit cross-cutting concern consistency: same auth, same error handling, same validation patterns everywhere
- Detect implicit coupling: shared global state, database tables, cache keys, file paths between features that don't explicitly depend on each other
- Prioritize testing by risk: recently changed features, shared mutable state, different implementation times

---

### Framework 5: Code Smell / Architectural Erosion Detection

**Domain**: Software Engineering (Martin Fowler, Tushar Sharma, SEI Architecture Degradation Research)

**Core model**: Architectural smells are sub-optimal design patterns at the system level — not bugs, not local code smells, but systemic structural degradation. Four canonical smells: Cyclic Dependency, Hub-Like Dependency, Unstable Dependency, God Component. They accumulate silently as individually reasonable decisions collectively erode the intended architecture.

**Key findings**:
- **Smells have different survival rates**: God Components survive ~19 versions (they attract more responsibility — reinforcing loop). Unstable Dependencies survive ~24 versions. Cyclic Dependencies are fixed faster (~6 versions). Long-lived smells cause the most cumulative erosion.
- **Co-occurrence patterns are diagnostic**: Feature Envy + Shotgun Surgery + Divergent Change clustering in the same area = responsibility leakage. Individual smells are noisy; co-occurrence patterns are reliable indicators.
- **Architecture drift is silent**: No test fails, no linter triggers, no user reports a bug. Drift only becomes visible when comparing actual vs. intended structure, or when accumulated drift makes changes unexpectedly difficult.
- **Emerging smells can be predicted** by analyzing trends in dependency metrics 2-3 versions before they fully manifest.

**Operationalizable techniques**:
- Dependency graph analysis: cycle detection, hub detection, instability metrics, God Component detection
- Reflexion analysis: compare actual dependencies against intended architecture layers
- Smell co-occurrence patterns: Feature Envy + Shotgun Surgery = responsibility leakage; God Component + Hub = bottleneck
- Trend analysis: track smell counts across iterations, flag accelerating deterioration

---

### Framework 6: Ecological Assessment / Ecosystem Health

**Domain**: Conservation Biology, Ecosystem Science (Costanza, Rapport, Holling)

**Core model**: Ecosystem health is assessed holistically using three indicators: **Vigor** (productivity, throughput), **Organization** (structural complexity, connectivity diversity), **Resilience** (capacity to absorb disturbances without structural change). Recent extensions add **Ecosystem Services Supply Rate** (is the system actually delivering value?). No single indicator suffices; health is multidimensional by definition.

**Key findings**:
- **VOR is inherently holistic**: A system can have high vigor (fast, productive) but low organization (tangled) and low resilience (brittle). All three must be assessed together.
- **Diversity indices measure richness AND evenness**: A codebase with 50 modules but one God Module containing 60% of logic has low evenness — poor organizational health despite looking module-rich.
- **Trophic cascades**: Changing a core abstraction doesn't just affect direct dependents — effects cascade through the entire system in ways only predictable from the full dependency topology.
- **Functional redundancy protects resilience**: Systems with fallback mechanisms, circuit breakers, and graceful degradation are more resilient than systems where each function has exactly one implementation with no fallback.
- **Assessment must be practical**: Health indicators should be "simple to apply, easily understood, scientifically justifiable, quantitative, and acceptable in terms of costs."
- **Adaptive cycles**: Systems cycle through growth → conservation (rigidity) → release (crisis) → reorganization. A coherence evaluator should detect which phase the system is in.

**Operationalizable techniques**:
- Vigor: build times, test pass rates, deployment frequency, active feature count
- Organization: module evenness (Shannon index on LOC distribution), coupling/cohesion ratios, dependency tree depth/breadth
- Resilience: error handling coverage, fallback mechanisms, single points of failure, cascade blast radius
- Cascade analysis: for each change, trace impact through dependency graph — how many levels deep?
- Adaptive cycle detection: is the system growing, conserving/rigidifying, or approaching a tipping point?

---

## Seven Convergence Points

### 1. The Whole Cannot Be Evaluated by Evaluating the Parts
All six frameworks independently conclude that emergent properties are fundamentally invisible at the component level. System-level evaluation must look at relationships, interactions, and patterns — not aggregate component scores.

### 2. Interactions Are Where Problems Hide
Every framework focuses attention on the spaces BETWEEN components: feedback loops, tradeoff points, visual relationships, pairwise interactions, dependency cycles, trophic cascades. The evaluator should spend MORE effort on interfaces and data flows than on internal component quality.

### 3. Drift Is Silent and Cumulative
Architecture erodes, terminology drifts, patterns diverge, complexity accumulates — all without any test failing or any user complaining. The evaluator MUST track trends over iterations. A system that looks fine today but is deteriorating on every metric is in danger.

### 4. Structure Determines Behavior
The dependency graph, the feedback loop topology, the information hierarchy — these structural properties determine system behavior more than the quality of individual implementations. Structural analysis is the most predictive indicator of system health.

### 5. Both Static Structure and Dynamic Behavior Matter
No single mode of analysis suffices. Static analysis catches structural smells; dynamic analysis catches behavioral inconsistencies. The evaluator needs both.

### 6. Health Requires Multiple Independent Indicators
Every framework rejects a single health score. VOR uses three indicators. ATAM evaluates multiple quality attributes. Nielsen has 10 heuristics. The evaluator should produce a multi-dimensional assessment with independently evaluated dimensions.

### 7. Assessment Must Be Continuous, Not One-Time
Fitness functions run in CI/CD. Ecological monitoring is ongoing. Architectural smells accumulate over versions. The coherence check should run after every milestone, maintaining history and reporting trends.

---

## Seven Evaluation Dimensions

Based on the convergence analysis, the System Coherence Check assesses seven dimensions, ordered from most structural to most strategic:

### Dimension 1: Structural Integrity
Does the system's actual structure match its intended architecture? Are dependencies clean, layered, and acyclic? Is responsibility distributed?

**Checks**: Dependency cycle detection, layering violations, hub/God Component detection, responsibility evenness (Shannon index), trend tracking across iterations.

### Dimension 2: Interaction Coherence
Do features interact correctly and without unintended side effects? Are feature boundaries clean?

**Checks**: Feature interaction matrix (independent/data-sharing/state-affecting/conflicting), shared state audit, feedback loop detection, cross-cutting concern consistency.

### Dimension 3: Conceptual Integrity
Does the system tell a coherent conceptual story? Are naming, abstractions, and patterns consistent?

**Checks**: Terminology consistency (synonym/homonym detection), design pattern uniformity, abstraction level consistency, naming convention adherence, mental model continuity across feature boundaries.

### Dimension 4: Behavioral Consistency
Does the system behave predictably across analogous situations in different features?

**Checks**: Error handling symmetry, loading/empty/error state consistency, data validation consistency, response format uniformity, performance evenness across features.

### Dimension 5: Informational Flow Integrity
Does data flow through the system cleanly, without leaks, dead ends, or contradictions?

**Checks**: Single source of truth verification, cross-view data consistency, dead data detection, duplication risk assessment, flow completeness (input → storage → display), information hierarchy coherence.

### Dimension 6: Resilience
When something goes wrong, does the system degrade gracefully or collapse?

**Checks**: Failure cascade analysis, functional redundancy, error boundary completeness, recovery path verification, single point of failure identification.

### Dimension 7: Evolutionary Capacity
Can the system accommodate future change without requiring rewrites?

**Checks**: Coupling trend, smell accumulation rate, extension cost ratio (modified-existing / new-files), API stability, dead code accumulation, adaptive cycle phase detection.

---

## Operational Design: System Coherence Evaluation

### When It Runs

**Two modes** (paralleling the VRC quick/full pattern from the Process Monitor):

1. **Quick Coherence Check** (Haiku, every 5 tasks or at epic boundaries):
   - Dimensions 1-2 only (Structural Integrity + Interaction Coherence)
   - Based on automated analysis: dependency graph, cross-cutting concern diff
   - Cost: ~$0.02-0.05 per check
   - Output: GREEN/YELLOW/RED per dimension

2. **Full Coherence Evaluation** (Opus, at epic boundaries + pre-exit-gate):
   - All 7 dimensions
   - Includes semantic analysis: terminology audit, pattern consistency, information hierarchy
   - Includes behavioral reasoning: cognitive walkthrough of cross-feature journeys
   - Cost: ~$0.50-1.00 per evaluation
   - Output: Structured 7-dimension report with specific findings and trend comparison

### Integration with Existing Mechanisms

| Mechanism | Scope | Complementary Role |
|-----------|-------|-------------------|
| QC Agent | Individual feature correctness | Catches implementation bugs |
| Regression | Feature stability after changes | Catches breakage from changes |
| Critical Eval | Individual feature experience | Catches bad user experience per feature |
| VRC | Value delivery progress | Measures how much of the vision is realized |
| **Coherence Eval** | **System-level emergent properties** | **Catches issues that arise from feature interactions** |

### Output Format

```python
@dataclass
class CoherenceReport:
    iteration: int
    mode: Literal["quick", "full"]
    timestamp: str
    dimensions: dict[str, DimensionResult]   # dimension_name → result
    overall: Literal["HEALTHY", "WARNING", "CRITICAL"]
    trends: dict[str, str]                    # dimension_name → "improving" | "stable" | "degrading"
    findings: list[CoherenceFinding]          # specific actionable findings
    comparison_to_previous: str               # narrative: what changed since last check

@dataclass
class CoherenceFinding:
    dimension: str
    severity: Literal["info", "warning", "critical"]
    description: str
    affected_files: list[str]
    suggested_action: str
    leverage_level: int   # Meadows 1-12, higher = more structural
```

### Decision Engine Integration

The coherence evaluation feeds into the existing decision engine:
- **HEALTHY**: No action needed, continue executing
- **WARNING**: Log findings, include in next Course Correction consideration
- **CRITICAL**: Trigger Course Correction immediately — structural issues must be addressed before adding more features (building on a degraded foundation wastes effort)

### Anti-Patterns

1. Don't run full coherence on every iteration — it's expensive and unnecessary. Quick checks are sufficient for continuous monitoring.
2. Don't try to fix all coherence issues at once — prioritize by leverage level (structural > behavioral > cosmetic).
3. Don't treat coherence findings as task blockers — they're strategic signals, not tactical blockers. The loop should finish the current task, then address coherence.
4. Don't aggregate dimensions into a single score — a system that scores well on 6 dimensions and poorly on 1 has a SPECIFIC problem. A mediocre average hides that.
5. Don't evaluate coherence before enough features exist — Dimensions 2-7 are meaningless with only 1 feature. Start coherence checks after 3+ features are implemented.

---

## Phase Assignment

Given the existing V3 phasing strategy:

- **Phase 2** (with VRC + Course Correction): Add Quick Coherence Check (Dimensions 1-2 only, automated analysis). Natural complement to VRC — VRC measures value delivery, Quick Coherence measures structural health.
- **Phase 3** (with Critical Eval + Process Monitor): Add Full Coherence Evaluation (all 7 dimensions). Natural complement to Critical Eval — Critical Eval judges individual feature experience, Full Coherence judges system-level properties.

This follows the existing stub pattern: Phase 2 implements a lightweight version, Phase 3 replaces with the full mechanism.
