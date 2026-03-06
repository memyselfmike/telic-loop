---
name: sprint-status
description: Check the status of a telic-loop sprint (phase, tasks, verifications)
argument-hint: <sprint-name>
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
---

# Sprint Status Check

Check the current status of sprint `$0`.

## Steps

1. **State file**: Read `sprints/$0/.loop_state.json`. If it doesn't exist, report that the sprint hasn't been started yet.

2. **Compute phase** from the state:
   - Missing `plan_generated` gate → **plan** phase
   - Missing `plan_reviewed` gate → **review** phase
   - Has pending/in_progress tasks or failing verifications → **implement** phase
   - Missing `critical_eval_passed` gate → **evaluate** phase
   - All gates passed → **complete**

3. **Report summary**:
   - Current phase
   - Iteration count
   - Tasks: total, done, pending, blocked, descoped (list each with status)
   - Verifications: total, passing, failing (list failures with last error)
   - Latest VRC score and recommendation (if any)
   - Token usage
   - Gates passed
   - Any crashes (check `crash_log` in state and `sprints/$0/.crash_log.jsonl`)

4. **Check artifacts**:
   - `sprints/$0/IMPLEMENTATION_PLAN.md` — exists?
   - `sprints/$0/VALUE_CHECKLIST.md` — exists?
   - `sprints/$0/DELIVERY_REPORT.md` — exists?
   - `sprints/$0/.loop/verifications/` — list scripts and their pass/fail status

5. **Git branch**: Run `git branch | grep $0` to show the sprint branch.

Present the status in a clear, concise format. Highlight any blockers or failures that need attention.
