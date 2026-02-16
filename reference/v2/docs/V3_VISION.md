# Loop V3: Vision-to-Value Algorithm

## Vision

Turn a Vision and PRD into **the outcome they promise** — with minimal human debugging, no babysitting, and near-zero post-loop cleanup.

The loop is not a code generator. It is not a software engineering tool. It is a **closed-loop value delivery system**. Given a description of what outcome a human wants (Vision) and what specifically must be true for that outcome to exist (PRD), the loop plans, executes, verifies, course-corrects, and repeats until the promised value is real — or honestly reports why it can't be delivered.

V3's primary focus is **software delivery** — web applications, CLI tools, APIs, integrations, system configurations. The architecture is designed to be extensible to non-software deliverables (documents, data pipelines, research analyses), but V3 validates its core algorithm against software first. Output-agnostic delivery is an architectural aspiration, not a V3 requirement.

A human provides two documents: a Vision and a PRD. That's it. They don't configure the toolchain, define test strategies, or specify the tech stack. The loop examines the Vision, the PRD, and any existing codebase or context, and **figures out what it needs** — what tools are available, what services to run, how to verify value, what the deliverable type is. The human provides the "what." The loop determines the "how."

## The Problem (Why V2 Fails)

V2 builds code, then discovers it doesn't work. It runs tests, discovers failures, but can't connect failures to root causes. It retries the same fixes blindly. It doesn't know if the user can actually use what was built. It doesn't know when it's stuck. A human must sit with it, diagnose issues, and intervene — defeating the purpose.

The root causes:
- **Build-then-test waterfall**: All code gets written before any tests run. Regressions compound silently.
- **Blind fix agents**: Tests fail, the fixer gets the error but not the history of what was already tried. It loops on the same failed approach.
- **No value awareness**: V2 knows "tests pass" but not "user can actually achieve the outcome." Function without value. The builder grades its own homework.
- **No pursuit of excellence**: Coding agents treat "tests pass + lint clean" as done. But a thing that works correctly can still be confusing, unintuitive, or unpleasant to use. No agent critically evaluates the actual user experience.
- **No self-diagnosis**: When stuck, V2 retries harder instead of changing strategy.
- **Fragile state management**: Agents edit markdown files with grep and sed. Formatting drift causes silent task skips.
- **Wrong model for the job**: Sonnet doing planning and critique work that requires Opus-level reasoning.
- **Software tunnel vision**: V2 assumes every sprint produces code. If the Vision calls for a document, a plan, or a migration — V2 has no framework for that.
- **Manual configuration burden**: The human must write a sprint config specifying tech stack, services, test frameworks. The loop should figure this out.
- **No graceful human handoff**: When the loop hits something only a human can do (OAuth, API key generation), it either fails, spins, or skips. There's no mechanism to pause, ask the human, verify, and resume.
- **Dead-end post-loop**: V2's final verification is outside the loop. If the final check discovers problems, there's no mechanism to fix them — the loop is already over. The most valuable check (fresh eyes on the whole deliverable) has no recourse.
- **Knowledge ceiling**: The loop can only use what's in the LLM's training data. When a library's API has changed, when there's a known bug with a workaround on GitHub Issues, when a newer approach exists — the loop has no way to discover this. It retries the same stale approach from its training data, burning iterations on a fix that can never work because the knowledge it needs doesn't exist in its weights.

## The Shift

**V2 (phase-driven, software-only, human-configured):**
Plan → Build all → Test all → Fix blindly → Hope it works → Human debugs the rest.
Builder grades own homework. "Tests pass" = done. Nobody asks "but is it actually good?"

**V3 (decision-driven, software-first, self-configuring):**
Discover context → Qualify feasibility → Execute one task → QC agent checks correctness → Catch regression → Fix with context → Research when knowledge is stale → Critical evaluator judges experience → Pause for human if needed → VRC: "Is the promised value real?" → Course correct if stuck → Repeat until value is delivered.
Separate agents for building, checking, and evaluating. The loop acquires external knowledge when its training data fails. It pursues excellence, not just correctness.

## Core Idea: The Loop Delivers Value, Not Just Working Code

The algorithm's core abstractions are deliverable-agnostic — the same concepts apply regardless of what is being produced:

| Concept | What It Means |
|---|---|
| **Vision** | The outcome a human was promised |
| **PRD** | The specific requirements that make the outcome real |
| **Task** | A unit of work that moves toward the outcome |
| **Deliverable** | Whatever artifact the Vision describes — code, document, data, config |
| **Quality Control** | Automated checks that the deliverable works correctly — tests, linting, type checks, static analysis |
| **Critical Evaluation** | A separate agent that *uses* the deliverable as a real user would and judges whether the experience actually delivers on the Vision |
| **Regression** | Checking that new work didn't break previous value |

These are not the same thing. Quality control asks "does it work?" Critical evaluation asks "is it good?" Both are required. Neither is sufficient alone.

V3 focuses on software deliverables. The architecture is designed so that the same abstractions *could* extend to other types — the table below illustrates how QC and Critical Evaluation map across deliverable types. Non-software types are **future extensions**, not V3 scope.

| Vision Describes | Deliverable Type | Quality Control | Critical Evaluation |
|---|---|---|---|
| A web application | Code + running services | Tests pass, lint clean, types check | Agent navigates the UI as a user, completes the promised workflow, evaluates the experience |
| A CLI tool | Code + executable | Commands produce correct output, edge cases handled | Agent runs the tool for its intended purpose, evaluates whether output is useful and clear |
| An API integration | Code + configuration | Endpoints respond correctly, error handling works | Agent exercises the integration end-to-end as a consuming application would |
| A system configuration | Config files + documentation | Config syntax valid, services start | Agent applies config and verifies the system actually behaves as intended |
| *A strategic document* | *Markdown/PDF* | *Structure complete, all PRD sections addressed* | *Agent reads as intended audience, evaluates whether actionable and convincing* |
| *A data migration* | *Scripts + transformed data* | *Data integrity checks, row counts, schema validation* | *Agent examines transformed data, verifies downstream purpose* |
| *A research analysis* | *Document + supporting data* | *Sources cited, methodology documented* | *Agent evaluates whether findings answer the research questions* |

*Italicized rows are architectural extensions, not V3-validated deliverable types.*

The pre-loop discovers what type of deliverable is needed and adapts both its quality control and critical evaluation strategies accordingly. For V3, this discovery targets software project types with strong automated QC signals (tests, linting, type checks). Extension to non-software types requires validating that QC and Critical Evaluation produce meaningful signals for those types (see Hypotheses H3 and H5).

## What the Loop Delivers

### 1. Self-Configuration ("The Discovery")
The human provides Vision + PRD. The loop examines them — along with any existing codebase, file structure, environment, and available tools — and **derives** what it needs to execute. What project type is this? What tools and frameworks are available? What services need running? How should value be verified? What does "done" look like for this specific deliverable?

This replaces the manual sprint config. The human describes the outcome; the loop figures out the execution environment. If the loop can't determine something critical (e.g., which database to use), it asks — but it asks specific questions, not "please fill out this config file."

### 2. Aggressive Pre-Qualification
Before executing a single task, the loop validates that the work is achievable. Opus critiques the PRD for feasibility, runs quality gates on the plan, verifies all external dependencies are available, and resolves or descopes every blocker. If the PRD asks for the impossible, the loop says so upfront — it doesn't discover it 50 iterations later.

### 3. Decision-Driven Delivery (Not Phases)
Each iteration, the loop asks "what should I do next?" based on current state — not "what phase am I in?" It can go from testing back to planning if the situation demands it. The decision engine is deterministic (no LLM needed) and follows a clear priority order: fix broken environment → unstick → fix failing QC checks → execute next task → run QC → run critical evaluation periodically → check if done.

### 4. Quality Control — Separate Agent, Continuous ("The Immune System")
The builder builds. A different agent checks the work. The builder never grades their own homework.

After every task, a QC agent runs the appropriate automated checks — unit tests, integration tests, linting, type checking, static analysis, whatever is relevant to the deliverable type. Previously-passing checks re-run (regression). If something breaks, the loop knows exactly which task caused it and fixes it immediately — not 20 tasks later when the damage is compounded.

For software, this is tests + linting + type checks. For documents, this is structure validation + completeness checks. For data, this is integrity checks + schema validation. The QC agent determines what's appropriate based on the deliverable type discovered in pre-loop. The checks are automated, fast, and run after every task. Non-negotiable.

But QC only answers "does it work correctly?" It says nothing about whether anyone would actually want to use it.

### 5. Critical Evaluation — The Real User Test ("The Beta Tester")
This is where the loop pursues excellence, not just correctness.

A separate Opus agent is spawned with one job: **be the user**. Not run tests. Not check code. Actually *use* the deliverable the way a real human (or consuming service) would, and critically evaluate whether it delivers a good experience that aligns with the Vision.

For a web app: the agent opens the browser, navigates the UI, tries to complete the workflow the Vision promises. Does the UI make sense? Are the interactions intuitive? Does the data flow correctly end-to-end? Could a real user figure this out without documentation?

For a CLI tool: the agent runs the tool for its intended purpose with realistic inputs. Is the output clear and useful? Are error messages helpful? Does the happy path feel natural?

For a document: the agent reads it as the intended audience would. Is it convincing? Is it actionable? Does it answer the questions it claims to? Would the reader trust these conclusions?

For an API: the agent exercises it as a consuming application would. Does the contract make sense? Are responses useful? Does the integration feel solid?

This is not a checklist. It's a critical evaluation with judgment. The agent is trained to be demanding — to represent the user who was promised something in the Vision and to honestly assess whether what was built lives up to that promise. Issues found become new tasks automatically.

The distinction matters: QC catches bugs. Critical evaluation catches "technically works but nobody would want to use it." Both are required. Current coding agents stop at QC. This loop doesn't.

### 6. VRC Heartbeat ("The Compass")
The Vision Reality Check runs every iteration. Not a checkpoint — a continuous pulse. "How much of the promised value have we actually delivered?" Quick checks (Haiku, cheap) track concrete metrics: task completion count, test pass rate delta since last check, active blocker count, and budget consumption percentage. Deep checks (Opus, every 5th iteration) assess quality — reading the actual deliverable state and judging whether it's converging on the Vision's promise. The loop always knows where it stands relative to the Vision.

When the decision engine believes all tasks are complete and verifications pass, the VRC becomes the **exit gate**. But not a rubber stamp — a fresh-context, Opus-level scrutiny of the entire deliverable against the Vision. If the exit VRC finds gaps, those gaps become tasks, and the loop continues. The loop doesn't exit into a "post-loop" that can fail with no recourse. It exits only when value is verified — or when it honestly determines it cannot deliver and reports why.

### 7. Interactive Pause ("The Handoff")
Autonomy is the goal, but not at the cost of delivery. Some blockers only emerge during execution — the loop builds an OAuth UI, but a human must complete the browser auth flow to get a token. The loop builds an integration, but an API key needs to be generated from an external dashboard. These aren't failures. They're expected collaboration points.

When the loop encounters something it genuinely cannot do itself, it doesn't die, spin, or silently skip ahead. It **pauses with purpose**:

1. **Recognize** — The loop identifies that it needs a human action (not a code fix, not a retry — a genuine human-only step).
2. **Instruct** — It tells the human exactly what to do, in clear non-technical language. Not "set GOOGLE_OAUTH_TOKEN in .env" but "Open the app in your browser, click 'Connect Google Account', and complete the sign-in."
3. **Wait** — The loop pauses. It doesn't burn tokens or spin. It saves state and waits for the human to signal they've completed the action.
4. **Verify** — Before resuming, the loop verifies the action actually worked (token exists and is valid, API key returns 200, etc.). If it didn't work, it tells the human what went wrong and waits again.
5. **Resume** — The loop picks up exactly where it left off, autonomously.

The key insight: the loop should **front-load work** to minimize pause points. Build everything that doesn't need the token first. Group human actions together where possible. A well-planned sprint might need only one or two pauses total, not one per task.

Interactive Pause is not course correction. It's not escalation. It's the loop being smart enough to know that 5 minutes of human action can unblock 2 hours of autonomous delivery — and that blocking on it is better than working around it.

**Progressive Trust**: The loop doesn't demand full autonomy from day one. Early sprints include more human touchpoints — the loop presents its plan for approval, shows intermediate results after the first few tasks, and asks "is this heading in the right direction?" before investing the full budget. As the human gains confidence in the loop's judgment, these check-ins can be reduced or disabled. Trust is earned through demonstrated competence, not assumed by default.

### 8. Course Correction ("The Self-Diagnosis")

When the loop is stuck — same failures repeating, no progress for N iterations — it doesn't retry harder. Opus diagnoses WHY it's stuck and changes strategy: restructure the plan, descope unachievable items, change approach, or escalate to a human with a clear explanation of the problem.

### 9. External Research ("The Deep Dive")

LLMs have a knowledge ceiling. Their training data has a cutoff. Libraries change APIs. Frameworks deprecate patterns. Known bugs get workarounds that only exist in GitHub Issues or Stack Overflow threads posted after the training cutoff. When the loop encounters a problem it can't solve with its built-in knowledge, retrying harder is futile — it needs to go outside and learn.

The Research Agent is an Opus agent with web search and documentation retrieval tools. It doesn't guess. It searches. When triggered:

1. **Identify the knowledge gap** — What specific question can't the loop answer from its training data? "Why does `google.adk.Agent` raise `TypeError` with this config?" not "something is broken."
2. **Search broadly** — Web search for the error, the library's current docs, its GitHub issues, its changelog. Look for breaking changes, migration guides, known bugs with workarounds.
3. **Synthesize findings** — Produce a focused research brief: what changed, what the current correct approach is, what workarounds exist. Not a dump of URLs — actionable intelligence.
4. **Inject into context** — The research brief becomes part of the fix agent's context on the next attempt. The loop now has knowledge it didn't have before.

Research triggers automatically when:
- Fix attempts are exhausted on a root cause (the loop tried N times and failed — maybe the knowledge is wrong)
- Course correction identifies a knowledge gap (the diagnosis is "we don't know how to do this")
- A builder or fixer explicitly flags uncertainty about a library or API

Research can also escalate to **human insight** as a last resort. This is different from Interactive Pause (which is about human *actions* — signing in, generating keys). Human insight is about human *knowledge* — "we've researched this and can't find the answer; here's what we've tried; can you point us in the right direction?" The loop presents what it knows, what it's tried, and what specifically it needs to know. The human provides guidance, and the loop resumes.

The key insight: research is not a failure mode. It's the loop being intelligent enough to recognize that its built-in knowledge is insufficient and actively acquiring what it needs. A developer who never reads docs or searches for solutions is a bad developer. The same is true for an autonomous loop.

### 10. Structured State (No Markdown Editing)
JSON is the single source of truth. Agents communicate through typed tool calls (`add_task`, `report_task_complete`, `report_vrc`), not by editing markdown with grep. Human-readable plans and checklists are rendered from state on demand. No formatting drift, no silent task skips, no dual-source-of-truth bugs.

### 11. Right Model — and Right Agent — for the Job
Different concerns require different agents with different capabilities and different models. This isn't just cost optimization — it's separation of concerns. The builder shouldn't evaluate its own work. The critic shouldn't be constrained by the builder's assumptions.

| Agent Role | Model | What It Does | Why This Model |
|---|---|---|---|
| **Planner** | Opus | Plans tasks, critiques PRD, runs quality gates | Requires strategic reasoning |
| **Builder** | Sonnet | Executes tasks, writes code/content, fixes issues | Volume work, follows plan |
| **QC Agent** | Sonnet/Haiku | Runs tests, linting, type checks, regression | Automated checks, fast feedback |
| **Critical Evaluator** | Opus | *Uses* the deliverable as a real user, judges experience quality | Requires judgment, taste, Vision-awareness |
| **VRC Agent** | Haiku (quick) / Opus (full) | Tracks progress metrics, assesses value delivery | Quick checks cheap; deep checks need judgment |
| **Course Corrector** | Opus | Diagnoses why the loop is stuck, changes strategy | Requires diagnostic reasoning |
| **Research Agent** | Opus | Searches web, reads current docs, synthesizes findings into actionable briefs | Requires judgment about source quality, relevance, and how to apply findings |

The critical evaluator is Opus deliberately. Evaluating whether something delivers a *good experience* requires the same level of judgment as planning it. A Sonnet-level agent will say "it works" and move on. An Opus-level agent will say "it works, but the error messages are confusing, the navigation is unintuitive, and the user would get lost at step 3." That's the difference between delivering function and delivering value.

## What the Loop Does NOT Do

- **Perform human-only actions itself** — OAuth flows, API key generation, external account creation. But it doesn't just fail either — it pauses, instructs the human, verifies completion, and resumes (see Interactive Pause).
- **Make product decisions** — The Vision and PRD define what to deliver. The loop can push back on feasibility, but it delivers what's asked.
- **Deploy to production** — The loop delivers locally-verified value. Deployment is a separate concern.
- **Replace human judgment on scope** — The loop can suggest descoping but won't unilaterally cut deliverables without reporting.
- **Guess what the human wants** — The Vision must exist. Without it, there's nothing to deliver against.
- **Rely solely on training data** — When built-in knowledge is wrong or stale, the loop researches externally. But it researches to solve specific problems, not to learn entire domains from scratch.

## How It Works (User's Perspective)

```
1. Human writes VISION.md    ("What outcome do we want?")
2. Human writes PRD.md        ("What specifically must be true?")
3. Human runs the loop         (one command, points at a sprint directory)
4. Loop discovers context      (examines codebase, environment, tools available)
5. Loop qualifies the work     (PRD critique, feasibility, blocker resolution)
6. Loop executes iteratively   (task → verify → regress → fix → VRC → repeat)
   6a. If the loop needs a human action (OAuth, API key, etc.):
       → Loop pauses with clear instructions
       → Human completes the action
       → Loop verifies and resumes
   6b. If the loop's knowledge is insufficient (stale API, unknown bug):
       → Research agent searches web, reads current docs, GitHub issues
       → Synthesizes findings into actionable brief
       → Fix agent retries with new knowledge
       → If still stuck, asks human for insight
   6c. When all tasks complete:
       → Fresh-context exit gate (full VRC + regression + critical eval)
       → If gaps found → new tasks, back to 6
       → If verified → exit
7. Loop delivers report        (what was delivered, what was descoped, final score)
8. Human has the outcome
```

Step 3 is not "Human writes sprint_config.py with 50 lines of configuration."
Step 6a is not "Human debugs a crash" — it's "Human completes an action only a human can do" (sign in, generate a key, approve access). The loop tells them exactly what to do, verifies it worked, and resumes autonomously.
Step 6b is not "Human debugs a library incompatibility" — the loop goes and finds the answer itself. Only if research truly fails does it ask the human for a specific piece of knowledge.
Step 8 is not "Human has working software" — it's "Human has the outcome." The outcome is whatever the Vision promised.

No step 4.5 where the human fills out a config file.
No step 5.5 where the human SSH's in to debug a crashed service.
No step 6.5 where the human reads test output and tells the loop what to fix.
No step 7.5 where the human manually tests because "tests pass but nothing works." (Minor cosmetic issues may remain — the loop catches critical and functional gaps, not every pixel.)

## Architecture

```
                         ┌─────────────────────┐
                         │   Human provides:    │
                         │  VISION.md + PRD.md  │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │         PRE-LOOP               │
                    │                                │
                    │  Context Discovery (Opus)      │
                    │    → examine codebase, env     │
                    │    → derive sprint context     │
                    │    → determine deliverable type│
                    │                                │
                    │  PRD Critique (Opus)            │
                    │  Plan Generation (Opus)         │
                    │  Quality Gates (Opus)           │
                    │  Blocker Resolution             │
                    │  Preflight                      │
                    │                                │
                    │  "Is this achievable?"          │
                    └───────────────┬───────────────┘
                                    │ yes
                    ┌───────────────▼───────────────┐
                    │       THE VALUE LOOP           │
                    │                                │
                    │  ┌──────────────────────┐      │
                    │  │   Decision Engine     │     │
                    │  │   "What next?"        │     │
                    │  └──────────┬───────────┘     │
                    │             │                  │
                    │  ┌──────── ▼ ────────┐        │
                    │  │ EXECUTE → VERIFY   │        │
                    │  │ REGRESS → FIX      │        │
                    │  │ RESEARCH (ext. kb)  │        │
                    │  │ CRITICAL EVAL       │        │
                    │  │ COURSE CORRECT      │        │
                    │  │ INTERACTIVE PAUSE   │        │
                    │  └──────┬─────────────┘        │
                    │         │                      │
                    │  ┌──────▼──────────┐           │
                    │  │ VRC Heartbeat    │           │
                    │  │ "Value delivered?"│           │
                    │  └──────┬──────────┘           │
                    │         │ no → loop             │
                    │         │                      │
                    │  ┌──────▼──────────────┐       │
                    │  │ All tasks done?      │       │
                    │  │ yes → EXIT GATE      │       │
                    │  │                      │       │
                    │  │ Fresh-context VRC    │       │
                    │  │ (Opus, full sweep)   │       │
                    │  │ Full regression      │       │
                    │  │ Final critical eval  │       │
                    │  │                      │       │
                    │  │ Pass? → EXIT         │       │
                    │  │ Fail? → new tasks    │       │
                    │  │         → loop       │       │
                    │  └──────┬──────────────┘       │
                    │         │                      │
                    └─────────┼──────────────────────┘
                              │ value verified
                    ┌─────────▼──────────────┐
                    │    DELIVERY REPORT      │
                    │                         │
                    │  What was delivered      │
                    │  What was descoped (why) │
                    │  What needs human action │
                    │  Final value score       │
                    └─────────────────────────┘
```

The loop has exactly **one exit**: verified value. There is no "post-loop" that can fail with no recourse. The exit gate is inside the loop — if it finds gaps, those become tasks and the loop continues. The only output after exit is the delivery report, which is a summary of what was already verified.

## Integration Architecture

The 7 agent types don't operate as independent services — they are roles played by a single orchestrator process that spawns agent sessions as needed. This section describes how they compose.

### State Sharing

All agents read from and write to a single **LoopState** object (JSON-serialized). No agent holds private state that other agents need. The state includes:

- **Task list** — all tasks with status, dependencies, ownership, and provenance
- **VRC history** — all value reality check scores over time
- **QC results** — test/lint/type-check outcomes per task
- **Agent results** — structured output from the most recent agent session of each type
- **Iteration counter and budget** — how many iterations have elapsed, how much budget remains

Agents access state through typed tool calls (`manage_task`, `report_vrc`, `report_qc`). No agent reads or writes state directly. The orchestrator validates every state mutation before applying it (see Task Mutation Guardrails in the implementation plan).

### Inter-Agent Communication Protocol

Agents don't talk to each other. They talk to the **Decision Engine**, which is a deterministic function (no LLM) that reads state and decides what to do next. The flow:

1. Decision Engine reads current state → selects next action (e.g., "run QC", "execute task 5", "run critical eval")
2. Orchestrator spawns the appropriate agent session with role-specific tools and context
3. Agent executes, producing structured output via tool calls that modify state
4. Agent session ends. Decision Engine re-evaluates state. Repeat.

No agent assumes another agent will run after it. No agent produces output that only one other agent can consume. All agent output is structured state that any role can read.

### Conflict Resolution

When agents produce contradictory signals:

| Conflict | Resolution |
|---|---|
| QC passes but Critical Evaluator flags issues | Critical Evaluator wins — issues become tasks. QC checks correctness; Critical Eval checks value. Both signals are valid. |
| VRC says value delivered but exit gate finds gaps | Exit gate wins — it has fresh context and full-sweep authority. Gaps become tasks. |
| Course Corrector restructures plan but new tasks fail validation | Task Mutation Guardrails reject invalid mutations. Course Corrector must produce valid tasks or the mutation is discarded with an error logged. |
| Research Agent produces findings that contradict builder's approach | Research findings are injected as structured context (what changed, what the correct approach is now, code examples if available), not as directives. The builder/fixer decides how to apply them. If the fix still fails, course correction triggers. |

The general principle: **downstream agents can override upstream agents, but never silently.** Every override is logged in state with rationale.

### Error Propagation

Agent sessions can fail (timeout, token limit, API error, malformed output). The orchestrator handles this:

1. **Retryable failures** (API timeout, rate limit) — retry with exponential backoff, up to 3 attempts
2. **Non-retryable failures** (malformed output, tool call rejected) — log the failure, mark the action as failed in state, let the Decision Engine re-evaluate (which will likely trigger course correction)
3. **Budget exhaustion** — the agent ran out of turns without completing. Log partial results, let Decision Engine handle

No failure silently disappears. Every failure is visible in state and influences the Decision Engine's next decision.

## Success Criteria

### User Outcomes (what changes for the human)

- Human provides Vision + PRD, runs one command — the loop handles the rest autonomously
- Human involvement is limited to: writing Vision/PRD, starting the loop, and completing actions only a human can do
- When human action is genuinely required (OAuth, API keys), the loop pauses with clear instructions, verifies completion, and resumes — no debugging, no guessing
- Loop either delivers the promised outcome or clearly reports what it couldn't deliver and why
- Post-exit debugging reduced by >90% compared to V2 — critical issues caught before exit; cosmetic issues may remain. The goal is near-zero, not absolute zero
- Value is verified from the user's perspective (critical evaluation), not just individual requirements
- The loop pursues excellence: a separate agent critically evaluates the experience, not just correctness — "it works" is necessary but not sufficient
- Total cost (Opus + Sonnet + Haiku tokens) is bounded by a configurable budget ceiling with graceful degradation (see Cost Model)
- As a last resort, the loop can ask the human for insight (not action) with a clear description of what it's tried and what it needs to know

### System Capabilities (what the loop can do)

- Loop discovers what it needs (tech stack, tools, verification strategy) from context — with config file as co-equal fallback (see H2)
- Exit gate is inside the loop — if the final fresh-context VRC finds gaps, they become tasks, not a failure report
- Regressions detected within 1 iteration of being introduced
- Loop recognizes when it's stuck and changes strategy (not infinite retry)
- Delivers software deliverables reliably (web apps, CLI tools, APIs, integrations, configs). Architecture supports future extension to non-software types once core hypotheses are validated
- Same algorithm handles a single-task sprint or a 50-task multi-phase sprint
- When the loop's built-in knowledge is insufficient (stale APIs, unknown bugs), it researches externally — web search, current docs, GitHub issues — rather than retrying blindly with stale knowledge

## Cost Model

The loop uses multiple model tiers. Cost is driven by iteration count and which agents run per iteration. This section provides estimates and describes the bounding mechanism.

### Token Estimates Per Agent Session

| Agent Role | Model | Estimated Input Tokens | Estimated Output Tokens | Est. Cost Per Session |
|---|---|---|---|---|
| **Planner** | Opus | 30-50K | 5-15K | $0.60-$1.50 |
| **Builder** | Sonnet | 20-40K | 5-20K | $0.15-$0.45 |
| **QC Agent** | Sonnet | 10-20K | 2-5K | $0.06-$0.15 |
| **Critical Evaluator** | Opus | 30-50K | 5-10K | $0.60-$1.20 |
| **VRC (quick)** | Haiku | 5-10K | 1-2K | $0.01-$0.02 |
| **VRC (full)** | Opus | 20-40K | 5-10K | $0.45-$0.90 |
| **Course Corrector** | Opus | 30-50K | 5-15K | $0.60-$1.50 |
| **Research Agent** | Opus | 30-60K | 5-15K | $0.60-$1.65 |

*Estimates assume Opus at $15/$75 per 1M input/output tokens, Sonnet at $3/$15, Haiku at $0.80/$4. Actual costs depend on context length and caching.*

### Per-Iteration Cost Profile

A typical iteration (execute task → QC → VRC quick) costs approximately **$0.22-$0.62**. Iterations that trigger critical evaluation, course correction, or research cost **$1.00-$3.00+**.

### Sprint Cost Ranges

| Sprint Complexity | Est. Iterations | Est. Total Cost | Notes |
|---|---|---|---|
| Simple (5-10 tasks) | 15-30 | $5-$20 | Few regressions, no course corrections |
| Medium (10-25 tasks) | 30-75 | $20-$75 | Some regressions, 1-2 course corrections |
| Complex (25-50 tasks) | 75-200 | $75-$250 | Multiple regressions, research triggers, course corrections |

**Note**: These estimates assume Claude API pricing. When running via Claude Max subscription, the cost is the subscription fee regardless of token usage — making cost predictability inherent.

### Budget Ceiling Mechanism

The loop enforces a configurable **iteration budget** (not a dollar amount — iteration count is the controllable variable):

1. **Budget is set at sprint start** — derived from task count and complexity estimate, or explicitly configured
2. **VRC tracks budget consumption** — every iteration, the VRC heartbeat reports remaining budget as a percentage
3. **At 80% budget consumed**: the loop enters **efficiency mode** — critical evaluation frequency decreases, VRC switches to quick-only, research triggers require higher confidence threshold
4. **At 95% budget consumed**: the loop enters **wrap-up mode** — no new tasks created, focus on completing highest-value in-progress tasks and running exit gate
5. **At 100% budget consumed**: the loop exits with a **partial delivery report** — what was delivered, what remains, why budget was exhausted. This is an honest report, not a failure

Cost is a VRC dimension: "Is value being delivered within budget?" A sprint that delivers 80% of value at 50% of budget is healthier than one that delivers 100% at 200%.

## Hypotheses and Validation Plan

The Vision makes several claims that are **hypotheses, not established facts**. These are the assumptions most critical to V3's success — and the ones with the least evidence. Each must be validated early, before full investment. If a hypothesis is refuted, the Vision must adapt (scope reduction, alternative approach, or feature removal) rather than ignoring the evidence.

### H1: LLM-as-Experience-Evaluator

**Claim**: An Opus agent can meaningfully simulate a real user's experience and produce valid quality judgments that improve the deliverable beyond what automated testing catches.

**Why it matters**: This is the core of "pursues excellence, not just correctness." If the Critical Evaluator produces generic, misaligned, or unhelpful feedback, it's an expensive token sink that bloats iteration count without adding value.

**Evidence today**: None. No prototype, no benchmark, no comparison with human evaluation.

**Validation experiment**: Before building the full Critical Evaluator, run a **calibration spike**:
1. Take 3 deliverables of known quality (one good, one mediocre, one poor — as judged by a human)
2. Have the Opus evaluator assess each, producing specific issues
3. Compare evaluator findings against human assessment
4. **Pass criteria**: Evaluator identifies >70% of human-flagged issues and <30% of its findings are false positives (things the human considers fine)

**If refuted**: Descope Critical Evaluation to a simpler checklist-based assessment (accessibility, error handling completeness, documentation coverage) rather than subjective UX judgment. Or: make Critical Evaluation human-assisted — the evaluator identifies areas of concern, a human reviews and confirms/dismisses.

### H2: Auto-Discovery of Execution Context

**Claim**: The loop can examine a Vision, PRD, and existing codebase to automatically determine the correct tech stack, verification strategy, deliverable type, and execution environment — without the human writing a config file.

**Why it matters**: This is the "one command" promise. If auto-discovery fails, the human is back to writing configurations — and correcting wrong auto-discoveries is worse than writing configs from scratch.

**Evidence today**: None. Mechanism not described.

**Validation experiment**: Run the **discovery-vs-config spike**:
1. Take 5 real projects of varying complexity (greenfield, existing codebase with tests, existing codebase without tests, monorepo, multi-language)
2. For each: have a human write the ideal sprint config, then have the auto-discovery produce its config
3. Compare: accuracy of tech stack detection, test framework identification, service requirements, deliverable type classification
4. **Pass criteria**: Auto-discovery matches human config on >80% of projects. For projects where it fails, the fallback (asking specific questions) resolves ambiguity in <3 questions

**If refuted**: Ship auto-discovery as a **suggestion** that the human confirms/corrects in 30 seconds, not as a replacement for configuration. Provide a config file option from day 1 — not as a "power user" afterthought but as a co-equal path.

### H3: Output-Agnostic Algorithm

**Claim**: The same algorithm (plan → execute → QC → critical eval → VRC → course correct) works for arbitrary deliverable types, not just software.

**Why it matters**: This is the generality claim that distinguishes V3 from "a better coding agent."

**Evidence today**: None. The algorithm's QC and Critical Evaluation mechanisms are well-defined only for software (tests, linting, type checks). For documents, data pipelines, and configurations, the quality signals are undefined.

**Validation experiment**: **Defer to post-V3.** V3 validates the algorithm for software. Once the core loop is proven, run a **non-code spike**:
1. Give the loop a Vision for a strategic document (not code)
2. Assess: Does QC produce meaningful checks? Does Critical Evaluation produce useful feedback? Does VRC track value?
3. **Pass criteria**: The deliverable is at least comparable in quality to what a human would produce with the same time investment

**If refuted**: V3 is a software delivery system. Output-agnostic is a V4+ aspiration. Remove from V3 claims.

### H4: VRC for Arbitrary Deliverables

**Claim**: The VRC agent can meaningfully assess "how much of the promised value has been delivered" across different deliverable types.

**Why it matters**: VRC is the exit gate. If VRC can't meaningfully score value delivery, the loop either exits too early (unverified value) or too late (burning tokens on a loop that's already done).

**Evidence today**: None. For software with tests, VRC can count coverage and passing tests. For everything else, "value delivered" is subjective.

**Validation experiment**: Combined with H3 validation. For software: validate that VRC's value score correlates with human assessment of "is this done?" For non-software: deferred to post-V3.

**If refuted (for software)**: Replace subjective VRC scoring with a **checklist VRC** — did each PRD requirement's acceptance criteria pass? Binary yes/no per requirement, percentage complete overall. Less nuanced but more reliable.

### H5: Multi-Agent Orchestration Reliability

**Claim**: Seven agent types (Planner, Builder, QC, Critical Evaluator, VRC, Course Corrector, Research) can be orchestrated into a reliable system via the Decision Engine + shared state architecture.

**Why it matters**: This is the master assumption. Every other hypothesis assumes the orchestration works. If agents produce emergent coordination failures (stepping on state, conflicting directives, cascading errors), the loop is worse than a single-agent approach.

**Evidence today**: None. No prototype, no reference architecture for this specific combination.

**Validation experiment**: **Incremental composition spike**:
1. **Phase 1** (3 agents): Builder + QC + Decision Engine. Run 5 real sprints with just these three. Measure: state corruption incidents, decision engine errors, regressions caught vs. missed
2. **Phase 2** (5 agents): Add VRC + Course Corrector. Run 5 more sprints. Measure: does VRC add value? Does course correction trigger correctly?
3. **Phase 3** (7 agents): Add Critical Evaluator + Research Agent. Run 5 more sprints. Measure: do these add value proportional to their cost?
4. **Pass criteria**: Each phase produces measurably better outcomes than the previous. No phase introduces more coordination failures than value

**If refuted at Phase 1**: The entire multi-agent architecture is wrong. Fall back to a single-agent loop with structured prompting (essentially V2 with better state management).
**If refuted at Phase 2**: Ship with 3 agents. VRC and course correction become manual (human reviews progress, human redirects when stuck).
**If refuted at Phase 3**: Ship with 5 agents. Critical evaluation is human-only. Research is manual.

The incremental approach is critical — it means partial refutation doesn't kill the entire project. Each phase is independently valuable.

## Risks and Mitigations

This section addresses the most likely failure modes identified during Vision Validation. These are not hypothetical — they are the specific ways V3 is most likely to fail, based on analysis of V2's history, the architecture's complexity, and common failure patterns in multi-agent systems.

### Risk 1: Orchestration Complexity ("The Integration Monster")

**What could happen**: Seven agent types, multiple models, typed tool calls, JSON state, decision engine, VRC heartbeat, interactive pause, research agent — the integration complexity overwhelms development. Each component works in isolation but composing them produces emergent failure modes: agents corrupting shared state, decision engine making wrong priority calls, VRC disagreeing with Critical Evaluator. Debugging the loop becomes harder than debugging V2.

**Likelihood**: High. This is the most likely failure mode.

**Mitigation — Incremental Agent Addition**:
- Do NOT build all 7 agents simultaneously. Follow the H5 validation phases:
  - **MVP** (Sprint 1): Builder + QC + Decision Engine only. Ship this. It's already better than V2.
  - **+VRC +Course Correction** (Sprint 2): Add value tracking and self-diagnosis. Ship.
  - **+Critical Eval +Research** (Sprint 3): Add the ambitious differentiators. Ship.
- Each phase is a shippable product. If Phase 2 orchestration fails, Phase 1 still works.
- Integration tests between agents run at every phase boundary, not just at the end.

**Mitigation — Decision Engine Simplicity**:
- The Decision Engine is deterministic — no LLM, no learning, no adaptation. A pure function from state to action. This makes it debuggable and predictable.
- If the Decision Engine has bugs, they are reproducible (same state → same bug), unlike LLM judgment errors.

### Risk 2: Auto-Discovery Failure ("Harder Than Config Files")

**What could happen**: The self-configuration step gets it wrong for existing codebases (the most common case). Wrong test runner, wrong tech stack, missing environment requirements. Users spend more time correcting auto-discovery than they would have spent writing a config file.

**Likelihood**: High for existing codebases. Low for greenfield projects.

**Mitigation — Config File as Co-Equal Path**:
- Auto-discovery is a convenience, not a requirement. From day 1, provide a `sprint_config.yaml` option.
- Auto-discovery produces a *proposed* config that the user can review and approve in 30 seconds. Not a black box.
- If auto-discovery confidence is below a threshold, it presents the proposed config for confirmation rather than proceeding silently.

**Mitigation — Graduated Discovery**:
- Start with high-confidence signals only: package.json → Node.js, requirements.txt → Python, Cargo.toml → Rust
- Do NOT attempt to infer architectural patterns, test conventions, or implicit decisions from code structure. These are config-file territory.
- Expand discovery scope only as confidence models improve with real-world usage data.

### Risk 3: Unbounded Token Costs ("The Runaway Meter")

**What could happen**: The loop iterates until value is verified. Complex sprints run 80+ iterations with Opus at planning, evaluation, VRC, course correction, and research. A single sprint costs $50-200+. Users with budget constraints stop using the loop for non-trivial work.

**Likelihood**: Moderate. Exacerbated by false-positive Critical Evaluator findings (see Risk 4).

**Mitigation — Budget Ceiling** (see Cost Model):
- Configurable iteration budget with efficiency mode (80%) and wrap-up mode (95%)
- Partial delivery reports at budget exhaustion — honest about what's done and what remains

**Mitigation — Cost as VRC Dimension**:
- VRC tracks cost-per-value-delivered, not just value-delivered
- If cost/value ratio deteriorates (spending more per iteration for less progress), trigger course correction early

**Mitigation — Claude Max Subscription**:
- For the primary use case (personal/small-team), Claude Max subscription makes per-token cost irrelevant. The budget ceiling still matters for time (iteration count), but dollar cost is fixed.

### Risk 4: Critical Evaluator Token Sink ("The Useless Critic")

**What could happen**: The Opus evaluator produces generic feedback ("error messages could be clearer"), subjective feedback misaligned with user preferences, or false positives. It adds 30-40% token cost and creates low-value tasks that bloat iteration count. Users configure it to "skip."

**Likelihood**: Moderate-High. LLMs are better at structured analysis than subjective taste.

**Mitigation — Calibration Before Deployment**:
- Run H1 validation spike before enabling Critical Evaluation in production. If it fails the spike, don't ship it.

**Mitigation — Configurable Aggressiveness**:
- Critical Evaluator has a configurable threshold: `critical_eval_severity = "blocking" | "major" | "all"`
- Default to "blocking" (only flag issues that would prevent a user from completing the core workflow)
- Users can increase sensitivity if they want more polish

**Mitigation — Human Override**:
- Critical Evaluator findings are presented as suggestions, not mandates
- The human can dismiss findings via Interactive Pause if the evaluator is wrong
- Dismissal patterns feed back into future evaluations (the evaluator learns what this user considers important)

### Risk 5: Vision/PRD Quality Bottleneck ("Garbage In, Garbage Out")

**What could happen**: Users write vague Visions and incomplete PRDs. The loop technically delivers what was described but it doesn't match what the user actually wanted. Users blame the loop.

**Likelihood**: High. Most users are better at recognizing what they want than specifying it upfront.

**Mitigation — Vision Validation Gate**:
- Before any execution, the loop runs a 5-pass Vision Validation that challenges assumptions, tests causal logic, and identifies gaps. If the Vision is vague, the gate catches it before tokens are burned.

**Mitigation — PRD Quality Rubric**:
- The PRD Critique (pre-loop) evaluates not just feasibility but completeness. Missing acceptance criteria, ambiguous requirements, and untestable claims are flagged for revision.
- Provide PRD templates with examples for common project types.

**Mitigation — Early Feedback Loop**:
- After the first 3-5 tasks are complete, present intermediate output to the human for directional feedback. "Is this heading in the right direction?" Catching misalignment at 10% completion is cheap. Catching it at 90% is catastrophic.

### Risk 6: Model Provider Dependency

**What could happen**: Claude API pricing changes, model capabilities shift across tiers, context windows change, models are deprecated. The carefully tuned model-to-role mapping breaks.

**Likelihood**: Certain (over 18+ months). Model evolution is continuous.

**Mitigation — Role-Based Abstraction**:
- The architecture maps roles to capability requirements (strategic reasoning, volume work, quick classification), not to specific model names.
- `AgentRole` enum specifies required capabilities. Model assignment is a configuration lookup, not hardcoded.
- When a new model generation ships, updating the role→model mapping is a config change, not an architecture change.

### Compounding Risks

These risks are not independent. They compound:

- **Complexity × Cost**: More agents = more orchestration complexity = more iterations to debug = higher cost
- **Ambition × Adoption**: Over-promising (output-agnostic, zero debugging) × under-delivering (evaluator useless, discovery wrong) = user distrust
- **Input Quality × Evaluation Quality**: Vague Vision + imprecise evaluator = the loop and the user are both confused about what "done" means

The incremental development approach (H5 phases) is the primary defense against compounding risks. Each phase reduces uncertainty before the next phase adds complexity.
