# Future Improvements

## Project-Aware Loop (IMPLEMENTED)

Added `project_dir` concept to separate application code (project root) from loop management artifacts (sprint directory). See `config.py:effective_project_dir`. Usage: `telic-loop <sprint> --project-dir /path/to/project`.

---

## Pre-compute Context Discovery Inputs (Priority: High)

**Problem**: The context discovery LLM session (Opus REASONER, up to 40 turns) spends most of its time on mechanical environment checks that don't require LLM reasoning. In the recipe-manager sprint, this phase took ~45 minutes — the agent individually checked Python version, pip version, each installed package version, node version, npm version, and probed for tools that weren't installed (cargo, go, docker, pnpm, yarn, uv, etc.). Each check is a separate Opus reasoning turn + Bash subprocess on Windows.

**Observed behavior**: The agent made 30+ individual tool calls for tasks like `python --version`, `pip show fastapi`, `node --version`, `where cargo`, etc. Each call requires a full Opus reasoning cycle (~60-90 sec per turn including API latency).

**Root cause confirmed**: The commands themselves are fast (all complete in <1 sec, even on Windows). The bottleneck is the **number of Opus reasoning turns**, not command execution time. Each tool check follows: Opus reasons what to check (~60s) → formats Bash command → command runs (~200ms) → Opus processes result (~60s) → repeat. With 15-20 tool checks, that's 22-30 minutes just for environment discovery, plus additional turns for reading source files, counting lines, analyzing stubs, etc.

**The prompt's "Be thorough" and "Do NOT be shallow" instructions cause Opus to check every possible tool individually** instead of batching into one compound command. The agent also reads every source file to count lines and assess implementation state — work that isn't needed for the classification task.

**Proposed solution**: Pre-compute all mechanical environment data in Python *before* the LLM session, then inject it into the prompt:

1. **Tool version scan** (Python, one compound bash call):
   - Runtime versions: `python --version`, `node --version`, etc.
   - Installed packages: `pip list --format=json` (one call, all packages)
   - Use timeouts to skip tools that hang (e.g., Docker daemon not running)

2. **Sprint directory scan** (Python pathlib, no subprocess):
   - File listing with sizes/line counts
   - Project marker detection (package.json, pyproject.toml, Cargo.toml, etc.)
   - .env file contents (variable names only)
   - Existing test file detection

3. **Inject into prompt**: "Here is what we already know about the environment: [pre-computed data]. Classify the deliverable, determine verification strategy, write value proofs, and flag unresolved questions."

**Expected improvement**: Session goes from ~30 turns to ~3-5 turns (read Vision, read PRD, call report_discovery). Time reduction from ~45 minutes to ~5 minutes.

**Files to modify**:
- `src/telic_loop/discovery.py` — Add `_precompute_environment()` function
- `src/telic_loop/prompts/discover_context.md` — Add pre-computed data section, remove "check for X" instructions
- Possibly extract shared file scanning logic with `process_monitor.py`
