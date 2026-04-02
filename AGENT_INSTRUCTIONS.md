# Working with Telic Loop — Agent Instructions

Copy the relevant sections below into your project's `CLAUDE.md` to give Claude Code context for working with telic-loop sprints. Telic Loop runs on macOS, Windows, and Linux.

---

## For Projects That USE Telic Loop

Add this to your project's `CLAUDE.md`:

```markdown
## Telic Loop Integration

This project uses [telic-loop](https://github.com/memyselfmike/telic-loop) for autonomous sprint delivery.

### Running a Sprint

1. Write `sprints/<name>/VISION.md` — the outcome you want
2. Write `sprints/<name>/PRD.md` — specific requirements
3. Optionally write `sprints/<name>/ARCHITECTURE.md` — existing system context
4. Run: `telic-loop <name> --project-dir .`

### Sprint Workflow

- **NEVER edit** `IMPLEMENTATION_PLAN.md`, `VALUE_CHECKLIST.md`, or `.loop_state.json` manually during a run — these are managed by the loop
- **ALWAYS commit** code changes before running `telic-loop` — the loop creates a new branch and stashes uncommitted changes
- Sprint artifacts live in `sprints/<name>/`, project code is modified in-place via `--project-dir`

### Resuming / Fixing

If a sprint stalls or produces bad output:

1. Kill the loop (`Ctrl+C`)
2. Edit `.loop_state.json` to reset the broken phase (see reset table below)
3. Re-run the same command — it resumes from saved state

| Phase to re-test | What to reset in `.loop_state.json` |
|------------------|-------------------------------------|
| Planning | Remove `plan_generated` from `gates_passed`, clear `tasks` |
| Review | Remove `plan_reviewed` from `gates_passed` |
| Implementation | Reset target tasks' `status` to `"pending"` |
| Verification | Clear `verifications`, delete `.loop/verifications/` |
| Evaluation | Remove `critical_eval_passed` from `gates_passed` |

### What the Loop Creates

- `sprints/<name>/IMPLEMENTATION_PLAN.md` — generated task breakdown
- `sprints/<name>/VALUE_CHECKLIST.md` — value delivery tracking
- `sprints/<name>/DELIVERY_REPORT.md` — final delivery report
- `sprints/<name>/.loop/verifications/` — auto-generated test scripts
- A git branch named `telic-loop/<name>-*` with per-iteration commits
```

---

## For Contributing to Telic Loop Itself

Add this to your working copy's `CLAUDE.md` (already present in the repo):

```markdown
## Development Rules

### Git Safety During Development

**ALWAYS commit code changes before running `run_e2e.py`.**

`setup_sprint_branch()` stashes all uncommitted changes and checks out a new branch.
If you have uncommitted edits to `src/`, they will be stashed away and the test will
use stale code.

When making live fixes during a test run:
1. Kill the test (`Ctrl+C`)
2. Switch to master: `git stash && git checkout master && git stash pop`
3. Apply and commit your fix
4. Clean sprint state and restart

### Architecture Quick Ref

- 4 phases: plan → review → implement → evaluate → complete
- Phase is COMPUTED by `determine_phase(state)`, never stored
- 3 gates: `plan_generated`, `plan_reviewed`, `critical_eval_passed`
- 4 roles: PLANNER (Opus), REVIEWER (Opus), BUILDER (Sonnet), EVALUATOR (Opus)
- 6 structured tools: manage_task, report_task_complete, report_discovery, report_vrc, report_eval_finding, request_exit
- State persisted to `.loop_state.json`, tool CLI mutates it, main loop reloads after each query

### Key Files

| File | Purpose |
|------|---------|
| `src/telic_loop/main.py` | Core loop + phase logic + CLI |
| `src/telic_loop/agent.py` | Claude SDK wrapper + role factory |
| `src/telic_loop/tools.py` | Tool schemas + validation + handlers |
| `src/telic_loop/state.py` | State dataclasses + persistence |
| `src/telic_loop/config.py` | Configuration with defaults |
| `src/telic_loop/prompts/` | 5 prompt templates |

### Common Pitfalls

- **Windows encoding**: Always use `encoding="utf-8"` with `read_text()`/`write_text()`
- **dacite casting**: Use `cast=[Literal, set, tuple]` for generic types
- **State sync**: After each `query()`, reload state from disk (tool CLI modified it)
- **Phase is derived**: Never store phase in state — compute from gates

### Test Runner

```bash
python run_e2e.py <sprint_name>          # E2E test
python -m telic_loop.main <sprint_name>  # Direct run
```
```

---

## Writing Effective Visions and PRDs

### VISION.md Template

```markdown
# Vision: <Project Name>

<2-4 sentences describing the OUTCOME. What does the user get? What can they do
that they couldn't before? Focus on the experience, not the technology.>
```

**Good**: "A recipe manager where home cooks can save, search, and organize their recipes. Open the app, see your collection, find any recipe in seconds."

**Bad**: "A Next.js app with a SQLite backend that implements CRUD operations for recipe entities with full-text search capabilities."

### PRD.md Template

```markdown
# PRD: <Project Name>

## Requirements

1. **<Feature Name>**: <Specific behavior — what the user can do, what happens>
2. **<Feature Name>**: <Specific behavior>
...

## Tech Stack (optional but recommended)
- Backend: <framework + language>
- Frontend: <framework or approach>
- Database: <specific database>

## Constraints (optional)
- <Any hard constraints: "must run without Docker", "single HTML file", etc.>
```

**Tips**:
- Be specific about behaviors, not implementations
- If you specify a tech stack, pin major versions (e.g., "Next.js 14" not "Next.js")
- Include non-obvious requirements (auth, persistence, responsive design)
- The more specific the PRD, the better the output

### ARCHITECTURE.md Template (for existing projects)

```markdown
# Architecture

## Overview
<Brief description of the existing system>

## Tech Stack
- <Language/framework with versions>
- <Database>
- <Key dependencies with versions>

## Directory Structure
```
src/
├── components/    # React components
├── api/           # API routes
└── db/            # Database models
```

## Key Patterns
- <Routing pattern, state management approach, etc.>
- <API conventions>

## Running Locally
```bash
<commands to start the project>
```
```
