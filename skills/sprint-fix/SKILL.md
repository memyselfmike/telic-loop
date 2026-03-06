---
name: sprint-fix
description: Diagnose and fix a stalled or failing telic-loop sprint
argument-hint: <sprint-name>
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Edit, Bash, Glob, Grep
---

# Diagnose and Fix a Stalled Sprint

Investigate why sprint `$0` is stuck and fix it.

## Step 1: Gather Diagnostics

Read these files (in parallel where possible):

- `sprints/$0/.loop_state.json` — full state
- `sprints/$0/.crash_log.jsonl` — crash history (if exists)
- `sprints/$0/IMPLEMENTATION_PLAN.md` — current plan (if exists)
- `sprints/$0/VALUE_CHECKLIST.md` — value tracking (if exists)

## Step 2: Identify the Problem

Common failure patterns:

### Repeated crashes in same phase
Check `crash_log` in state and `.crash_log.jsonl`. Look for:
- **Rate limits**: `RateLimitError` — the loop handles this automatically, just wait and re-run
- **SDK timeouts**: `SDK query timed out` — may need longer timeout or simpler tasks
- **Non-retryable errors**: CLI connection failures, auth issues — fix the environment

### Tasks stuck as blocked
Look for tasks with `status: "blocked"`. Read their `blocked_reason`. Common causes:
- Version incompatibility — check for framework version conflicts in the project
- Missing dependencies — check package.json/pyproject.toml
- External service unavailable — check Docker, databases, APIs

### Verification failures looping
Tasks done but verifications keep failing. Read the failure records in `verifications`:
- If the test script is wrong, delete it from `.loop/verifications/` and clear it from state
- If the app code is wrong, the issue is likely in implementation — reset the task

### Plan review rejecting repeatedly
`plan_reviewed` never gets set. Check `evaluation_findings` in state:
- If findings are valid, reset to plan phase and let it re-plan
- If the reviewer is being too strict, force the gate: add `plan_reviewed` to `gates_passed`

### Evaluator rejecting repeatedly
`critical_eval_passed` never gets set. Check eval findings:
- If findings are real gaps, reset failing tasks to `pending` and re-run
- If the evaluator is wrong, force the gate: add `critical_eval_passed` to `gates_passed`

## Step 3: Apply the Fix

Based on the diagnosis:

1. **Edit `.loop_state.json`** to reset the appropriate phase/tasks (see `/sprint-reset`)
2. **Fix any environment issues** (install dependencies, start services, etc.)
3. **If source code needs changes**: make the fix, commit it, then check out the sprint branch and cherry-pick or merge

## Step 4: Resume

Tell the user to re-run: `telic-loop $0 [--project-dir .]`

The loop will resume from the corrected state.
