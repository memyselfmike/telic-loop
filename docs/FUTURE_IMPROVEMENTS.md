# Future Improvements

## Project-Aware Loop (IMPLEMENTED)

Added `project_dir` concept to separate application code (project root) from loop management artifacts (sprint directory). See `config.py:effective_project_dir`. Usage: `telic-loop <sprint> --project-dir /path/to/project`.

---

## Pre-compute Context Discovery Inputs (IMPLEMENTED)

Pre-computes tool versions, project markers, file tree with line counts, test file detection, and service indicators in Python before the LLM session. Data injected into `discover_context.md` prompt via `{PRECOMPUTED_ENV}` placeholder. Steps 2/4/5 simplified to reference pre-computed data. Expected reduction: ~30 turns → ~5 turns.

See `discovery.py:_precompute_environment()` and helpers.

---

## Zero-Debt Shipping (IMPLEMENTED)

Tightened exit gate to prevent shipping with unresolved VRC gaps. VRC `SHIP_READY` now requires ALL deliverables verified with no critical, blocking, or degraded gaps. Exit gate step 2b deterministically blocks shipping if unresolved degraded+ gaps remain, auto-creating tasks for each gap. VRC full evaluations auto-create tasks for gaps rated `critical` or `blocking`.

See `phases/exit_gate.py`, `phases/vrc.py`, `prompts/vrc.md`, `prompts/exit_gate.md`.

---

## Task Granularity Enforcement (IMPLEMENTED)

Prevents task bloat that degraded builder effectiveness in multi-epic sprints. Hard limits: 600 char description max, 5 files_expected max — enforced deterministically in `validate_task_mutation()`. Prescriptive sizing rules in `plan.md` prompt (Single Concern Rule, API Rule, Frontend Rule). Builder scope fence in `execute.md` prevents over-delivery across task boundaries.

See `tools.py:validate_task_mutation()`, `config.py:max_task_description_chars/max_files_per_task`, `prompts/plan.md`, `prompts/execute.md`.

---

## Per-Phase Token and Time Tracking (IMPLEMENTED)

Breaks down token usage and wall-clock time per phase (execute, qc, vrc, etc.). `LoopState.record_progress()` enriched with `input_tokens`, `output_tokens`, `duration_sec`. Delivery report includes Phase Usage table sorted by total tokens. Input/output tokens tracked separately in `ClaudeSession` via `ResultMessage.usage`.

See `state.py:record_progress()`, `claude.py:_send_async()/_sync_state()`, `main.py`, `render.py:generate_delivery_report()`.

---

## Self-Healing Loop (IMPLEMENTED)

Three layers of crash resilience: (1) `asyncio.timeout()` on SDK `query()` calls prevents infinite hangs (default 300s). (2) Handler-level try/except catches phase crashes, resets in_progress tasks to pending, saves state, and continues to next iteration. (3) Auto-restart wrapper in `main()` retries catastrophic crashes with linear backoff (10s, 20s, 30s), up to 3 attempts.

See `claude.py:_send_async()`, `main.py:run_value_loop()/main()/_run_main()`, `config.py:sdk_query_timeout_sec/max_crash_restarts`.

---

## Deterministic Code Quality Checks (IMPLEMENTED)

Six zero-LLM code health checks run by process monitor: MONOLITH (files >= 500 lines), RAPID_GROWTH (> 50% growth between iterations), CONCENTRATION (> 60% of code in one file), LONG_FUNCTION (functions > 50 lines), DUPLICATE blocks (>= 8 identical lines across files), LOW_TEST_RATIO (test:source ratio < 0.5). Exit gate hard-blocks shipping if monolithic files remain (`code_health_enforce_at_exit`). Auto-creates REFACTOR-* tasks for files exceeding thresholds.

See `phases/process_monitor.py:scan_file_line_counts()/format_code_health()/create_refactoring_tasks()`, `phases/exit_gate.py`, `config.py:code_health_*`.

---

# Backlog — Beep2b Post-Mortem (2026-02-19)

Sprint stats: 63 iterations, 1.1M tokens, 6.2 hrs wall clock. **53% of time wasted** on timeouts, crashes, and concurrent instances. Despite this, delivered 35/36 tasks at 100% VRC. Analysis below identifies 6 improvements ranked by impact.

---

## P0: Fix Exit Gate Timeouts

**Problem**: Exit gate is the #1 time sink — 6 attempts, ALL failed as `no_progress`, 100 min wasted (27% of total runtime), 106K tokens burned. Each attempt takes 17-20 min. The gate eventually only passed via the safety valve (auto-pass after `max_exit_gate_attempts`), meaning it **never actually verified** the output.

**Root cause**: The gate runs 5 checks sequentially, each spawning a full SDK session: coherence eval → regression sweep → fresh VRC → critical eval → code quality. Critical eval alone takes 10+ min (Playwright browser evaluation). The total consistently exceeds any reasonable timeout.

**Evidence** (from progress log):
```
iter=29  exit_gate  1036s (17min) no_progress
iter=30  exit_gate  1096s (18min) no_progress
iter=32  exit_gate  1165s (19min) no_progress
iter=60  exit_gate  1222s (20min) no_progress
iter=61  exit_gate   313s  (5min) no_progress
iter=63  exit_gate  1155s (19min) no_progress
```

**Fix**:
1. **Fail fast**: If coherence or regression fails, skip later checks and return immediately (currently runs all 5 even after early failure).
2. **Lightweight critical eval at exit gate**: Replace full Playwright browser evaluation with a build-only check (`npm run build` exit code 0). Reserve heavy browser eval for epic boundaries only.
3. **Wall-clock cap**: Add a total timeout on the entire exit gate function (e.g. 10 min). If it hasn't passed all checks by then, fail and move on.
4. **Per-check timeouts**: Give each sub-check its own timeout (e.g. coherence=2min, regression=3min, VRC=2min, critical=3min, quality=1min) instead of letting one check consume all time.

**Files**: `phases/exit_gate.py`, `phases/critical_eval.py`, `config.py`

**Expected savings**: ~100 min per multi-epic sprint

---

## P1: Fix Critical Eval Timeouts

**Problem**: Critical eval timed out at 600s (SDK timeout) on **every single invocation** — 4 attempts, 39 min wasted, 33K tokens. It never successfully completed. This means critical evaluation provided zero value during the entire sprint.

**Root cause**: Critical eval likely spawns Playwright to evaluate the live site, requiring: start dev server → wait for ready → navigate pages → take screenshots → analyze. This exceeds the 5-min SDK timeout.

**Evidence**:
```
iter=28  critical_eval  600s (10min) no_progress
iter=46  critical_eval  600s (10min) no_progress
iter=54  critical_eval  600s (10min) no_progress
iter=58  critical_eval  536s  (9min) no_progress
```

**Fix**:
1. **Increase timeout for critical eval**: Use a role-specific timeout (e.g. 900s) rather than the global `sdk_query_timeout_sec`.
2. **Break into stages**: Static analysis first (file structure, imports, build check) — fast, reliable. Browser evaluation second as a separate SDK session with its own timeout — optional, can fail gracefully.
3. **Pre-warm dev server**: Start the dev server before the SDK session so Playwright doesn't waste time waiting for startup.
4. **Consider skipping browser eval for static sites**: Astro builds to static HTML — `npm run build` success + file content checks may be sufficient. Browser eval adds most value for dynamic SPAs.

**Files**: `phases/critical_eval.py`, `claude.py` (per-role timeout), `config.py`

**Expected savings**: ~40 min per sprint

---

## P2: Prevent Concurrent Loop Instances

**Problem**: 10 iterations ran as duplicates (up to 4x concurrent), causing 58 min wasted time, 93K wasted tokens, and state file corruption. User saw "playwright firing up over and over" from multiple competing instances.

**Root cause**: `run_beep2b.py` (custom launcher) calls `run_epic_loop()` directly, bypassing the lock file mechanism in `main.py:_acquire_lock()`. Multiple background Task tool invocations each launched a separate `python run_beep2b.py` process.

**Evidence** (duplicate iterations in progress log):
```
Iteration 40: 2 entries
Iteration 42: 3 entries
Iteration 43: 2 entries
Iteration 45: 4 entries  ← four concurrent instances!
Iteration 46: 3 entries
```

**Fix**:
1. **Move lock acquisition into `run_epic_loop()`**: Lock at the epic loop level, not just `main()`. Any entry point (main, run_e2e.py, custom launchers) gets locking for free.
2. **OS-level file locking**: Replace the current PID-based lock with `fcntl.flock()` (Unix) / `msvcrt.locking()` (Windows) for atomic lock acquisition. Current PID check has TOCTOU race conditions.
3. **Startup process check**: On launch, scan for existing `python run_*.py` or `telic_loop` processes and abort if found.

**Files**: `main.py`, `phases/epic.py`, potentially a new `locking.py` module

**Expected savings**: ~58 min per sprint + prevents state corruption

---

## P3: Reduce Startup Tax

**Problem**: Iterations 1-10 achieved only 40% progress rate, burning 52 min before real execution began. Service fixes and QC generation failures dominate early iterations.

**Root cause**:
- `service_fix` triggers at iter 1 before any tasks exist — tries to start dev servers that aren't needed yet
- `generate_qc` triggers at iters 8-10 despite the `min 3 tasks` guard in decision.py — possibly the guard counts tasks from a previous epic or the counter wasn't properly scoped

**Evidence**:
```
Epic 1 startup (iters 1-10): 4/10 progress (40%), 52 min
Epic 1 execution (iters 11-27): 15/16 progress (94%), 49 min  ← night and day
```

**Fix**:
1. **Defer service discovery**: Don't run service detection until after the first EXECUTE action creates something to serve. Context discovery already identifies project type — don't try to start servers until files exist.
2. **QC generation guard audit**: Trace why `generate_qc` fired at iter 8 with no completed tasks. The `min 3 tasks` guard may not be counting correctly for the first epic.
3. **Brownfield detection**: Beep2b was brownfield (existing scaffold). The service fixer tried to start servers for a project that was already configured. Detect existing `package.json` scripts and skip service setup.

**Files**: `phases/execute.py` (service detection), `decision.py` (QC guard), `discovery.py`

**Expected savings**: ~30 min per sprint

---

## P4: Smarter VRC Frequency

**Problem**: 70 VRC evaluations for 63 iterations. VRC runs after every action — including timeouts, crashes, and failed service fixes. Many consecutive VRCs return identical scores (e.g. VRC #6 through #15 all returned 25%).

**Root cause**: `run_vrc()` is called unconditionally after every action in the value loop (main.py line 144), skipping only after `exit_gate` and during `pause`.

**Fix**:
1. **Skip VRC when no tasks changed**: Track `last_vrc_task_hash` (hash of task statuses). If no task changed status since last VRC, skip.
2. **Skip VRC after failed actions**: If `progress=False`, no work was done — VRC score can't have changed.
3. **Minimum interval**: Don't run VRC more than once every N minutes (e.g. 3 min) unless a task was completed.
4. **Lightweight vs full**: Currently uses `force_full` after critical eval and course correction. For regular heartbeats, use a cheaper "did any tasks complete since last check?" heuristic before spawning a full LLM evaluation.

**Files**: `main.py` (VRC call site), `phases/vrc.py`, `state.py` (tracking hash)

**Expected savings**: ~20-30 VRC calls eliminated per sprint (~50K tokens)

---

## P5: PRD Structure False Positive Prevention

**Problem**: The STRUCTURE-prd-conformance task was reopened 5 times before auto-descoping. It detected "missing" `tailwind.config.mjs` which doesn't exist in Tailwind v4 (uses `@tailwindcss/vite` instead). The infinite reopen cycle consumed execution iterations and delayed exit gate.

**Root cause**: `_scan_prd_structure()` in code_quality.py parses the PRD's file tree literally. It doesn't understand framework-specific alternatives (e.g. Tailwind v4 removed the config file in favor of CSS-first configuration).

**Fix**:
1. **Framework-aware exceptions**: When the project uses `@tailwindcss/vite` (detected in astro.config or package.json), suppress `tailwind.config.mjs` from the required files list.
2. **Builder feedback loop**: When the builder marks STRUCTURE-prd-conformance as done with a note like "not applicable — Tailwind v4", the code quality system should accept the explanation rather than reopening.
3. **Reduce retry cap**: The auto-descope threshold of 2 retries eventually caught it, but the task had `retry_count=5` — suggesting the retry cap was added mid-sprint. Verify the cap is working correctly from the start.

**Files**: `phases/code_quality.py` (`_scan_prd_structure`, `_upsert_task`)

**Expected savings**: ~5-10 wasted iterations per sprint with novel frameworks
