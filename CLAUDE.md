# Telic Loop — Development Guide

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

```bash
# Full cleanup for a sprint called "mysprint":
rm -rf sprints/mysprint/.loop_state.json sprints/mysprint/.loop sprints/mysprint/.gitignore
rm -rf sprints/mysprint/project  # if using --project-dir
git branch -D $(git branch | grep mysprint)  # delete sprint branches
```

### Test Runner

```bash
# Test sprints — code goes in the sprint dir itself:
python run_e2e.py <sprint_name>

# Real-world use — code goes in an external project dir:
python run_e2e.py <sprint_name> --project-dir /path/to/project
```

`--project-dir` is for real-world projects where the code lives outside the
sprint directory. For test sprints, omit it — the sprint dir IS the project dir.

## Architecture Quick Reference

### Pre-Loop Gate Order

1. Vision validation + classification
2. Epic decomposition (if multi_epic)
3. Context discovery
4. Docker environment setup
5. PRD critique
6. **Service bootstrap** (greenfield only — scaffold before planning)
7. Plan generation
8. Quality gates (CRAAP, CLARITY, VALIDATE, CONNECT, BREAK, PRUNE, TIDY, blockers, VRC init, preflight)
9. Blocker check

Bootstrap runs BEFORE plan generation so the planner sees the existing scaffold
and generates feature tasks, not setup/infrastructure tasks.

### Decision Engine Priority (P0-P9)

| Priority | Action | Guard |
|----------|--------|-------|
| P0 | INTERACTIVE_PAUSE | `state.pause is not None` |
| P1 | SERVICE_FIX | Services registered + `done_count > 0` + `service_bootstrap` gate passed + unhealthy |
| P2 | COURSE_CORRECT | Stuck (no progress for N iterations) |
| P3 | GENERATE_QC | Enough tasks done + no verifications yet |
| P4 | FIX | Failing QC verifications |
| P5 | INTERACTIVE_PAUSE | Human-blocked tasks |
| P6 | EXECUTE | Pending tasks with deps met |
| P7 | RUN_QC | Pending verifications |
| P8 | CRITICAL_EVAL | Interval-based or all-pass trigger |
| P8b | COHERENCE_EVAL | Critical pending |
| P9 | EXIT_GATE | All done + all passing |

### Task Validation Guards

Tasks are validated by `validate_task_mutation()` in `tools.py`:
- Description required, max 600 chars
- Max 5 files per task
- Meta-instruction detection (rejects "Continue with EXECUTE phase", "Run tasks 1.2-1.11", "Covered by existing tasks", etc.)
- Oversized scope detection (rejects "Build entire frontend", "All remaining epic deliverables")
- VRC auto-created tasks go through the same validation pipeline

### Epic Task Tagging

Tasks from initial plan generation have empty `epic_id`. The epic loop tags
them using `_tag_unassigned_tasks()` which matches by task ID prefix convention
(`N.X` → `epic_N`). This runs ALWAYS before the value loop, not just during
epic preloop.

## Key File Locations

| File | Purpose |
|------|---------|
| `src/telic_loop/phases/preloop.py` | Pre-loop gate orchestration |
| `src/telic_loop/phases/epic.py` | Multi-epic loop + task tagging |
| `src/telic_loop/decision.py` | Deterministic action selection |
| `src/telic_loop/tools.py` | Tool handlers + task validation |
| `src/telic_loop/claude.py` | Claude SDK wrapper |
| `src/telic_loop/state.py` | State dataclasses + persistence |
| `src/telic_loop/config.py` | Configuration with defaults |
| `src/telic_loop/prompts/` | All prompt templates |
| `run_e2e.py` | E2E test runner |

## Common Pitfalls

- **Windows encoding**: Always use `encoding="utf-8"` with `read_text()`/`write_text()`
- **dacite casting**: Use `cast=[Literal, set, tuple]` for generic types
- **State sync**: After each `query()`, reload state from disk (tool CLI modified it)
- **Branch switches discard edits**: Commit before running tests
- **Empty epic_id**: Tasks with empty `epic_id` are invisible to the epic-scoped decision engine
- **VRC meta-tasks**: VRC may create tasks that are execution instructions rather than implementation specs — validation catches most patterns but new variants may appear
