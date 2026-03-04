# Telic Loop V4 — Development Guide

## Critical Workflow Rules

### Git Safety During Development

**ALWAYS commit code changes before running `run_e2e.py`.**

`setup_sprint_branch()` in `git.py` stashes all uncommitted changes and checks
out a new branch. If you have uncommitted edits to source files (`src/`), they
will be stashed away and the running test will use stale code.

```
# WRONG: Edit files → run test → changes stashed → old code runs
# RIGHT: Edit files → git commit → run test → new code on sprint branch
```

When making live fixes during a test run:
1. Kill the test (`Ctrl+C` or `taskkill`)
2. Switch to master: `git stash && git checkout master && git stash pop`
3. Apply and commit your fix
4. Clean sprint state and restart

### Sprint State Cleanup Between Runs

#### Surgical Reset (preferred for targeted fixes)

Edit `.loop_state.json` directly to rewind to just before the broken phase.

V4 has only 3 gates: `plan_generated`, `plan_reviewed`, `critical_eval_passed`.

| Phase to re-test | What to reset in `.loop_state.json` | Files to delete |
|------------------|-------------------------------------|-----------------|
| Planning | Remove `plan_generated` from `gates_passed`, clear `tasks` | — |
| Review | Remove `plan_reviewed` from `gates_passed` | — |
| Implementation | Reset target tasks' `status` to `"pending"` | — |
| Verification | Clear `verifications`, reset failing tests | `.loop/verifications/` |
| Evaluation | Remove `critical_eval_passed` from `gates_passed` | — |

#### Full Reset (only when necessary)

```bash
rm -rf sprints/mysprint/.loop_state.json sprints/mysprint/.loop sprints/mysprint/.gitignore
git branch -D $(git branch | grep mysprint)
```

### Test Runner

```bash
# Test sprints — code goes in the sprint dir itself:
python run_e2e.py <sprint_name>

# Via main module:
python -m telic_loop.main <sprint_name> [--project-dir /path/to/project]
```

## Architecture Quick Reference (V4)

### Phase Flow (4 phases, derived from gates)

```
plan → review → implement → evaluate → complete
  ↑        ↑         ↑           |
  |        |         └───────────┘  (eval finds gaps → back to implement)
  |        └── review rejects → re-plan
  └── no tasks created → retry
```

Phase is COMPUTED by `determine_phase(state)`, never stored:
- No `plan_generated` gate → `plan`
- No `plan_reviewed` gate → `review`
- Has pending work → `implement`
- No `critical_eval_passed` gate → `evaluate`
- All gates + all work done → `complete`

### Role Model (4 roles)

| Role | Model | Max Turns | Tools | Purpose |
|------|-------|-----------|-------|---------|
| PLANNER | Opus | 40 | Full + Web | Context discovery, plan creation |
| REVIEWER | Opus | 20 | Read-only | Plan quality review (separate context) |
| BUILDER | Sonnet | 60 | Full | Implementation, verification, fixing |
| EVALUATOR | Opus | 40 | Read-only + Playwright | Adversarial quality evaluation |

### Task Validation Guards

Tasks are validated by `validate_task_mutation()` in `tools.py`:
- Description required, max 600 chars
- Max 5 files per task
- Meta-instruction detection (rejects "Continue with EXECUTE phase", etc.)
- Oversized scope detection (rejects "Build entire frontend", etc.)
- Duplicate detection (Jaccard similarity ≥ 0.75)
- Mid-loop task ceiling (15 non-plan tasks)

### Structured Tools (tool CLI)

V4 has 6 structured tools (V3 had 15):
- `manage_task` — Add/modify/remove tasks
- `report_task_complete` — Signal task completion
- `report_discovery` — Report context discovery results
- `report_vrc` — Vision Reality Check
- `report_eval_finding` — Evaluation findings + verdict
- `request_exit` — Builder signals readiness for evaluation

## Key File Locations

| File | Purpose |
|------|---------|
| `src/telic_loop/main.py` | Core loop + phase logic + CLI |
| `src/telic_loop/agent.py` | Claude SDK wrapper + role factory |
| `src/telic_loop/tools.py` | Tool schemas + validation + handlers |
| `src/telic_loop/state.py` | State dataclasses + persistence |
| `src/telic_loop/config.py` | Configuration with defaults |
| `src/telic_loop/git.py` | Git operations (branch, commit, rollback) |
| `src/telic_loop/render.py` | Markdown artifact generation |
| `src/telic_loop/testing.py` | Cross-platform test execution |
| `src/telic_loop/tool_cli.py` | Tool CLI bridge |
| `src/telic_loop/prompts/` | 5 prompt templates |
| `run_e2e.py` | E2E test runner |
| `archive/v3/` | V3 source code archive (tagged v3-final) |

## Common Pitfalls

- **Windows encoding**: Always use `encoding="utf-8"` with `read_text()`/`write_text()`
- **dacite casting**: Use `cast=[Literal, set, tuple]` for generic types
- **State sync**: After each `query()`, reload state from disk (tool CLI modified it)
- **Branch switches discard edits**: Commit before running tests
- **VRC meta-tasks**: VRC may create tasks that are execution instructions — validation catches most patterns
- **Phase is derived**: Never store phase in state — compute it from gates via `determine_phase()`
