# Skill: telic-loop

Use when the user wants to run an autonomous development sprint using telic-loop — a vision-to-value delivery system that plans, builds, verifies, and evaluates code autonomously.

## What is Telic Loop?

Telic Loop is a multi-agent system that takes a Vision (desired outcome) and PRD (requirements), then autonomously plans, implements, tests, and evaluates until the promised value is delivered. It uses 4 specialized Claude agents: Planner (Opus), Reviewer (Opus), Builder (Sonnet), and Evaluator (Opus).

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/memyselfmike/telic-loop.git
```

### Prerequisites

- Python >= 3.11
- Claude Code CLI installed and authenticated (`claude` must be on PATH)
- Claude Max subscription or Anthropic API key configured in Claude Code
- Node.js (for browser-based evaluation via Playwright MCP)
- Git (the loop creates branches and commits automatically)

## Setting Up a Sprint

### 1. Create sprint directory

```bash
mkdir -p sprints/<sprint-name>
```

### 2. Write VISION.md

The Vision describes the **outcome** — what the user gets when the sprint is done. Keep it short and concrete.

```markdown
# Vision: <Project Name>

<2-4 sentences describing the desired outcome from the user's perspective.
Focus on what the user can DO when it's done, not how it's built.>
```

### 3. Write PRD.md

The PRD specifies **what must be true** for the Vision to be real. Be specific about behaviors, not implementations.

```markdown
# PRD: <Project Name>

## Requirements

1. **Feature A**: <specific behavior description>
2. **Feature B**: <specific behavior description>
...

## Tech Stack
- <language/framework choices>
- <database/storage>
- <any other constraints>
```

### 4. (Optional) Write ARCHITECTURE.md

For brownfield projects or complex stacks, add `ARCHITECTURE.md` to give the planner context about existing code structure, conventions, and patterns.

## Running a Sprint

```bash
# Basic — sprint artifacts and project code go in sprints/<name>/
telic-loop <sprint-name>

# Existing repo — project code stays in current directory
telic-loop <sprint-name> --project-dir .

# Custom sprint directory
telic-loop <sprint-name> --sprint-dir /path/to/sprint

# Skip post-delivery doc generation
telic-loop <sprint-name> --no-docs
```

### Using with THIS project (existing repo)

To add features or make changes to this codebase via telic-loop:

```bash
mkdir -p sprints/<sprint-name>
# Write VISION.md and PRD.md in sprints/<sprint-name>/
telic-loop <sprint-name> --project-dir .
```

The `--project-dir .` flag tells the loop the application source code is here. Sprint artifacts (state, plan, verifications) stay in the sprint directory.

## Resuming / Resetting

The loop auto-saves state. If interrupted, re-run the same command to resume.

### Surgical Reset

Edit `sprints/<name>/.loop_state.json` to rewind specific phases:

| Phase to redo | What to reset |
|---------------|---------------|
| Planning | Remove `plan_generated` from `gates_passed`, clear `tasks` |
| Review | Remove `plan_reviewed` from `gates_passed` |
| Implementation | Reset target tasks' `status` to `"pending"` |
| Verification | Clear `verifications`, delete `.loop/verifications/` |
| Evaluation | Remove `critical_eval_passed` from `gates_passed` |

### Full Reset

```bash
rm -rf sprints/<name>/.loop_state.json sprints/<name>/.loop
git branch -D $(git branch | grep <name>)
```

## Important Notes

- **Commit before running**: The loop creates a git branch and stashes uncommitted changes. Commit your work first or it will run against stale code.
- **Don't interrupt mid-phase**: If you must stop, use Ctrl+C. The loop will resume from saved state.
- **Check the delivery report**: After completion, review `sprints/<name>/DELIVERY_REPORT.md` for what was built and verified.
- **Sprint artifacts vs project files**: VISION.md, PRD.md, state files stay in the sprint dir. Project code, README, configs go in the project dir (or sprint dir if no `--project-dir` specified).
