# Outer Loop Design — Project-Level Orchestration

## Status: Design Proposal (not implemented)

This document describes how telic-loop could be extended from sprint-level delivery to **project-level delivery** — orchestrating multiple sprints to build entire projects autonomously.

The inner loop (plan → review → implement → evaluate) is proven and stable. This design adds an **outer loop** that decides *which* sprint to run next and *what the system knows* going into it. The inner loop stays completely untouched.

## Problem Statement

The inner loop delivers sprint-sized units of work well. But real projects aren't single sprints — they evolve across iterations. Sprint 1 might reveal that the original database choice won't scale. Sprint 3 might uncover UX requirements that weren't in the original vision. A human orchestrating sprints manually can adapt; we want the system to do this autonomously.

Key challenges:
- **Learning between sprints**: What does the system carry forward?
- **Adaptive planning**: Each sprint's scope should be informed by everything before it
- **Cross-sprint regression**: Sprint 3 must not break what Sprint 1 built
- **Termination**: When is a project "done"?

## Architecture

### Outer Loop Flow

```
PROJECT_VISION.md
       ↓
    assess → plan sprint → execute sprint (inner loop) → retrospect → decide
      ↑                                                                  |
      |          ← update project memory ←──────────────────────────────┘
      └── next sprint / pivot / complete
```

### Phases

#### 1. Assess

An Opus agent reads project memory and the current state of the codebase to understand:
- What has been built so far
- What's working (passing tests, verified deliverables)
- What's missing relative to the project vision
- What was learned in previous sprints (pivots, technical constraints discovered)

#### 2. Plan Sprint

The **Sprint Planner** (new role, Opus) writes the next sprint's VISION.md and PRD.md. This is fundamentally different from planning all sprints upfront — each sprint plan is shaped by everything that came before.

The Sprint Planner has access to:
- `PROJECT_VISION.md` — the big-picture outcome
- `ARCHITECTURE.md` — living architecture doc, updated after each sprint
- `DECISIONS.md` — accumulated ADRs
- `BACKLOG.md` — remaining work, reprioritized after each retrospective
- `.project_state.json` — structured history (sprints completed, metrics, blockers)
- The actual codebase (read-only exploration)

It produces:
- `sprints/<sprint-N>/VISION.md` — sprint-scoped vision
- `sprints/<sprint-N>/PRD.md` — sprint-scoped requirements
- `sprints/<sprint-N>/ARCHITECTURE.md` — current architecture context for the inner loop's planner

#### 3. Execute Sprint

Run the existing inner loop unchanged:
```python
config = LoopConfig(
    sprint=f"sprint-{n}",
    sprint_dir=project_dir / f"sprints/sprint-{n}",
    project_dir=project_dir,
)
run_loop(config, state, agent)
```

The inner loop's API surface is small: `LoopConfig` + `run_loop()`. The outer loop constructs configs and calls it.

#### 4. Retrospect

After the inner loop completes, a **Retrospective** agent (Opus, read-only) reviews what happened and updates project memory:

1. Read the sprint's DELIVERY_REPORT.md, final state, and verification results
2. Update `ARCHITECTURE.md` with what was *actually built* (not what was planned)
3. Append to `DECISIONS.md` with key choices the builder made and why
4. Update `BACKLOG.md` — remove delivered items, add newly discovered work
5. Update `.project_state.json` with sprint metrics and outcomes
6. Optionally update `PROJECT_VISION.md` if scope has shifted

This is where learning happens. Without it, sprints are isolated. With it, the project accumulates institutional knowledge.

#### 5. Decide

Evaluate whether to:
- **Continue** — plan and execute the next sprint
- **Pivot** — the vision needs adjustment based on what was learned
- **Complete** — the project vision has been achieved
- **Halt** — budget exhausted or fundamental blocker encountered

This could be an Opus agent, a human checkpoint, or both (human approves the next sprint plan before execution).

## Project Memory

### Recommended: File-Based

Start with structured markdown files that agents read directly. The agents' context windows are large enough for this, and it requires no infrastructure.

```
my-project/
├── PROJECT_VISION.md          # Big-picture outcome (may evolve)
├── ARCHITECTURE.md            # Living architecture doc, updated per sprint
├── DECISIONS.md               # Accumulated ADRs (append-only)
├── BACKLOG.md                 # Remaining work, reprioritized per retrospective
├── .project_state.json        # Structured: sprint history, metrics, gates
├── sprints/
│   ├── sprint-1/              # Completed sprint (inner loop artifacts)
│   │   ├── VISION.md
│   │   ├── PRD.md
│   │   ├── DELIVERY_REPORT.md
│   │   └── .loop_state.json
│   ├── sprint-2/
│   │   └── ...
│   └── sprint-N/              # Current sprint
└── src/                       # The actual project codebase
```

### Why Not Embeddings?

An embedding-based memory (vector store) would add:
- Infrastructure dependency (vector DB or local index)
- Opacity (can't just read the memory files to debug)
- Complexity that isn't justified until projects exceed ~10 sprints

If projects get large enough that the living docs exceed useful context, add retrieval *then*. Start simple.

### Memory Hygiene

The retrospective agent must be disciplined:
- `ARCHITECTURE.md` reflects *current* state, not history. Rewrite, don't append.
- `DECISIONS.md` is append-only but each entry is concise (short MADR format).
- `BACKLOG.md` is actively curated — completed items are removed, not struck through.
- Old sprint artifacts are kept but not loaded into context. They're an archive, not working memory.

## New Components

### ProjectConfig

```python
@dataclass
class ProjectConfig:
    project_name: str
    project_dir: Path
    project_vision: Path          # PROJECT_VISION.md
    max_sprints: int = 20         # Safety valve
    sprint_budget_tokens: int = 0 # Per-sprint token cap (0 = unlimited)
    human_checkpoint: bool = True # Require approval before each sprint
```

### ProjectState

```python
@dataclass
class ProjectState:
    project_name: str
    sprints_completed: list[SprintSummary]
    current_sprint: int
    backlog_items: int
    total_tokens_used: int
    status: Literal["active", "completed", "halted", "pivoted"]
```

### New Roles

| Role | Model | Purpose |
|------|-------|---------|
| Sprint Planner | Opus | Reads project memory, writes next sprint's VISION + PRD |
| Retrospective | Opus | Reviews completed sprint, updates project memory |
| Project Evaluator | Opus | Assesses overall project vision delivery (periodic) |

These are *outer loop* roles. The 4 inner loop roles (Planner, Reviewer, Builder, Evaluator) are unchanged.

## The Telic Philosophy

The name "telic" means purposeful — directed toward an end. The system's job is not to produce artifacts, check boxes, or reach a "done" state as fast as possible. Its job is to deliver the *outcome* promised in the vision.

This is a direct response to a fundamental LLM failure mode: **completion bias**. Language models are trained on next-token prediction and RLHF reward signals that favor producing plausible-looking output quickly. Left unchecked, an LLM will:

- Generate code that looks right but doesn't actually work end-to-end
- Skip edge cases, error handling, and security because they slow down "completion"
- Report tasks as done based on what it wrote, not what it verified
- Produce MVP-quality work when production quality was asked for
- Optimize for getting to the exit condition rather than meeting the bar

The inner loop already fights this with adversarial evaluation (the builder never grades its own work) and verification scripts (mechanical proof that things work). The outer loop needs to fight it even harder because the stakes are higher — an entire project, not just a sprint.

### Quality Ambition as a First-Class Input

The project-level vision should explicitly state the quality bar:

- **MVP**: Ship the minimum that proves the concept works. Rough edges acceptable.
- **Production**: Secure, tested, documented, accessible, responsive. Ready for real users.
- **Enterprise**: All of production, plus audit logging, RBAC, monitoring, DR, compliance.

This isn't a nice-to-have — it fundamentally changes what every sprint delivers. An MVP sprint might skip auth; a production sprint must include it. The Sprint Planner, inner loop Planner, and all Evaluators need to see this quality bar and hold work to it.

```markdown
# PROJECT_VISION.md

## Quality Bar: Production

This is not a prototype. Every sprint must deliver production-quality work:
secure, tested, accessible, and ready for real users. The evaluator will
reject work that merely "functions."
```

### Project-Level Critical Evaluation

The sprint-level evaluator asks: "Did this sprint deliver what its VISION.md promised?"

The project-level evaluator asks harder questions:

1. **Are we building the right thing?** Does the accumulated work actually serve the PROJECT_VISION, or have we drifted?
2. **How close are we?** Honest gap analysis — what percentage of the project vision is genuinely delivered and verified?
3. **What's the quality?** Is the work at the stated quality bar (MVP/Production/Enterprise), or has the system been cutting corners?
4. **Is it coherent?** Do the sprints form a unified product, or a collection of disconnected features?
5. **Would a real user succeed?** End-to-end walkthrough of the core user journeys against the actual running system.

This should run after every 2-3 sprints (not every sprint — too expensive and the delta is too small). It produces a **Project Health Report** that the Sprint Planner reads before planning the next sprint.

### Project-Level Test Suite

This is the mechanical counterpart to the evaluator's judgment. Verification scripts from completed sprints are **promoted** to a persistent, growing test suite.

```
my-project/
├── tests/                          # Project-level test suite (grows across sprints)
│   ├── regression/                 # Promoted from completed sprints
│   │   ├── sprint-1_integration_api.sh
│   │   ├── sprint-1_value_search.sh
│   │   ├── sprint-2_security_auth.sh
│   │   └── sprint-2_integration_payments.sh
│   ├── e2e/                        # Cross-sprint end-to-end journeys
│   │   └── user_signup_to_purchase.sh
│   └── security/                   # Accumulated security checks
│       └── project_security_scan.sh
└── sprints/
    └── ...
```

**Lifecycle of a test:**
1. Builder creates `security_auth.sh` during Sprint 2
2. Sprint 2 completes — retrospective promotes it to `tests/regression/sprint-2_security_auth.sh`
3. Sprint 3 starts — builder runs all project-level tests as P0
4. If Sprint 3 breaks auth, the promoted test catches it immediately

**Cross-sprint e2e tests** are different. These test *user journeys* that span multiple sprints' features (e.g., "sign up, create a recipe, search for it, share it"). The Retrospective agent or Project Evaluator identifies these and creates them. They're the highest-value tests because they verify the *product works as a whole*, not just that individual features pass.

## Fighting Completion Bias

The LLM's drive to finish fast is the single biggest threat to quality. Every layer of the system needs countermeasures:

### Inner Loop (existing, could strengthen)

| Countermeasure | Status | How it helps |
|----------------|--------|--------------|
| Adversarial evaluator | Implemented | Builder can't grade itself |
| Verification scripts | Implemented | Mechanical proof, not LLM judgment |
| Security self-check | Implemented | Builder reviews own code for OWASP basics |
| Security verification scripts | Implemented | Automated scanning catches what self-check misses |
| Browser-based evaluation | Implemented | Evaluator uses the app as a real user via Playwright |
| Craft Standard | Implemented | Visual/UX quality bar in builder prompt |

Potential additions:
- **"Show your work" requirement**: Builder must demonstrate (via curl, test output, or screenshot) that each task *actually works* before reporting complete — not just that the code looks right
- **Evaluator budget floor**: Evaluator must spend a minimum number of tool calls before issuing SHIP_READY — prevents rubber-stamping

### Outer Loop (new)

| Countermeasure | Purpose |
|----------------|---------|
| Quality bar in PROJECT_VISION.md | Explicit standard that every agent reads |
| Project-level test suite | Cross-sprint regression — mechanical, not LLM judgment |
| Project Evaluator (periodic) | "Are we building the right thing at the right quality?" |
| Retrospective forced learning | System must articulate what it learned, not just move on |
| Sprint Planner justification | Must explain why this sprint advances the vision |
| Human checkpoint (optional) | Final backstop against drift |

### The Core Principle

**Verification must be independent of generation.** The thing that builds should never be the thing that judges. The thing that judges should use mechanical evidence (tests, browser interaction, security scans) alongside LLM judgment. And the project level should verify that the accumulated sprints form a coherent, quality product — not just a stack of individually-passing sprints.

## Orchestration Framework Considerations

### Should we use LangChain, LangGraph, or similar?

The short answer: **probably not, but it's worth understanding why.**

**What these frameworks offer:**
- State machines / graph-based workflow definitions
- Built-in memory management (conversation, summary, vector)
- Tool/agent abstraction layers
- Observability and tracing
- Checkpoint and resume

**What telic-loop already has:**
- State machine via `determine_phase()` + gates — simple, debuggable, ~20 lines
- File-based state persistence via `.loop_state.json` — transparent, version-controlled
- Agent abstraction via `claude-agent-sdk` — thin wrapper, direct control
- Tool system via structured tool schemas — 6 tools, validated, no framework needed
- Crash recovery with exponential backoff

**The mismatch:**

LangChain/LangGraph are designed for request-response AI applications — chatbots, RAG pipelines, multi-step reasoning chains. Telic-loop is a **long-running autonomous build system**. The architectural concerns are different:

| Concern | LangChain's answer | Telic-loop's answer |
|---------|-------------------|---------------------|
| State | In-memory + checkpoints | File on disk (survives crashes, human-readable) |
| Memory | Vector store + summarization | Living markdown docs (agents read files) |
| Agent control | Framework manages turns | Outer loop manages phases, inner agents run to completion |
| Observability | LangSmith tracing | State file + delivery reports (version-controlled artifacts) |
| Tool calls | Framework dispatches | Tool CLI subprocess (agents call tools via Claude Code) |

Adding LangChain would mean wrapping the Claude Agent SDK in another abstraction layer, converting the file-based state to LangChain's checkpoint format, and adopting LangChain's memory system instead of the transparent file-based approach. The result would be more abstract but not more capable.

**Where a framework *might* help:**

- **LangGraph's state machine visualization** could be useful for debugging complex outer loop flows — but only if the flow becomes complex enough to need it
- **Vector-based memory** might become necessary at scale (10+ sprints) — but file-based should be tried first
- **Observability/tracing** would help debug multi-sprint runs — but a simpler solution (structured logging to a JSONL file) achieves the same thing

**Recommendation:**

Don't adopt an orchestration framework preemptively. The current architecture is simple, transparent, and debuggable. If a specific capability is needed (e.g., vector memory at scale), add that capability directly rather than adopting an entire framework for one feature. Revisit if the outer loop's complexity grows beyond what file-based state + simple Python can handle cleanly.

### What *Would* Help

Instead of a framework, invest in:

1. **Structured logging**: Every outer loop decision (sprint planned, retrospective finding, project evaluation) logged to a JSONL file with timestamps, token costs, and rationale. This is the observability layer.

2. **Project dashboard**: A simple HTML report (like the inner loop's VALUE_CHECKLIST.md but for the project) showing sprint history, test suite health, project completion percentage, and token spend. Generated after each sprint.

3. **Test runner infrastructure**: A reliable way to run the growing project-level test suite. This is the most important piece of tooling — more valuable than any orchestration framework.

## Hard Problems

### 1. When Is a Project "Done"?

Sprints have clear gates (3 gates → complete). Projects are fuzzier — the vision may evolve. Options:
- **Project Evaluator** periodically assesses "has the project vision been achieved?" against PROJECT_VISION.md
- **Human checkpoint** after each sprint — human confirms completion or continues
- **Backlog exhaustion** — no more work items + all sprints passing

Recommend: human checkpoint by default, with an option to run fully autonomous with a Project Evaluator gate.

### 2. Scope Creep

Each retrospective may discover new work. Without bounds, the outer loop never terminates. Mitigations:
- Hard cap on sprint count (`max_sprints`)
- Token budget at the project level
- Sprint Planner must justify each new sprint against the original vision
- Backlog items should trace back to PROJECT_VISION.md requirements

### 3. Cross-Sprint Regression

The inner loop handles regression *within* a sprint. But Sprint 3 might break Sprint 1's deliverables. Solutions:
- **Project-level test suite**: verification scripts from completed sprints are promoted to a persistent test suite that runs at the start of every subsequent sprint
- The inner loop's P1 priority (fix failing verifications) already handles this — the key is making sure old verification scripts are visible to new sprints
- Simplest implementation: copy/symlink completed sprint verifications into a `tests/` directory that the builder always runs

### 4. Context Growth

By Sprint 10, project memory could be substantial. Mitigations:
- ARCHITECTURE.md is rewritten (not appended) — always reflects current state
- DECISIONS.md uses short entries — title + 2-3 sentence rationale
- Completed sprint details stay in their sprint dirs, not in working memory
- If this becomes insufficient, add a summarization step in retrospective

### 5. Git Branch Strategy

The inner loop creates branches per sprint. For the outer loop:
- Each sprint branch merges to a `develop` or `main` branch after completion
- The next sprint branches from the merged result
- If a sprint fails, its branch can be discarded without affecting previous work

## Implementation Strategy

### Phase 1: Minimal Outer Loop

1. `ProjectConfig` and `ProjectState` dataclasses
2. Quality bar as a first-class field in `ProjectConfig`
3. Sprint Planner agent (generates VISION.md + PRD.md for next sprint)
4. Retrospective agent (updates ARCHITECTURE.md + BACKLOG.md after each sprint)
5. Simple driver loop: assess → plan → execute → retrospect → human checkpoint
6. File-based memory only
7. Structured JSONL logging for all outer loop decisions

This is ~300-500 lines of new code + prompt templates. The inner loop is imported as-is.

### Phase 2: Project-Level Testing

1. Retrospective promotes completed verification scripts to `tests/regression/`
2. Run project-level test suite at start of each sprint (before inner loop)
3. Builder sees project-level test failures as P0
4. Retrospective identifies cross-sprint e2e journeys and creates `tests/e2e/` scripts
5. Security checks accumulate in `tests/security/`

### Phase 3: Project-Level Evaluation

1. Project Evaluator role — runs after every 2-3 sprints
2. Produces Project Health Report (vision alignment, quality assessment, gap analysis)
3. Sprint Planner reads health report when planning next sprint
4. Project dashboard (HTML report) generated after each sprint

### Phase 4: Autonomous Completion

1. Automatic termination criteria based on Project Evaluator + test suite
2. Remove human checkpoint requirement (optional)
3. "Are we done?" gate: all PROJECT_VISION requirements traced to passing tests

### Fork Strategy

Fork the repository before starting implementation. The inner loop must remain stable — it's the proven foundation. The outer loop should:
- Import `LoopConfig`, `LoopState`, `Agent`, `run_loop` from the inner loop package
- Add new modules (`project.py`, `retrospective.py`, `sprint_planner.py`)
- Add new prompt templates (`prompts/sprint_planner.md`, `prompts/retrospective.md`)
- Not modify any inner loop code

If the outer loop needs changes to the inner loop's interface, those should be minimal and backward-compatible (e.g., adding an optional `project_memory_dir` field to `LoopConfig`).
