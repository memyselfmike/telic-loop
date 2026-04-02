# Telic Loop

**Vision-to-value delivery system.** Give it a Vision (what outcome you want) and a PRD (what must be true), and it plans, builds, verifies, and course-corrects until the promised value is real — or honestly reports why it can't be delivered.

## Quick Start

### Install

```bash
# From PyPI (when published)
pip install telic-loop

# From GitHub
pip install git+https://github.com/memyselfmike/telic-loop.git

# Editable install (for development)
git clone https://github.com/memyselfmike/telic-loop.git
cd telic-loop
pip install -e .
```

### Prerequisites

- **Python** >= 3.11
- **Claude Code CLI** installed and authenticated (`claude` must be on PATH)
- **Claude Max subscription** or Anthropic API key configured in Claude Code
- **Node.js** >= 18 (for browser-based evaluation via Playwright MCP)
- **Git** (the loop creates branches and commits automatically)

#### macOS Setup

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install prerequisites
brew install python node git

# Install Claude Code CLI (requires npm)
npm install -g @anthropic-ai/claude-code

# Authenticate Claude Code
claude auth
```

#### Windows Setup

```bash
# Install Python from https://python.org (3.11+)
# Install Node.js from https://nodejs.org (18+)
# Install Git from https://git-scm.com

# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Authenticate Claude Code
claude auth
```

### Run a Sprint

```bash
# 1. Create a sprint directory with your Vision and PRD
mkdir -p sprints/my-sprint
# Write sprints/my-sprint/VISION.md  — the outcome you want
# Write sprints/my-sprint/PRD.md     — the specific requirements

# 2. Run the loop
telic-loop my-sprint
```

That's it. The loop handles planning, implementation, verification, and evaluation autonomously.

See `sprints/temp-calc/` for an example VISION.md and PRD.md to use as a starting point.

## How It Works

```
Human writes VISION.md  →  "What outcome do I want?"
Human writes PRD.md     →  "What must be true for that outcome?"
Human runs one command   →  telic-loop my-sprint
Loop delivers the outcome (or reports why it can't)
```

### Phase Flow

```
plan → review → implement → evaluate → complete
  ↑        ↑         ↑           |
  |        |         └───────────┘  (eval finds gaps → back to implement)
  |        └── review rejects → re-plan
  └── no tasks created → retry
```

Phase is always **computed** from gate state, never stored:

| Gate | Phase if missing |
|------|-----------------|
| `plan_generated` | plan |
| `plan_reviewed` | review |
| (has pending work) | implement |
| `critical_eval_passed` | evaluate |
| (all gates passed) | complete |

### Multi-Agent System (4 roles)

| Role | Model | Purpose |
|------|-------|---------|
| **Planner** | Opus | Context discovery, plan creation, version pinning |
| **Reviewer** | Opus | Adversarial plan quality review (separate context) |
| **Builder** | Sonnet | Implementation, verification, fixing, version troubleshooting |
| **Evaluator** | Opus | Uses the deliverable as a real user (browser via Playwright) |

The builder never grades its own work. The evaluator judges quality adversarially.

## Usage

### CLI

```bash
# Basic — sprint dir is sprints/<name>/, project code goes there too
telic-loop my-sprint

# Separate project directory (for adding features to existing repos)
telic-loop my-sprint --project-dir /path/to/existing/project

# Custom sprint directory location
telic-loop my-sprint --sprint-dir /path/to/sprint

# Skip post-delivery documentation generation
telic-loop my-sprint --no-docs
```

### Using with an Existing Repository

To run a telic-loop sprint against an existing codebase:

```bash
# From inside your project repo:
mkdir -p sprints/add-auth
# Write sprints/add-auth/VISION.md and sprints/add-auth/PRD.md

telic-loop add-auth --project-dir .
```

The `--project-dir` flag tells the loop where the application source code lives. The sprint artifacts (state, plan, verifications) stay in the sprint directory.

### As a Python Module

```bash
python -m telic_loop.main my-sprint [--project-dir /path] [--sprint-dir /path]
```

### Programmatic Use

```python
from pathlib import Path
from telic_loop.config import LoopConfig
from telic_loop.state import LoopState
from telic_loop.agent import Agent
from telic_loop.main import run_loop
from telic_loop.git import ensure_gitignore, setup_sprint_branch

config = LoopConfig(
    sprint="my-sprint",
    sprint_dir=Path("sprints/my-sprint"),
    project_dir=Path("."),       # optional: existing repo
    max_iterations=80,           # safety valve
)

config.sprint_dir.mkdir(parents=True, exist_ok=True)
state = LoopState(sprint="my-sprint")
agent = Agent(config, state)

ensure_gitignore(config.sprint_dir)
setup_sprint_branch(config, state)
state.save(config.state_file)

run_loop(config, state, agent)
```

## Writing a Good Vision and PRD

### VISION.md

The Vision describes the **outcome** — what the user gets when the sprint is done. Keep it short and concrete.

```markdown
# Vision: Recipe Manager

A web app where home cooks can save, search, and organize recipes.
The cook opens the app, sees their recipe collection, and can find
any recipe in seconds by ingredient, cuisine, or meal type.
```

### PRD.md

The PRD specifies **what must be true** for the Vision to be real. Be specific about behaviors, not implementations.

```markdown
# PRD: Recipe Manager

## Requirements

1. **Recipe CRUD**: Create, read, update, delete recipes with title,
   ingredients, instructions, prep time, cuisine, and meal type
2. **Search**: Full-text search across title and ingredients
3. **Filter**: Filter by cuisine and meal type
4. **Responsive UI**: Works on mobile (320px) through desktop (1920px)
5. **Persistent storage**: Recipes survive page refresh (SQLite or JSON file)

## Tech Stack
- Backend: Node.js with Express
- Frontend: Single HTML page with vanilla JS
- Database: SQLite via better-sqlite3
```

### ARCHITECTURE.md (optional)

For brownfield projects or complex stacks, add `ARCHITECTURE.md` to the sprint directory to give the planner existing context.

## Sprint Directory Structure

After a sprint completes:

```
sprints/my-sprint/
├── VISION.md                    # Input: what you want
├── PRD.md                       # Input: what must be true
├── ARCHITECTURE.md              # Optional input: existing architecture
├── IMPLEMENTATION_PLAN.md       # Generated: task breakdown
├── VALUE_CHECKLIST.md           # Generated: value delivery tracking
├── DELIVERY_REPORT.md           # Generated: final delivery report
├── .loop_state.json             # State: full loop state (JSON)
├── .loop/                       # Internal: loop artifacts
│   └── verifications/           # Auto-generated test scripts
└── <project files>              # The actual deliverable
```

## Configuration

All configuration is via `LoopConfig` dataclass fields. Key options:

| Option | Default | Description |
|--------|---------|-------------|
| `max_iterations` | 200 | Safety valve — max loop iterations |
| `max_fix_attempts` | 3 | Times to retry a failing verification |
| `token_budget` | 0 (unlimited) | Token spending limit |
| `model_reasoning` | `claude-opus-4-6` | Model for planning, review, evaluation |
| `model_execution` | `claude-sonnet-4-5-20250929` | Model for building |
| `generate_docs` | `true` | Auto-generate README/ARCHITECTURE post-delivery |
| `browser_eval_headless` | `false` | Run Playwright evaluation headless |

## Resuming a Sprint

The loop persists all state to `.loop_state.json`. If interrupted, just run the same command again — it picks up where it left off.

```bash
# Resumes automatically from saved state
telic-loop my-sprint
```

### Surgical Reset

To re-run a specific phase, edit `.loop_state.json` directly:

| Phase to re-test | What to reset |
|------------------|---------------|
| Planning | Remove `plan_generated` from `gates_passed`, clear `tasks` |
| Review | Remove `plan_reviewed` from `gates_passed` |
| Implementation | Reset target tasks' `status` to `"pending"` |
| Verification | Clear `verifications`, delete `.loop/verifications/` |
| Evaluation | Remove `critical_eval_passed` from `gates_passed` |

### Full Reset

```bash
rm -rf sprints/my-sprint/.loop_state.json sprints/my-sprint/.loop
git branch -D $(git branch | grep my-sprint)
```

## Project Structure

```
telic-loop/
├── src/telic_loop/
│   ├── main.py          # Core loop + phase logic + CLI
│   ├── agent.py         # Claude SDK wrapper + role factory
│   ├── tools.py         # Tool schemas + validation + handlers
│   ├── state.py         # State dataclasses + persistence
│   ├── config.py        # Configuration with defaults
│   ├── git.py           # Git operations (branch, commit, rollback)
│   ├── render.py        # Markdown artifact generation
│   ├── testing.py       # Cross-platform test execution
│   ├── tool_cli.py      # Tool CLI bridge
│   ├── errors.py        # Error classification + crash logging
│   └── prompts/         # 5 prompt templates (system, planner, reviewer, builder, evaluator)
├── AGENT_INSTRUCTIONS.md # Instructions for agents/projects using telic-loop
├── run_e2e.py           # E2E test runner (development only)
├── pyproject.toml
└── CLAUDE.md            # Development guide
```

## Platform Support

Telic Loop runs on **macOS**, **Windows**, and **Linux**. The codebase uses pathlib for all path handling and explicit UTF-8 encoding for all file I/O. Shell-based verification scripts (`.sh`) require `bash` to be available on PATH (included by default on macOS and Linux; on Windows, Git Bash provides this).

## License

MIT
