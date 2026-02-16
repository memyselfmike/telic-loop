# Loop V2: Closed-Loop Autonomous Sprint Delivery

**Status**: Design Document
**Goal**: A truly closed-loop system that delivers production-ready, fully tested implementations of sprint visions

---

## Problem Statement

The current loop system is **linear**, not **closed-loop**:

```
plan → build → beta-plan → beta-test → ???
```

Issues discovered:
1. **Planning doesn't verify completeness** - Tasks get marked done but routes don't exist
2. **Build doesn't verify integration** - Components built in isolation, not wired together
3. **Beta-test doesn't feed back** - Finds gaps but doesn't create new tasks
4. **Quality gates not enforced** - CRAAP, CLARITY, etc. exist but aren't in the loop
5. **Project-specific hardcoding** - Prompts have EtsyBot-specific checks

---

## Design Goals

1. **Closed-loop**: Every phase feeds back to earlier phases when gaps found
2. **Project-agnostic**: Works for any project, any sprint - reads from docs
3. **Quality-gated**: Built-in CRAAP, CLARITY, VALIDATE, CONNECT, TIDY gates
4. **Self-healing**: Discovers missing pieces and creates tasks to fix them
5. **Production-ready output**: Not just "compiles" but "works end-to-end"

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SPRINT DELIVERY LOOP V2                               │
│                                                                          │
│  ╔═══════════════════════════════════════════════════════════════════╗  │
│  ║  VISION REALITY CHECK (VRC) - THE NORTH STAR                      ║  │
│  ║  "Can a human use this RIGHT NOW to achieve the VISION outcome?"  ║  │
│  ║  Runs after each phase. Course-corrects toward usable value.      ║  │
│  ╚═══════════════════════════════════════════════════════════════════╝  │
│         ↓                ↓                 ↓                ↓            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 0: VISION & PRD (Human-Driven)                             │   │
│  │                                                                   │   │
│  │   User creates/approves:                                         │   │
│  │   • VISION.md - What we're building and why                      │   │
│  │   • PRD.md - Detailed requirements                               │   │
│  │   • ARCHITECTURE.md - Technical decisions                        │   │
│  │                                                                   │   │
│  │   Gate: Human approval required to proceed                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              ↓                                           │
│                        ┌─────────┐                                      │
│                        │  VRC:   │ "Does VISION define a usable         │
│                        │ Check 1 │  outcome clearly?"                   │
│                        └─────────┘                                      │
│                              ↓                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 1: PLANNING (Quality-Gated Loop)                           │   │
│  │                                                                   │   │
│  │   ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌─────────┐        │   │
│  │   │ Generate│ → │ CRAAP   │ → │ CLARITY  │ → │VALIDATE │        │   │
│  │   │  Plan   │   │ Review  │   │ Protocol │   │ Sprint  │        │   │
│  │   └─────────┘   └─────────┘   └──────────┘   └─────────┘        │   │
│  │        ↑              │             │              │             │   │
│  │        │              ↓             ↓              ↓             │   │
│  │        └──────── ISSUES FOUND? ─────────────────────             │   │
│  │                       │                                          │   │
│  │                       ↓ All Pass                                 │   │
│  │   ┌──────────┐   ┌──────────┐                                   │   │
│  │   │ CONNECT  │ → │  TIDY    │ → Plan Ready                      │   │
│  │   │ Review   │   │  FIRST   │                                   │   │
│  │   └──────────┘   └──────────┘                                   │   │
│  │                                                                   │   │
│  │   Output: IMPLEMENTATION_PLAN.md (refined, validated)            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              ↓                                           │
│                        ┌─────────┐                                      │
│                        │  VRC:   │ "Does this plan deliver the VISION?  │
│                        │ Check 2 │  What's the critical path to value?" │
│                        └─────────┘                                      │
│                              ↓ (may reorder/reprioritize plan)          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 2: BUILD (Implement + Test Loop)                           │   │
│  │                                                                   │   │
│  │   For each task in IMPLEMENTATION_PLAN.md:                       │   │
│  │                                                                   │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │   │
│  │   │   Implement  │ →  │    Test      │ →  │   Verify     │      │   │
│  │   │    Agent     │    │    Agent     │    │  Integration │      │   │
│  │   └──────────────┘    └──────────────┘    └──────────────┘      │   │
│  │          ↑                   │                   │               │   │
│  │          └───────── FAILS ───┴───────────────────┘               │   │
│  │                                                                   │   │
│  │   Gate: typecheck + lint + test + build must pass                │   │
│  │                                                                   │   │
│  │   ┌─────────┐ (Every N tasks or milestone)                       │   │
│  │   │  VRC:   │ "Can user achieve PARTIAL value yet?               │   │
│  │   │ Check 3 │  Should we reorder remaining tasks?"               │   │
│  │   └─────────┘                                                    │   │
│  │                                                                   │   │
│  │   Output: All tasks marked [x] complete                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              ↓                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ PHASE 3: INTEGRATION VERIFICATION (Discovery Loop)               │   │
│  │                                                                   │   │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │   │
│  │   │  Generate   │ →  │   Execute   │ →  │   Analyze   │         │   │
│  │   │  Test Plan  │    │   Tests     │    │    Gaps     │         │   │
│  │   │ from VISION │    │             │    │             │         │   │
│  │   └─────────────┘    └─────────────┘    └─────────────┘         │   │
│  │                                                │                 │   │
│  │                                                ↓                 │   │
│  │                              ┌─────────────────────────────┐     │   │
│  │                              │  GAPS FOUND?                │     │   │
│  │                              │  • Missing routes → Task    │     │   │
│  │                              │  • Broken flow → Task       │     │   │
│  │                              │  • UX issues → Task         │     │   │
│  │                              └─────────────────────────────┘     │   │
│  │                                    │              │              │   │
│  │                              Yes   ↓              ↓ No           │   │
│  │                         Add tasks to plan    All tests pass     │   │
│  │                         Loop to PHASE 2      Proceed            │   │
│  │                                                                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              ↓                                           │
│                        ┌─────────┐                                      │
│                        │  VRC:   │ "If I login as the VISION user,      │
│                        │ Check 4 │  can I achieve the outcome TODAY?"   │
│                        └─────────┘                                      │
│                              │                                          │
│                    ┌─────────┴─────────┐                                │
│                    ↓                   ↓                                │
│               NOT USABLE            USABLE                              │
│           (UX gaps, missing      (Value delivered)                      │
│            connections)                │                                │
│                    │                   ↓                                │
│           Add UX/connection    ┌──────────────────────────────────┐    │
│           tasks, loop to       │ PHASE 4: SHIP                    │    │
│           PHASE 2              │                                  │    │
│                                │   • Final VRC: "Would YOU use    │    │
│                                │     this to get value today?"    │    │
│                                │   • Documentation complete       │    │
│                                │   • Ready for human review       │    │
│                                │                                  │    │
│                                │   Output: PR ready               │    │
│                                └──────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The Missing Piece: Vision Reality Check

Throughout the loop, we need a continuous mechanism asking:

> **"Can a human use this RIGHT NOW to achieve the outcome the VISION promised?"**

This isn't just testing - it's **real-time course correction** to ensure we deliver usable value, not just technically complete code.

---

## Value-Driven Verification (The Deepest Layer)

**Features can "work" without delivering VALUE.** The loop must verify VALUE, not just function.

### Feature vs Value

| Level | Question | Example (Everbee Discovery) |
|-------|----------|----------------------------|
| **Exists** | Does code exist? | EverbeeAgent class exists |
| **Works** | Does it run without error? | Route returns 200 OK |
| **Functions** | Does it do the thing? | Returns product data |
| **Delivers Value** | Does user get intended benefit? | User can identify PROVEN WINNERS to reduce risk |

**A feature that "works" but doesn't deliver VALUE is not complete.**

### Value Mapping from VISION

The loop MUST understand WHY each feature exists:

| Deliverable | What It Does | **Why It Matters (VALUE)** |
|-------------|--------------|---------------------------|
| Everbee discovery | Find products on Etsy | **Reduce risk** - start from proven winners, not guesses |
| Claude concepts | Generate phrase variations | **Scale ideation** - 100 ideas vs. 5 manual brainstorming |
| Concept approval | Human reviews concepts | **Quality control** - bad ideas don't waste design resources |
| Gemini designs | Auto-generate artwork | **Save cost/time** - no designer needed per design |
| Design approval | Human reviews designs | **Brand protection** - only publish quality work |
| Printify creation | Create product in Printify | **Eliminate manual work** - no clicking through Printify UI |
| Etsy publishing | List product on Etsy | **Scale output** - 33 listings/day vs 5/day manual |
| Pipeline view | See items flowing through | **Visibility** - nothing stuck, no hidden failures |
| Portfolio dashboard | Track all listings | **Data-driven decisions** - know what's working |
| Winner/cull flags | Auto-identify good/bad | **Portfolio optimization** - double winners, cut losers |

**Ultimate Value Proposition**: Transform from "guess and manual grind" to "data-driven automation at scale"

### Value Verification Questions

For EACH deliverable, VRC must verify:

```
┌─────────────────────────────────────────────────────────────────┐
│  DELIVERABLE: Everbee Seed Discovery                            │
│  VALUE: User can find PROVEN WINNERS to reduce risk             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. EXISTENCE: Does the entry point exist?                      │
│     → Is there a route/UI to trigger this?                      │
│                                                                  │
│  2. FUNCTION: Does it execute without error?                    │
│     → Does calling it return a response?                        │
│                                                                  │
│  3. DATA: Does it return meaningful data?                       │
│     → Not empty, not stubs, not mocks?                          │
│                                                                  │
│  4. VALUE: Does the data enable the intended benefit?           │
│     → Does it show revenue, reviews, proof of "winner"?         │
│     → Can user actually IDENTIFY proven products from this?     │
│                                                                  │
│  5. USABILITY: Can the target user (non-technical) use it?      │
│     → Is it accessible via UI, not just API?                    │
│     → Is the UX clear enough for the VISION persona?            │
│                                                                  │
│  VERDICT: Only [x] if ALL levels verified                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Examples of "Works But No Value"

| Situation | Works? | Value? | Verdict |
|-----------|--------|--------|---------|
| Route returns empty array | ✅ | ❌ No winners to discover | NOT COMPLETE |
| Returns data but no revenue metrics | ✅ | ❌ Can't identify winners | NOT COMPLETE |
| Works but takes 10 minutes | ✅ | ❌ User won't use it | NOT COMPLETE |
| API works but no UI | ✅ | ❌ Non-technical user can't access | NOT COMPLETE |
| Returns data, shows winners, UI works | ✅ | ✅ User can find proven winners | ✓ COMPLETE |

### The Value Checklist

Generated from VISION.md, tracking VALUE not just function:

```markdown
## VISION VALUE CHECKLIST

Sprint: 1-mvp
Generated from: VISION.md

### Deliverables

| # | Deliverable | Value to User | Exists | Works | Delivers Value |
|---|-------------|---------------|--------|-------|----------------|
| 1 | Everbee discovery | Find proven winners → reduce risk | [ ] | [ ] | [ ] |
| 2 | Claude concepts | Scale ideation → 100 ideas fast | [ ] | [ ] | [ ] |
| 3 | Concept approval | Quality gate → filter bad ideas | [ ] | [ ] | [ ] |
| 4 | Gemini designs | Auto-generate → no designer cost | [ ] | [ ] | [ ] |
| 5 | Design approval | Quality gate → protect brand | [ ] | [ ] | [ ] |
| 6 | Printify creation | Auto-create → no manual clicking | [ ] | [ ] | [ ] |
| 7 | Etsy publishing | Auto-list → scale to 33/day | [ ] | [ ] | [ ] |
| 8 | Pipeline view | See status → nothing hidden | [ ] | [ ] | [ ] |
| 9 | Portfolio dashboard | Track performance → data decisions | [ ] | [ ] | [ ] |
| 10 | Winner/cull system | Auto-identify → optimize portfolio | [ ] | [ ] | [ ] |

### Exit Criteria

CANNOT SHIP until ALL rows have [x] in ALL THREE columns.

A deliverable is only complete when the USER GETS THE VALUE, not just when the code runs.
```

### Vision Reality Check (VRC) - Runs Throughout

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    VISION REALITY CHECK (VRC)                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   INPUT: VISION.md (the promised outcome)                               │
│                                                                          │
│   QUESTIONS:                                                            │
│   1. What outcome does VISION promise the user can achieve?             │
│   2. Can the user achieve that outcome RIGHT NOW with current state?    │
│   3. If not, what's the SHORTEST PATH to usable value?                  │
│   4. Are we building the right things, or just building things right?   │
│                                                                          │
│   REALITY CHECK TRIGGERS:                                               │
│   • After planning: "Does this plan actually deliver the vision?"       │
│   • After each build milestone: "Can the user do X yet?"                │
│   • When tests pass: "Is this actually USABLE or just functional?"      │
│   • Before shipping: "Would a real human get value from this today?"    │
│                                                                          │
│   OUTPUTS:                                                              │
│   • COURSE_CORRECT: Reprioritize tasks toward usable outcome            │
│   • MISSING_PATH: Add tasks that connect built pieces to user value     │
│   • UX_GAP: Built but not usable - fix the experience                   │
│   • ON_TRACK: Continue current path                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### When VRC Runs

| Phase | VRC Question | Action if Fails |
|-------|--------------|-----------------|
| After Plan | "Does this plan lead to a usable outcome?" | Reprioritize/restructure plan |
| During Build (each milestone) | "Can user achieve partial value yet?" | Reorder tasks for earlier value |
| After Build Complete | "Can user complete the VISION workflow end-to-end?" | Add missing connection tasks |
| Before Ship | "Would you use this yourself, today, to get value?" | Fix UX gaps before shipping |

### VRC vs Beta Test

| Vision Reality Check | Beta Test |
|---------------------|-----------|
| "Does this deliver VALUE?" | "Does this WORK?" |
| Outcome-focused | Function-focused |
| Runs throughout | Runs at end |
| Course-corrects early | Catches bugs late |
| "Would a user get value?" | "Does the button work?" |
| Strategic | Tactical |

### The North Star Question

At every phase, the VRC asks:

> **"If I login right now as the user described in VISION.md, can I achieve the outcome they wanted? If not, what's blocking me and what's the fastest fix?"**

Example for EtsyBot VISION:
```
VISION says: "Solo POD seller can go from Everbee data to published Etsy listing"

VRC asks:
- Can I discover seeds via Everbee? → Route missing → BLOCKING
- Can I generate concepts from seeds? → Works → OK
- Can I generate designs? → Works → OK
- Can I publish to Etsy? → Route missing → BLOCKING
- End-to-end flow possible? → NO → CRITICAL GAP

Course correction:
- Prioritize the BLOCKING items
- These are on the critical path to user value
- Other tasks are nice-to-have until these work
```

---

## Vision Reality Check (VRC) Agent

The VRC is a specialized agent that runs throughout the loop, asking the fundamental question:

### The VRC Prompt Pattern

```markdown
## Your Role: Vision Reality Check

You are a reality-check agent ensuring we deliver USABLE VALUE, not just working code.

## The North Star Question

"If I login RIGHT NOW as the user described in VISION.md,
 can I achieve the outcome they wanted?
 If not, what's the SHORTEST PATH to get there?"

## Process

1. **Read VISION.md** - Understand:
   - WHO is the user? (persona, technical level)
   - WHAT outcome do they want? (the "job to be done")
   - HOW do they expect to achieve it? (the workflow)
   - WHAT does success look like? (measurable outcome)

2. **Attempt the Workflow** (or analyze if it's possible):
   - Can I start the workflow? (entry point exists?)
   - Can I complete each step? (all pieces connected?)
   - Does data flow through correctly?
   - Is the UX usable for THIS user (not a developer)?

3. **Identify Blockers to Value**:
   - CRITICAL: Can't achieve outcome at all
   - BLOCKING: Missing step in critical path
   - DEGRADED: Works but painful/confusing
   - POLISH: Works but could be better

4. **Recommend Course Correction**:
   - What's the MINIMUM needed to deliver value?
   - Which tasks should be prioritized/deprioritized?
   - What's missing that wasn't in the plan?
   - What was built but doesn't connect?

## Output

### Checklist Update

```markdown
VISION VALUE CHECKLIST - Status after VRC run

| # | Deliverable | Exists | Works | Delivers Value | Blocking Issue |
|---|-------------|--------|-------|----------------|----------------|
| 1 | Everbee discovery | ❌ | - | - | Route missing |
| 2 | Claude concepts | ✅ | ✅ | ✅ | - |
| 3 | Concept approval | ✅ | ✅ | ⚠️ | Uses mock data |
| 4 | Gemini designs | ✅ | ✅ | ✅ | - |
| 5 | Design approval | ✅ | ✅ | ⚠️ | Uses mock data |
| 6 | Printify creation | ❌ | - | - | Route missing |
| 7 | Etsy publishing | ❌ | - | - | Route missing |
| 8 | Pipeline view | ✅ | ✅ | ✅ | - |
| 9 | Portfolio dashboard | ✅ | ✅ | ⚠️ | Mock data only |
| 10 | Winner/cull system | ✅ | ✅ | ⚠️ | Mock data only |

Summary: 4/10 fully deliver value, 4/10 partial, 3/10 blocked
VERDICT: NOT_READY - Cannot ship
```

### Recommended Actions

```markdown
PRIORITY 1 - Unblock critical path:
- [ ] Implement /api/v1/seeds/discover (blocks #1)
- [ ] Implement /api/v1/publishing/printify (blocks #6)
- [ ] Implement /api/v1/publishing/etsy (blocks #7)

PRIORITY 2 - Convert mock to real:
- [ ] Wire approval queue to real database (#3, #5)
- [ ] Wire portfolio to real Etsy analytics (#9, #10)

After these: Re-run VRC to verify VALUE delivery
```

### Verdicts

- **SHIP_READY**: All deliverables show ✅ in "Delivers Value" column
- **ALMOST_READY**: All exist and work, some value gaps (< 20%)
- **NOT_READY**: Critical path blocked or major value gaps
- **COURSE_CORRECT**: Need to reprioritize to unblock value
```

### VRC Checkpoints

| Checkpoint | When | Question | Possible Actions |
|------------|------|----------|------------------|
| **VRC-1** | After Phase 0 | "Is the VISION clear enough to deliver?" | Clarify VISION with user |
| **VRC-2** | After Phase 1 | "Does this plan deliver the VISION?" | Reprioritize plan, add missing tasks |
| **VRC-3** | During Phase 2 | "Can user get partial value yet?" | Reorder tasks for earlier value |
| **VRC-4** | After Phase 3 | "Can user achieve full VISION outcome?" | Add UX/connection tasks |
| **VRC-5** | Before Phase 4 | "Would YOU use this today?" | Final polish or loop back |

### VRC vs Other Checks

| Check | Focus | Question |
|-------|-------|----------|
| CRAAP | Plan quality | "Is the plan well-formed?" |
| CLARITY | Precision | "Is each task unambiguous?" |
| VALIDATE | Completeness | "Does plan cover all PRD?" |
| CONNECT | Integration | "Do pieces connect?" |
| **VRC** | **Usable value** | **"Can user GET VALUE?"** |
| Beta Test | Functionality | "Does it work?" |

**VRC is the strategic layer on top of all tactical checks.**

---

## Phase Details

### Phase 0: Vision & PRD (Human-Driven)

**Input**: User's idea or requirement
**Output**: Approved VISION.md, PRD.md, ARCHITECTURE.md

**Process**:
1. User runs `/vision` to create VISION.md interactively
2. User runs `/prd` to create PRD.md from vision
3. User runs `/architecture` to create ARCHITECTURE.md
4. User reviews and approves all three

**Gate**: Human must explicitly approve to proceed to Phase 1.

**Prompts needed**: Existing `/vision`, `/prd`, `/architecture` skills

---

### Phase 1: Planning (Quality-Gated Loop)

**Input**: Approved VISION.md, PRD.md, ARCHITECTURE.md
**Output**: Validated IMPLEMENTATION_PLAN.md

**Sub-phases**:

#### 1.1 Generate Initial Plan
- Read all approved docs
- Gap analysis: what exists vs what's needed
- Generate tasks that trace to PRD sections
- Each task sized to fit in one context window

#### 1.2 CRAAP Review
- **C**urrency: Is the plan based on current codebase state?
- **R**elevance: Does every task trace to PRD/VISION?
- **A**uthority: Are technical decisions from ARCHITECTURE.md?
- **A**ccuracy: Are estimates and dependencies realistic?
- **P**urpose: Does each task serve the sprint goal?

**If issues**: Refine plan, loop back to 1.1

#### 1.3 CLARITY Protocol
- Eliminate ambiguity from every task
- Two developers should implement identically
- Specify exact files, functions, interfaces
- Define acceptance criteria per task

**If ambiguous**: Refine task descriptions, loop back

#### 1.4 VALIDATE-SPRINT
- Assert all PRD requirements have tasks
- Assert all VISION features are covered
- Assert dependencies are resolvable
- Assert no circular dependencies

**If validation fails**: Add missing tasks, loop back

#### 1.5 CONNECT Review
- Verify tasks connect to existing system
- No "island" features that don't integrate
- API routes have UI consumers
- Backend has frontend wiring

**If disconnected**: Add integration tasks, loop back

#### 1.6 TIDY-FIRST
- Identify codebase prep needed before building
- Refactoring tasks that unblock implementation
- Add prep tasks to beginning of plan

**Output**: Fully validated IMPLEMENTATION_PLAN.md

---

### Phase 2: Build (Implement + Test Loop)

**Input**: Validated IMPLEMENTATION_PLAN.md
**Output**: All tasks implemented and tested

**Process for each task**:

```
┌─────────────────────────────────────────────────────────┐
│                    TASK BUILD LOOP                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   1. Read task from IMPLEMENTATION_PLAN.md               │
│   2. Read referenced PRD section                         │
│   3. Read referenced ARCHITECTURE section                │
│                                                          │
│   ┌──────────────────────────────────────────────────┐  │
│   │ IMPLEMENT AGENT                                   │  │
│   │ • Write failing test first (TDD)                  │  │
│   │ • Implement minimum code to pass                  │  │
│   │ • Follow ARCHITECTURE patterns                    │  │
│   │ • Run: typecheck, lint, test, build               │  │
│   └──────────────────────────────────────────────────┘  │
│                         ↓                                │
│   ┌──────────────────────────────────────────────────┐  │
│   │ TEST AGENT                                        │  │
│   │ • Verify implementation matches PRD               │  │
│   │ • Run unit tests                                  │  │
│   │ • Run integration tests if applicable             │  │
│   │ • Verify no regressions                           │  │
│   └──────────────────────────────────────────────────┘  │
│                         ↓                                │
│   ┌──────────────────────────────────────────────────┐  │
│   │ INTEGRATION CHECK                                 │  │
│   │ • Is this wired to the rest of the system?        │  │
│   │ • Can it be called from UI/API?                   │  │
│   │ • Does data flow correctly?                       │  │
│   └──────────────────────────────────────────────────┘  │
│                         ↓                                │
│            ALL PASS? ──No──→ Loop back to IMPLEMENT      │
│                 │                                        │
│                Yes                                       │
│                 ↓                                        │
│            Mark task [x] complete                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Key innovation**: Implement and Test are separate agents, forcing verification.

---

### Phase 3: Integration Verification (Discovery Loop)

**Input**: All tasks marked complete
**Output**: Either "all verified" or "new tasks added"

**This is the critical closed-loop phase.**

#### 3.1 Generate Test Plan from VISION

**NOT hardcoded.** The agent:
1. Reads VISION.md
2. Extracts all promised features/capabilities
3. For each promise, generates a verification test
4. Creates BETA_TEST_PLAN.md dynamically

Example:
```
VISION says: "Discover proven products via Everbee"
  → Generate test: "Can trigger seed discovery and get results"
  → Test checks: route exists, returns data, UI shows results

VISION says: "Publish to Etsy with SEO optimization"
  → Generate test: "Can publish a design to Etsy"
  → Test checks: route exists, Etsy listing created, SEO fields populated
```

#### 3.2 Execute Tests

Using Playwright and API calls:
1. Navigate to UI
2. Attempt each user journey
3. Verify end-to-end flow works
4. Capture evidence (screenshots, API responses)

#### 3.3 Analyze Gaps

When a test fails:
1. **Categorize**: Missing route? Broken logic? UI bug? Integration gap?
2. **Create task**: Add to IMPLEMENTATION_PLAN.md or GAPS.md
3. **Trace to VISION**: Which promise is unfulfilled?

Example gap discovery:
```
Test: "Trigger seed discovery"
Result: 404 on /api/v1/seeds/discover
Gap: Route doesn't exist
Action: Create task "Implement /api/v1/seeds/discover route wiring EverbeeAgent"
```

#### 3.4 Loop Decision

```
if (gaps.length > 0) {
  add_tasks_to_plan(gaps)
  return to PHASE 2  // Build the missing pieces
} else {
  proceed to PHASE 4  // Ship
}
```

---

### Phase 4: Ship (Final Verification)

**Input**: All tests passing
**Output**: Sprint complete, ready for merge

**Checklist**:
- [ ] All IMPLEMENTATION_PLAN.md tasks [x] complete
- [ ] All BETA_TEST_PLAN.md scenarios pass
- [ ] No critical/major issues open
- [ ] ADRs written for significant decisions
- [ ] Documentation updated (README, etc.)
- [ ] RETRO.md created with learnings

---

## Implementation Plan for Loop V2

### New Scripts Needed

#### 1. `loop-v2.sh` - Main orchestrator
```bash
#!/bin/bash
# Usage: ./loop-v2.sh <sprint>
# Example: ./loop-v2.sh 1-mvp

SPRINT=$1
SPRINT_DIR="docs/sprints/$SPRINT"

# Phase 0: Verify approved docs exist
verify_docs || exit 1

# VRC Check 1: Is VISION clear?
run_vrc "Is the VISION clear enough to deliver?" || {
  echo "VRC-1 FAILED: VISION needs clarification"
  exit 1
}

# Phase 1: Planning loop
while ! planning_gates_pass; do
  run_planning_phase
  run_craap_review
  run_clarity_protocol
  run_validate_sprint
  run_connect_review
  run_tidy_first
done

# VRC Check 2: Does plan deliver VISION?
run_vrc "Does this plan deliver the VISION outcome?" || {
  echo "VRC-2: Course correcting plan..."
  reorder_plan_for_value
}

# Phase 2 + 3: Build and verify loop
MILESTONE_COUNT=0
while ! all_verified; do

  # Phase 2: Build tasks
  while has_uncomplete_tasks; do
    run_build_phase
    ((MILESTONE_COUNT++))

    # VRC Check 3: Periodic reality check during build
    if (( MILESTONE_COUNT % 5 == 0 )); then
      run_vrc "Can user achieve partial value yet?" && {
        echo "VRC-3: Partial value achievable!"
      } || {
        echo "VRC-3: Reordering for earlier value..."
        reorder_remaining_tasks
      }
    fi
  done

  # Phase 3: Integration verification
  run_beta_test_discovery

  if has_gaps; then
    add_gaps_to_plan
    # Loop back to Phase 2
    continue
  fi

  # VRC Check 4: Can user achieve VISION outcome?
  run_vrc "Can user achieve full VISION outcome?" || {
    echo "VRC-4: UX/connection gaps found, adding tasks..."
    add_ux_tasks
    continue
  }
done

# VRC Check 5: Final reality check
run_vrc "Would YOU use this today to get value?" || {
  echo "VRC-5: Final polish needed..."
  add_polish_tasks
  # Loop back if needed
}

# Phase 4: Ship
run_ship_phase

echo "✅ VISION delivered and verified usable!"
```

#### 2. New/Updated Prompts

| Prompt | Purpose | New? |
|--------|---------|------|
| `PROMPT_vrc.md` | **Vision Reality Check - the strategic layer** | **New (critical)** |
| `PROMPT_plan-v2.md` | Generate plan with quality gates | Update |
| `PROMPT_craap.md` | CRAAP review of plan | New (from skill) |
| `PROMPT_clarity.md` | Eliminate ambiguity | New (from skill) |
| `PROMPT_validate.md` | Validate completeness | New (from skill) |
| `PROMPT_connect.md` | Check integration | New (from skill) |
| `PROMPT_tidy.md` | Prepare codebase | New (from skill) |
| `PROMPT_implement.md` | Implement single task | Update |
| `PROMPT_test-task.md` | Test single task | New |
| `PROMPT_discover-gaps.md` | Find gaps from VISION | New |
| `PROMPT_ship.md` | Final verification | New |

**The VRC prompt is the most important new addition** - it's the strategic layer that ensures we build the right thing, not just build things right.

#### 3. Generic Prompts (Project-Agnostic)

All prompts should:
- Read from `{SPRINT_DIR}/VISION.md`, `PRD.md`, `ARCHITECTURE.md`
- Discover what to check (not hardcode)
- Create tasks dynamically when gaps found
- Work for ANY project, not just EtsyBot

Example generic pattern:
```markdown
## Your Task

1. Read {SPRINT_DIR}/VISION.md
2. Extract all promised features/capabilities
3. For each promise:
   - Determine how to verify it exists
   - Check if implementation exists
   - If missing: create task to implement
   - If exists: verify it works
4. Output gaps found as new tasks
```

---

## Key Differences from Loop V1

| Aspect | V1 | V2 |
|--------|----|----|
| **Flow** | Linear | Closed-loop |
| **Quality gates** | None built-in | CRAAP, CLARITY, VALIDATE, CONNECT, TIDY |
| **Gap discovery** | Manual/hardcoded | Dynamic from VISION |
| **Task creation** | One-time planning | Continuous discovery |
| **Testing** | After build | Interleaved with build |
| **Integration check** | None | Built into every task |
| **Feedback loop** | None | Beta-test → new tasks → build |
| **Project-specific** | Hardcoded routes | Reads from docs |

---

## Success Criteria

Loop V2 is successful when:

1. **Zero hardcoding**: No project-specific checks in prompts
2. **Self-healing**: Missing pieces discovered and fixed automatically
3. **Quality-gated**: All sub-loops enforce their gates
4. **Vision-verified**: Final output matches VISION.md promises
5. **Production-ready**: Not just "compiles" but "works end-to-end"
6. **Reusable**: Works for any project with proper docs

---

## Migration Path

1. **Keep V1 working** - Don't break existing loop.sh
2. **Build V2 alongside** - New loop-v2.sh script
3. **Extract skills to prompts** - Convert /craap, /clarity, etc.
4. **Test on EtsyBot sprint 2** - Prove it works
5. **Replace V1** - Once V2 proven

---

## Open Questions

1. **Parallelism**: Can multiple tasks build in parallel?
2. **Human gates**: Where should human approval be required?
3. **Cost control**: How to prevent infinite loops?
4. **Context management**: How to keep context fresh across loops?
5. **Rollback**: What if Phase 3 keeps finding gaps?

---

## Why This Should Work

### The Core Insight

Current systems fail because they optimize for **technical completion** not **user value**.

- ✅ "All tests pass" → ❌ But user can't achieve their goal
- ✅ "All tasks complete" → ❌ But pieces don't connect
- ✅ "Build succeeds" → ❌ But it's unusable

**Loop V2 optimizes for the user's outcome**, with technical checks as supporting gates.

### The VRC Difference

Without VRC:
```
Build feature A → Build feature B → Build feature C → "Done!"
                                                        ↓
                                              But user can't use it
```

With VRC:
```
Build feature A → VRC: "Can user get value?" → No → Reprioritize!
                                              → Yes → Build feature B
                                                      → VRC: "Can user get MORE value?"
                                                              → No → Add connecting tasks
                                                              → Yes → Continue...
```

### Concrete Example (EtsyBot)

Without VRC:
1. Build EverbeeAgent class ✅
2. Build Claude research API ✅
3. Build Gemini design API ✅
4. Build approval queue UI ✅
5. "Sprint complete!"
6. User logs in... can't do anything. Routes missing. Pieces don't connect.

With VRC after step 2:
```
VRC: "Can user discover seeds and generate concepts?"
Result: NO - EverbeeAgent exists but no route connects it
Action: Add task "Wire EverbeeAgent to /api/v1/seeds/discover"
        Prioritize this BEFORE building more features
```

**VRC catches the gap DURING the sprint, not after.**

---

## Implementation Approach

### Phase 1: Minimal Viable Loop

Start with the simplest version that demonstrates the concept:

1. **VRC prompt only** - Create PROMPT_vrc.md
2. **Manual VRC runs** - Run VRC at checkpoints manually
3. **Prove the concept** - Does VRC catch gaps the old loop missed?

### Phase 2: Integrate with Existing Loop

Once VRC proves valuable:

1. Add VRC checkpoints to loop.sh
2. Keep existing prompts, add VRC as overlay
3. VRC outputs feed back as new tasks

### Phase 3: Full Loop V2

Complete implementation:

1. Create loop-v2.sh with full flow
2. Convert all skills to prompts
3. Automated VRC at all checkpoints
4. Full closed-loop with feedback

---

## Next Steps

1. [ ] **Review this design** - Does this capture the intent?
2. [ ] **Create PROMPT_vrc.md** - The critical new piece
3. [ ] **Test VRC manually** - Run it against current EtsyBot state
4. [ ] **Validate VRC catches gaps** - Does it find the missing routes?
5. [ ] **Integrate VRC into loop.sh** - Add checkpoints
6. [ ] **Create loop-v2.sh** - Full implementation
7. [ ] **Test on Sprint 2** - Prove it works end-to-end

---

## Appendix: Example VRC Run

### Input: Current EtsyBot State

```
VISION.md says:
- "Solo POD seller can go from Everbee data to published Etsy listing"
- "Web-based dashboard for approval workflow"
- "Human approves at RESEARCH and GENERATE stages"

VISION User Persona:
- Solo Etsy seller (non-technical)
- Manages via UI, not CLI
- Wants to test 1,000 listings in 30 days
```

### VRC Value-Based Analysis

```
╔══════════════════════════════════════════════════════════════════════════╗
║  VISION VALUE VERIFICATION                                               ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  DELIVERABLE #1: Everbee Seed Discovery                                  ║
║  VALUE: Find proven winners → reduce risk of failed designs              ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  EXISTS?  → /api/v1/seeds/discover                    → ❌ 404          ║
║  WORKS?   → N/A (doesn't exist)                       → ❌              ║
║  VALUE?   → Can user find proven winners?             → ❌ NO           ║
║  STATUS:  BLOCKED - User cannot reduce risk, forced to guess            ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  DELIVERABLE #2: Claude Concept Generation                               ║
║  VALUE: Scale ideation → 100 concepts vs 5 manual brainstorming          ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  EXISTS?  → /api/v1/research/generate                 → ✅ Found        ║
║  WORKS?   → Returns concepts with reasoning           → ✅ Yes          ║
║  VALUE?   → Can user generate 100 varied concepts?    → ✅ YES          ║
║  STATUS:  ✅ COMPLETE - User gets scaled ideation                       ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  DELIVERABLE #6: Printify Product Creation                               ║
║  VALUE: Eliminate manual work → no clicking through Printify UI          ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  EXISTS?  → /api/v1/publishing/printify               → ❌ 404          ║
║  WORKS?   → N/A                                       → ❌              ║
║  VALUE?   → Can user auto-create products?            → ❌ NO           ║
║  STATUS:  BLOCKED - User must manually create in Printify               ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  DELIVERABLE #7: Etsy Listing Creation                                   ║
║  VALUE: Scale output → 33 listings/day vs 5/day manual                   ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  EXISTS?  → /api/v1/publishing/etsy                   → ❌ 404          ║
║  WORKS?   → N/A                                       → ❌              ║
║  VALUE?   → Can user auto-publish at scale?           → ❌ NO           ║
║  STATUS:  BLOCKED - User stuck at 5/day manual pace                     ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

SUMMARY:
┌────────────────────────────────────────────────────────────────┐
│  Deliverables: 10 total                                        │
│  ✅ Fully deliver value: 4 (concepts, designs, pipeline, UI)  │
│  ⚠️ Partial value: 3 (work but use mocks)                     │
│  ❌ Blocked/no value: 3 (discovery, printify, etsy)           │
│                                                                 │
│  CRITICAL PATH ANALYSIS:                                        │
│  User wants: "Everbee data → published Etsy listing"           │
│  Current:    "??? → concepts → designs → ???"                  │
│                ↑                          ↑                     │
│              BLOCKED                    BLOCKED                 │
│                                                                 │
│  User cannot achieve VISION. Start and end of pipeline broken. │
└────────────────────────────────────────────────────────────────┘

VERDICT: NOT_READY

VALUE GAP ANALYSIS:
The VISION promises user can "go from Everbee to Etsy listing"
Current state: User can generate concepts and designs (middle of pipeline)
              But cannot START (no Everbee) or FINISH (no Etsy)

This is like building a bridge with no on-ramps or off-ramps.
The user gets ZERO of the intended value because the workflow is incomplete.

COURSE CORRECTION - Prioritize by VALUE delivery:

PRIORITY 1 (Unblock critical path - user gets ZERO value without these):
  [ ] Implement /api/v1/seeds/discover → User can START workflow
  [ ] Implement /api/v1/publishing/etsy → User can FINISH workflow

PRIORITY 2 (Scale the value):
  [ ] Implement /api/v1/publishing/printify → Automate middle step

PRIORITY 3 (Polish existing):
  [ ] Wire approval queue to real data
  [ ] Wire portfolio to real analytics

After Priority 1: User can complete end-to-end workflow = VISION delivered
Priority 2+3 enhance but aren't blockers to core value.
```

**This is exactly what the current loop failed to catch.**

The old loop said: "EverbeeAgent implemented ✅, approval queue works ✅, designs generate ✅"
VRC says: "User gets ZERO value because they can't start or finish the workflow."

The difference is asking "does the USER get VALUE?" not "does the CODE work?"
