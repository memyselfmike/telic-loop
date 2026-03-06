---
name: sprint-reset
description: Reset a telic-loop sprint phase to re-run it (surgical or full reset)
argument-hint: <sprint-name> [phase|full]
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob
---

# Reset a Sprint Phase

Reset sprint `$0` to re-run a specific phase or do a full reset.

## Determine Reset Type

If the user specified a phase (`$1`), do a surgical reset. If they said "full", do a full reset. If no second argument, ask the user what they want to reset:

- `plan` — Re-run planning from scratch
- `review` — Re-run plan review
- `implement` — Re-run specific tasks
- `verify` — Re-run verification scripts
- `evaluate` — Re-run critical evaluation
- `full` — Wipe everything and start over

## Surgical Reset

Read `sprints/$0/.loop_state.json` and modify it:

| Phase | Edit to `.loop_state.json` | Files to delete |
|-------|---------------------------|-----------------|
| `plan` | Remove `plan_generated` from `gates_passed`, clear `tasks` object | — |
| `review` | Remove `plan_reviewed` from `gates_passed` | — |
| `implement` | Ask which tasks to reset, set their `status` to `"pending"` | — |
| `verify` | Clear `verifications` object, reset related task statuses | `sprints/$0/.loop/verifications/` |
| `evaluate` | Remove `critical_eval_passed` from `gates_passed` | — |

After editing, save the file and confirm the change.

## Full Reset

**Ask for confirmation first** — this is destructive.

```bash
rm -rf sprints/$0/.loop_state.json sprints/$0/.loop sprints/$0/.gitignore
```

Then list and offer to delete the sprint branch:
```bash
git branch | grep $0
```

If branches exist, ask before deleting: `git branch -D <branch-name>`

## After Reset

Tell the user to re-run with `/sprint-run $0` or `telic-loop $0 [--project-dir .]`.
