# V4 Design Principles: The Middle Ground

**Date:** 2026-03-04
**Status:** Draft for discussion
**Context:** Post V3 post-mortem, post zeroclaw analysis, before V4 planning begins

---

## The Problem We're Solving

LLMs are capable of delivering excellent work. But they don't by default. Left unconstrained, they gravitate toward:

- **Token efficiency** — doing the minimum to satisfy the prompt
- **Early termination** — stopping at "works" rather than "works well"
- **Approval-seeking** — asking the human rather than deciding
- **Median quality** — no error handling, no edge cases, no polish

Tools like Claude Code demonstrate this daily: sessions produce code that works for the happy path, misses edge cases, includes debug artifacts, lacks proper error handling, and requires human cleanup.

**Telic Loop exists to push past this equilibrium.** The name says it: *telic* — purposeful, goal-directed. The system's job is to ensure that what gets delivered meets a quality bar that the LLM wouldn't reach on its own.

V3 tried to solve this with deterministic control — a decision engine, phase handlers, quality scanners, process monitors. It created a complexity trap. But the underlying goal was right.

V4 must find the middle ground: **enough structure to push past mediocrity, without enough complexity to create cascading failure modes.**

---

## Principle 1: Guardrails, Not Rails

**Rails** tell the LLM exactly what to do next (V3's P0-P9 decision engine).
**Guardrails** prevent it from stopping too early or producing low-quality work.

| Rails (V3) | Guardrails (V4) |
|------------|-----------------|
| "Your next action is FIX" | "You may not exit until all verifications pass" |
| "Run code quality scanner after each task" | "Your deliverable must have no debug artifacts, proper error handling, and responsive design" |
| "Execute RESEARCH after 3 failed fixes" | "If you're stuck, explain why and try a different approach" |
| "Run 7 quality gates on the plan" | "Before implementing, verify your plan addresses these common failure patterns: [list]" |

The LLM decides *how* to work. The system decides *when work is done.*

---

## Principle 2: Plan Hard, Implement, Evaluate Hard

This was V3's best insight, buried under complexity. The three phases are:

### Plan Hard
The planning phase is where deterministic quality enforcement has the highest ROI. A bad plan leads to hours of wasted implementation. A good plan front-loads the thinking.

**V3's mechanism:** 7 separate quality gates (CRAAP, CLARITY, VALIDATE, CONNECT, BREAK, PRUNE, TIDY), each an Opus call. Cost: ~50k tokens, 30+ minutes. Value: rubber-stamped 90% of the time.

**V4's mechanism:** One comprehensive plan review that encodes ALL the quality insights from those 7 gates into a single prompt. The review asks:

> Does this plan account for:
> - Error handling for every user-facing operation?
> - Edge cases (empty states, long strings, special characters, concurrent access)?
> - Input validation at all system boundaries?
> - Responsive design across device sizes?
> - Accessibility basics (semantic HTML, keyboard navigation, ARIA labels)?
> - Security (XSS prevention, SQL injection, CSRF)?
> - Performance (pagination for lists, lazy loading for media, debouncing for inputs)?
> - Graceful degradation (what happens when the API is down? when JS fails?)?

One call. All the knowledge. If the plan has gaps, the review identifies them before implementation starts.

### Implement
The LLM drives implementation with tools. It creates tasks, executes them, manages its own workflow. The system provides tools and stays out of the way.

But: the system tracks progress. If the LLM has executed 10 tasks and generated 0 verifications, that's a guardrail trigger — not "your next action is GENERATE_QC" but "you have built 10 features with no quality checks. Generate verifications before continuing."

### Evaluate Hard
This is where telic-loop earns its name. The evaluation phase must be:

1. **Non-negotiable** — the LLM cannot skip it, cannot self-certify
2. **Adversarial** — a separate evaluation context (not the builder) judges quality
3. **Browser-based** — for UI deliverables, actually look at what was built
4. **Value-focused** — not "does the code compile" but "would a user be satisfied"

V3's critical evaluation was one of its best features. It just didn't fire reliably. In V4, critical evaluation is a hard gate: you cannot exit without it passing.

---

## Principle 3: Encode Quality Knowledge in Prompts, Not Subsystems

V3 built subsystems to enforce quality (code quality scanner, coherence eval, process monitor). Each subsystem was 200-800 lines of code with its own failure modes.

V4 encodes the same knowledge in the system prompt and tool descriptions. The LLM internalizes the quality expectations and applies them naturally during implementation.

**Example — V3's code quality scanner (778 lines) detected:**
- Debug artifacts (console.log, alert, debugger)
- Functions >80 lines
- Files >500 lines
- Duplicate code blocks
- Missing PRD-specified files

**V4 equivalent — system prompt paragraph:**

> Code quality standards (non-negotiable):
> - No debug artifacts in delivered code (console.log, debugger statements, TODO/FIXME comments, hardcoded test data)
> - No function exceeding 60 lines — split into focused helpers
> - No file exceeding 400 lines — split by responsibility
> - Every user-facing error must have a meaningful error message
> - All API endpoints must validate input and return appropriate HTTP status codes
> - All forms must validate client-side before submission

The LLM applies these during implementation, not after. Prevention, not detection.

BUT — the critical evaluation (separate context, adversarial) still checks for these issues. This is the safety net. If the builder misses something, the evaluator catches it.

---

## Principle 4: Value-Gated Termination

The LLM may not exit until value is verified. This is the most important deterministic rule in the system.

**Termination requires ALL of:**
1. All planned tasks completed (or explicitly descoped with justification)
2. All verifications passing
3. Critical evaluation score above threshold
4. VRC (Value Reality Check) confirms acceptance criteria met

The LLM decides when to *attempt* exit. The system decides whether the attempt *succeeds*. If it fails, the LLM gets the gap analysis and keeps working.

This is the "keep going" imperative. The natural LLM tendency is to call it done at first green test. The value gate says: not yet.

---

## Principle 5: One Loop, Not Two

V3 had a preloop and a value loop — two distinct execution modes with different logic. The preloop ran 10+ gates sequentially before the value loop started. If any gate failed, the entire preloop restarted.

V4 has one loop. The first iterations are naturally planning-focused (the system prompt guides this). The middle iterations are implementation. The final iterations are evaluation and polish. But it's one continuous conversation with the LLM, not two separate modes.

**Phase transitions happen naturally:**
- "I've analyzed the PRD and codebase. Here's my plan: [tasks]. Let me review this against the quality checklist before starting." → Planning to implementation
- "All tasks are complete. Let me generate verification scripts and run them." → Implementation to evaluation
- "3 of 5 verifications are failing. Let me fix these issues." → Evaluation to fix
- "All verifications pass. Running critical evaluation..." → Fix to final eval

The system prompt describes this flow. The LLM follows it. But the LLM has freedom to deviate when the situation requires it (e.g., a task reveals a design flaw — go back to planning without needing a "COURSE_CORRECT" subsystem).

---

## Principle 6: Model-Agnostic Quality Through Prompt Scaffolding

Opus naturally produces better plans and more thorough implementations than Sonnet. But telic-loop should deliver quality with any capable model. This means:

**More scaffolding for less capable models:**
- Detailed task descriptions with acceptance criteria (not just "implement login")
- Explicit checklists in the system prompt (not implicit expectations)
- Worked examples of good vs bad implementations
- Step-by-step evaluation rubrics

**Less scaffolding for more capable models:**
- Terser system prompts
- Higher-level task descriptions
- Trust the model to fill in quality details

V4 should support a `scaffolding_level` config (or infer it from the model) that adjusts prompt verbosity. The quality bar stays the same — only the amount of guidance changes.

---

## Principle 7: Hard Limits Are Non-Negotiable

Every loop, every retry, every recovery path must have a hard upper bound that cannot be overridden by any subsystem or LLM decision.

| Limit | Default | Override? |
|-------|---------|-----------|
| Max iterations per task attempt | 5 | No |
| Max total iterations per epic | 50 | No |
| Max total iterations per sprint | 200 | No |
| Max token spend per sprint | 2M | Config only (human sets before run) |
| Max fix attempts per verification | 3 | No |
| Max QC regeneration cycles | 2 | No |
| Critical eval: must run before exit | Always | No |

When a limit is hit, the system stops that activity and moves on. No strategy reasoner. No process monitor. No "but maybe one more try." The limit is the limit.

---

## Principle 8: Observability Over Automation

V3 tried to automatically diagnose and fix problems (process monitor, strategy reasoner, research subsystem). V4 makes problems visible and lets the LLM (or human) decide.

**Observable state (always available via tools):**
- Task list with status
- Verification results with full output
- VRC score with gap analysis
- Iteration count and token spend
- Recent error history

**Automated responses: none.** The LLM reads the state, reasons about it, and acts. If it's stuck, it says so (and the human can intervene). If a verification is failing, it reads the error and fixes the code.

The only automated behavior is the hard limits (Principle 7). Everything else is LLM-driven.

---

## Principle 9: The Human Is the Escape Valve, Not the Steering Wheel

V3's INTERACTIVE_PAUSE was rarely useful. V4 should have a clearer model:

- **Human provides:** Vision, PRD, config, approval to start
- **LLM handles:** Everything from planning to delivery
- **Human intervenes only when:** LLM explicitly requests help (tool: `request_help`) OR hard limit is reached
- **Human never:** Monitors iteration-by-iteration, kills stuck runs, manually resets state

If the system needs human intervention to work, it's broken. The human's job is to define what "done" looks like. The system's job is to get there.

---

## Principle 10: Earn Every Line of Code

V3 grew from a clean concept to 9,610 lines because each addition felt locally justified. V4 starts from zero and every line must earn its place through evidence.

**Rules:**
1. No feature is added until an e2e test proves it's needed
2. No subsystem is added — features are tools, prompts, or config
3. If a prompt can do the job, don't write code
4. If a hard limit can prevent a problem, don't build a detector
5. Re-run the benchmark sprint (recipe-manager) after every significant change
6. If the benchmark gets worse, revert

---

## Summary: The Quality Stack

```
┌─────────────────────────────────────────┐
│ LAYER 4: Value Gate (deterministic)     │
│ Cannot exit without verified value      │
│ Critical eval + VRC + all tests passing │
├─────────────────────────────────────────┤
│ LAYER 3: Adversarial Evaluation         │
│ Separate context evaluates quality      │
│ Browser-based for UI, API-based for BE  │
│ Catches what the builder missed         │
├─────────────────────────────────────────┤
│ LAYER 2: Quality-Aware Implementation   │
│ System prompt encodes quality standards │
│ LLM applies them during building        │
│ Prevention over detection               │
├─────────────────────────────────────────┤
│ LAYER 1: Plan Quality Check             │
│ One comprehensive review before build   │
│ All V3 gate insights in one prompt      │
│ Catches design-level issues early       │
├─────────────────────────────────────────┤
│ LAYER 0: Hard Limits (deterministic)    │
│ Iteration caps, token budgets           │
│ Non-overridable safety bounds           │
└─────────────────────────────────────────┘
```

The bottom and top layers are deterministic. The middle layers are LLM-driven. This is the balance: **deterministic boundaries, intelligent interior.**
