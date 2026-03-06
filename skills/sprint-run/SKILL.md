---
name: sprint-run
description: Run a telic-loop sprint to deliver the Vision autonomously
argument-hint: <sprint-name>
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash, Read, Glob, Grep
---

# Run a Telic Loop Sprint

Run the sprint `$0` using telic-loop.

## Pre-flight Checks

Before running, verify:

1. **Sprint files exist**: Check that `sprints/$0/VISION.md` and `sprints/$0/PRD.md` exist. If not, tell the user to run `/sprint-init $0` first.

2. **telic-loop is installed**: Run `python -c "import telic_loop; print('OK')"`. If it fails, install it:
   ```bash
   pip install git+https://github.com/memyselfmike/telic-loop.git
   ```

3. **Clean git state**: Run `git status`. Warn the user if there are uncommitted changes — the loop will stash them when it creates a sprint branch. Recommend committing first.

4. **Version pinning**: Read `sprints/$0/PRD.md` and check that any tech stack references use pinned versions. Flag "latest", loose ranges like "3.x", or unversioned framework names.

## Run

Determine the correct command based on project structure:

- If `sprints/$0/` contains application source code (or will — greenfield): `telic-loop $0`
- If this is an existing repo and code should be modified in-place: `telic-loop $0 --project-dir .`

Ask the user which mode applies if unclear, then run:

```bash
telic-loop $0 [--project-dir .]
```

## Monitoring

The loop is fully autonomous. It will:
- Print phase transitions and iteration counts
- Create a git branch `telic-loop/$0-*`
- Commit after each implementation iteration
- Generate `IMPLEMENTATION_PLAN.md`, `VALUE_CHECKLIST.md`, and `DELIVERY_REPORT.md`

The loop handles crashes and rate limits internally with retry logic. Only interrupt if it's clearly stuck repeating the same action.

## When It Finishes

Report to the user:
- Which git branch has the changes
- Read `sprints/$0/DELIVERY_REPORT.md` for the summary
- Read `sprints/$0/VALUE_CHECKLIST.md` for value delivery status
