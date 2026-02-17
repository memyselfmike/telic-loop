# Telic Loop

**A closed-loop value delivery system.** Given a Vision (what outcome a human wants) and a PRD (what must be true for that outcome to exist), Telic Loop plans, executes, verifies, course-corrects, and repeats until the promised value is real — or honestly reports why it can't be delivered.

Telic Loop is not a code generator. It is not a software engineering tool. It is a **vision-to-value algorithm**. The human provides the "what." The loop determines the "how."

## How It Works

```
1. Human writes VISION.md    ("What outcome do we want?")
2. Human writes PRD.md       ("What specifically must be true?")
3. Human runs the loop        (one command)
4. Loop discovers context     (examines codebase, environment, tools)
5. Loop qualifies the work    (PRD critique, feasibility, blocker resolution)
6. Loop executes iteratively  (task -> verify -> regress -> fix -> VRC -> repeat)
7. Loop delivers report       (what was delivered, what was descoped, final score)
8. Human has the outcome
```

No manual configuration. No babysitting. No post-loop debugging.

## Core Concepts

| Concept | What It Means |
|---|---|
| **Vision** | The outcome a human was promised |
| **PRD** | The specific requirements that make the outcome real |
| **Task** | A unit of work that moves toward the outcome |
| **Quality Control** | Automated checks that the deliverable works correctly |
| **Critical Evaluation** | A separate agent that *uses* the deliverable as a real user would — opens a browser for web apps |
| **VRC** | Vision Reality Check — continuous pulse on value delivery |

## Architecture

Telic Loop uses a **two-phase architecture**:

### Pre-Loop
Qualify the work before executing. Validate inputs, discover context, critique the PRD, generate a plan, run quality gates (CRAAP, CLARITY, VALIDATE, CONNECT, BREAK, PRUNE, TIDY), resolve blockers, and verify the environment.

### The Value Loop
Decision-driven delivery — each iteration asks "what should I do next?" based on current state, not "what phase am I in?"

```
while not value_delivered:
    decision = decide_next_action(state)

    match decision:
        EXECUTE         -> execute task (Builder agent)
        QC              -> run quality checks (QC agent)
        FIX             -> fix failing checks
        CRITICAL_EVAL   -> evaluate experience (Evaluator agent)
        COURSE_CORRECT  -> re-plan, restructure, descope
        RESEARCH        -> search web/docs for external knowledge
        INTERACTIVE_PAUSE -> human action needed
        EXIT_GATE       -> fresh-context final verification
```

The exit gate is **inside** the loop. If it finds gaps, those become tasks and the loop continues. There is no post-loop dead end.

## Multi-Agent System

Different concerns require different agents with different models:

| Agent | Model | Purpose |
|---|---|---|
| **Planner** | Opus | Plans tasks, critiques PRD, runs quality gates |
| **Builder** | Sonnet | Executes tasks, writes code/content |
| **QC Agent** | Sonnet/Haiku | Tests, linting, type checks, regression |
| **Critical Evaluator** | Opus | Uses the deliverable as a real user, judges experience |
| **VRC Agent** | Haiku/Opus | Tracks progress, assesses value delivery |
| **Course Corrector** | Opus | Diagnoses why the loop is stuck, changes strategy |
| **Research Agent** | Opus | Searches web, reads current docs, synthesizes findings |

The builder never grades its own work. QC checks correctness. Critical evaluation checks value. Both are required.

## Key Capabilities

1. **Self-Configuration** — Loop derives what it needs from Vision + PRD + codebase
2. **Aggressive Pre-Qualification** — Validates work is achievable before executing
3. **Decision-Driven Delivery** — State-based decisions, not rigid phases
4. **Separate QC** — Builder never grades own work
5. **Critical Evaluation** — Uses deliverable as real user (opens browser for web apps via Playwright MCP), pursues excellence not just correctness
6. **VRC Heartbeat** — Continuous value tracking every iteration
7. **Interactive Pause** — Pauses for genuine human-only actions, resumes autonomously
8. **Course Correction** — Self-diagnoses stuck states, changes strategy or rolls back
9. **Git Safety Net** — Feature branches, per-task commits, checkpoints at QC pass, rollback to known-good state
10. **External Research** — Searches web when built-in knowledge is stale
11. **Structured State** — JSON single source of truth, no markdown editing

## Implementation Phases

The system is built incrementally. Each phase is independently usable:

| Phase | Agents | What It Adds |
|---|---|---|
| **Phase 1** (MVP) | Builder + QC + Decision Engine | Pre-loop, execute, QC, fix, interactive pause |
| **Phase 2** | + VRC + Course Corrector | Value tracking, exit gate, course correction, budget |
| **Phase 3** | + Critical Eval + Research | Experience evaluation, external research, process monitor, vision validation, epic decomposition |

## Project Structure

```
telic-loop/
├── src/telic_loop/
│   ├── main.py              # Entry point
│   ├── config.py            # LoopConfig
│   ├── state.py             # LoopState + dataclasses
│   ├── discovery.py         # Context Discovery
│   ├── decision.py          # Decision engine
│   ├── claude.py            # Claude Agent SDK wrapper (MCP + browser eval)
│   ├── git.py               # Git ops: branching, commits, safety, rollback
│   ├── tools.py             # Tool implementations
│   ├── render.py            # Markdown generation from state
│   ├── phases/              # Action handlers
│   │   ├── preloop.py
│   │   ├── execute.py
│   │   ├── qc.py
│   │   ├── critical_eval.py
│   │   ├── vrc.py
│   │   ├── course_correct.py
│   │   ├── exit_gate.py
│   │   └── ...
│   └── prompts/             # Reasoning templates (30 prompts)
├── docs/                    # V3 planning & architecture docs
├── reference/v2/            # V2 implementation (reference)
├── pyproject.toml
└── README.md
```

## Requirements

- Python >= 3.11
- `claude-agent-sdk` >= 0.1.37 (wraps `claude` CLI subprocess)
- Claude Code CLI installed and authenticated (Max subscription or API key)
- Node.js (for browser-based critical evaluation via `@playwright/mcp`)

## Status

**Phase 3 complete.** All three implementation phases are live and tested end-to-end. The system autonomously delivers value from Vision + PRD through interactive pre-loop refinement, multi-agent execution, browser-based critical evaluation, and verified exit gate.

## Documentation

- [Loop Flow](docs/LOOP_FLOW.md) — Visual flow diagram (Mermaid) with git operations
- [Vision](docs/V3_VISION.md) — The full vision document
- [Architecture](docs/V3_ARCHITECTURE.md) — Structural specification
- [PRD](docs/V3_PRD.md) — Product requirements with acceptance criteria
- [Phase 1 Plan](docs/V3_PHASE1_PLAN.md) — MVP implementation details
- [Phase 2 Plan](docs/V3_PHASE2_PLAN.md) — VRC + Course Correction
- [Phase 3 Plan](docs/V3_PHASE3_PLAN.md) — Critical Eval + Research + Process Monitor

## License

MIT
