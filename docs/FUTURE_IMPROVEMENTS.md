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

Sprint stats: 63 iterations, 1.1M tokens, 6.2 hrs wall clock. **53% of time wasted** on timeouts, crashes, and concurrent instances. Despite this, delivered 35/36 tasks at 100% VRC. Analysis below identifies improvements ranked by impact.

Quality-gated: CRAP + CONNECT + project-agnostic review applied 2026-02-19. Original P1 merged into P5, original P7 merged into P5, P3/P5/P8 revised to remove framework-specific logic.

**Implementation status (2026-02-19)**: P0 DONE, P1 DONE, P2 DONE, P3 DONE, P4 DONE, P5 PARTIAL (artifact cleanup done; staged eval/pre-warm TODO), P6 DONE, P7 DONE.

### Implementation philosophy: Measure first, constrain second

The beep2b sprint data is from a buggy run with concurrent instances, state corruption, and missing fixes. Timeouts derived from that data would be unreliable. For the next test sprint:

1. **Set generous defaults**: All timeouts should allow functions to complete naturally (e.g. EVALUATOR at 1800s, exit gate wall-clock at 30 min). We want a clean run, not artificial failures.
2. **Collect real timing data**: Per-phase `record_progress()` already tracks `duration_sec` for every action. The delivery report's Phase Usage table gives us exact p50/p95/max per phase.
3. **Tighten after observation**: After a successful clean sprint, use the observed timings to set realistic timeouts with reasonable headroom (e.g. p95 + 50%).

This means P0's wall-clock cap and P1's per-role timeouts should ship with **permissive defaults** that prevent infinite hangs but don't cut off legitimate work. The goal for the next sprint is a fully delivered end-to-end run with no gaps — timing data from that run informs the production-ready thresholds.

---

## P0: Exit Gate Fail-Fast and Timeout Control (IMPLEMENTED)

**Problem**: Exit gate is the #1 time sink — 6 attempts, ALL failed as `no_progress`, 100 min wasted (27% of total runtime), 106K tokens. Each attempt takes 17-20 min. The gate only passed via safety valve, meaning it **never actually verified** the output.

**Root cause**: The gate runs 5 checks sequentially (coherence → regression → VRC → critical eval → code quality), each spawning a full SDK session. If an early check fails, the later (expensive) checks still run. No wall-clock cap exists.

**Evidence**:
```
iter=29  exit_gate  1036s (17min) no_progress
iter=30  exit_gate  1096s (18min) no_progress
iter=32  exit_gate  1165s (19min) no_progress
iter=60  exit_gate  1222s (20min) no_progress
iter=61  exit_gate   313s  (5min) no_progress
iter=63  exit_gate  1155s (19min) no_progress
```

**Fix**:
1. **Fail fast**: If coherence or regression fails, return immediately — skip VRC, critical eval, and code quality. Currently runs all 5 even after early failure.
2. **Wall-clock cap**: Add a configurable total timeout on the exit gate function. Default generous for measurement: `exit_gate_wall_clock_sec: int = 1800` (30 min). Tighten after observing real durations from a clean sprint.
3. **Budget-aware short-circuit**: If token budget > 95%, skip non-essential checks (coherence, code quality) and run only regression + VRC.

**Files**: `phases/exit_gate.py`, `config.py`

**Expected savings**: ~100 min per multi-epic sprint

---

## P1: Per-Role SDK Timeout Configuration (IMPLEMENTED)

**Problem**: A single global `sdk_query_timeout_sec` (300s) doesn't fit all roles. CLASSIFIER needs 60s. EVALUATOR needs 900s. BUILDER is fine at 300s. Multiple proposals (P0, P5) depend on role-appropriate timeouts.

**Root cause**: `ClaudeSession.timeout_sec` is set from the single `config.sdk_query_timeout_sec` value at `claude.py:151`. No per-role override exists.

**Fix**:
1. Add `sdk_timeout_by_role: dict[str, int]` to LoopConfig with generous defaults for measurement:
   ```python
   sdk_timeout_by_role: dict[str, int] = field(default_factory=lambda: {
       "CLASSIFIER": 120,
       "BUILDER": 600,
       "FIXER": 600,
       "QC": 600,
       "REASONER": 600,
       "EVALUATOR": 1800,   # 30 min — Playwright page-by-page review
       "RESEARCHER": 600,
   })
   ```
   These are intentionally generous. After a clean test sprint, tighten based on observed p95 + 50% headroom from the delivery report's Phase Usage table.
2. In `Claude.session()`, look up `role.name` in the dict, falling back to the global default.

**Files**: `config.py`, `claude.py`

**Expected savings**: Enables P0 and P5 to work correctly. Prevents EVALUATOR timeouts without bloating timeout for fast roles.

---

## P2: Prevent Concurrent Loop Instances (IMPLEMENTED)

**Problem**: 10 iterations ran as duplicates (up to 4x concurrent), causing 58 min wasted time, 93K wasted tokens, and state file corruption.

**Root cause**: `run_beep2b.py` (custom launcher) calls `run_epic_loop()` directly, bypassing the lock file in `main.py:_acquire_lock()`. The lock mechanism works correctly — it's just not applied at the right level.

**Evidence**:
```
Iteration 40: 2 entries
Iteration 42: 3 entries
Iteration 45: 4 entries  ← four concurrent instances!
```

**Fix**:
1. **Move lock acquisition into `run_value_loop()` and `run_epic_loop()`**: Any entry point (main, run_e2e.py, custom launchers) gets locking for free. Accept `lock_path` as parameter, default to `config.sprint_dir / ".loop.lock"`.

That's it. The locking mechanism itself (PID-based `O_CREAT | O_EXCL` with stale PID check) is adequate. The bug is **where** it's called, not **how** it works.

**Files**: `main.py`, `phases/epic.py`

**Expected savings**: ~58 min per sprint + prevents state corruption

---

## P3: Smarter VRC Frequency (IMPLEMENTED)

**Problem**: 70 VRC evaluations for 63 iterations. VRC runs after every action — including timeouts, crashes, and failed service fixes. VRC #6 through #15 all returned 25% (10 identical runs).

**Root cause**: `run_vrc()` called unconditionally after every action in the value loop (main.py line 144).

**Fix** (implement in order):
1. **Skip VRC after failed actions**: If `progress=False`, no work was done — VRC score can't have changed.
2. **Skip VRC when no tasks changed**: Track task status hash. If no task changed status since last VRC, skip.
3. **Minimum interval**: Don't run VRC more than once every 60s unless a task was completed. `vrc_min_interval_sec: int = 60` in LoopConfig.

Note: Sub-item 4 from original plan ("lightweight vs full heuristic") already exists at `vrc.py` lines 29-39. No change needed.

**Files**: `main.py` (VRC call site), `state.py` (task status hash)

**Expected savings**: ~30 VRC calls eliminated per sprint (~50K tokens)

---

## P4: Quality Task Auto-Descope Fix (IMPLEMENTED)

**Problem**: STRUCTURE-prd-conformance task reopened 5 times before auto-descoping. The `_upsert_task()` retry cap (`retry_count >= 2`) was added mid-sprint and the counter wasn't correct. Additionally, `_has_architectural_alternative()` in code_quality.py contains Astro-specific patterns (lines 324-345) that violate project-agnosticism.

**Root cause**: Two separate issues:
1. Auto-descope counter wasn't incrementing correctly — task hit `retry_count=5` despite a cap of 2.
2. `_has_architectural_alternative()` hardcodes framework-specific file patterns (`.astro`, `[...slug].astro`) instead of using a generic mechanism.

**Fix**:
1. **Audit `_upsert_task()` retry counting**: Verify `retry_count` increments on every done→pending reopen. Add logging to trace the lifecycle. The cap should have worked at 2; find out why it didn't.
2. **Builder override mechanism**: Replace framework-specific `_has_architectural_alternative()` with a generic approach: when the builder marks a quality task as done, it can set a `resolution_note` field explaining why the violation is intentional (e.g. "Tailwind v4 uses CSS-first config, no tailwind.config.mjs needed"). If the quality check re-triggers but `resolution_note` is set and `retry_count >= 1`, auto-descope with "Builder provided architectural justification."
3. **Remove Astro-specific code**: Delete the hardcoded Astro file patterns from `_has_architectural_alternative()`. The builder override mechanism replaces them generically.

**Files**: `phases/code_quality.py`, `tools.py` (add `resolution_note` to task complete), `state.py` (TaskState field)

**Expected savings**: Eliminates infinite reopen cycles for any framework, not just Astro/Tailwind.

---

## P5: Reliable Playwright Critical Evaluation (PARTIAL — artifact cleanup done)

*Absorbs original P1 (critical eval timeouts) and P7 (artifact cleanup).*

**Problem**: Critical eval with Playwright timed out 4/4 times (39 min wasted) and never delivered value. However, visual review is **essential** for catching layout issues, broken responsive behavior, and UX gaps that code-only checks miss. The user spotted a dodgy category filter layout that a working critical evaluator should have caught. Additionally, 90+ Playwright screenshots and `.playwright-mcp/` logs littered the project root.

**Root cause**: The evaluator tries to start a dev server, wait for it, navigate pages, screenshot, and analyze — all in one SDK session with a 5-min timeout. Screenshots save to CWD (project root) with no cleanup.

**What the critical evaluator SHOULD do** (project-agnostic for any web deliverable):
1. Navigate every page/route at desktop and mobile viewports
2. Take screenshots and inspect for layout issues, broken components, missing content
3. Test interactive elements (forms, navigation, modals)
4. Compare against PRD/vision to catch intent-vs-implementation gaps
5. File specific, actionable tasks for issues found

**Fix**:
1. **Pre-warm dev server** (gated behind `_needs_browser_eval()`): Start the dev server as a background subprocess BEFORE the SDK session. Wait for port readiness. Pass the URL to the evaluator's prompt. This is project-agnostic — uses existing `state.context.services` which discovery already populated.
2. **Per-role timeout**: EVALUATOR role gets 900s via P1's `sdk_timeout_by_role`. Enough time for a thorough page-by-page review.
3. **Staged evaluation**: Two SDK sessions:
   - (a) **Structural check**: Does it build? Do routes exist? Any console errors? (Fast, deterministic, ~60s)
   - (b) **Visual review**: Playwright page-by-page at desktop + mobile viewports. (Slow, thorough, ~10 min)
   - If (a) fails, skip (b) and return findings immediately.
4. **Retry with narrower scope**: If (b) times out, retry with only the routes changed since the last successful eval (track in state).
5. **Artifact cleanup**: After any phase using Playwright:
   - Delete `*.png` from CWD that weren't there before the phase started
   - Delete `.playwright-mcp/` directory
   - Add `.playwright-mcp/` and `.loop/screenshots/` to `ensure_gitignore()` template
6. **Screenshot directory**: Instruct Playwright to save screenshots to `sprints/<name>/.loop/screenshots/` via evaluator system prompt.

**Files**: `phases/critical_eval.py`, `claude.py` (per-role timeout via P1), `config.py`, `prompts/critical_eval.md`, `prompts/critical_eval_browser.md`, `git.py` (gitignore)

**Expected impact**: Visual QC that actually runs. The difference between "it builds" and "it looks polished."

---

## P6: QC Generation Guard Audit (IMPLEMENTED)

**Problem**: QC generation fired 3 times at iterations 8-10 with no completed tasks, wasting 17 min.

**Root cause**: The `min 3 tasks` guard at decision.py line 82-87 should prevent premature QC, but it triggered anyway. Likely the guard counts tasks from across all epics rather than scoped to the current epic, or the `generate_verifications_after` config (default 1) overrides `min_for_qc`.

**Fix**:
1. Audit `decide_next_action()` P3 logic (decision.py lines 78-88) to confirm it uses `_scoped_tasks()` for the done count, not global tasks.
2. Ensure `min_for_qc = min(3, len(scoped))` cannot evaluate to 0 or 1 for a new epic with no completed tasks.
3. Add a guard: don't attempt QC generation if 0 tasks have been completed in the current epic.

**Files**: `decision.py`

**Expected savings**: ~17 min per sprint (eliminates pointless early QC attempts)

---

## P7: VRC Accuracy and Skepticism (IMPLEMENTED)

**Problem**: VRC reported 100% SHIP_READY for beep2b, but the Sanity CMS integration was non-functional (`projectId='placeholder'`, no real project created). Graceful degradation (showing fallback content) masked the failure — pages rendered without errors, so VRC counted them as working. This is a systemic gap: VRC verifies that deliverables **render** but not that they **function**.

**Root cause**: VRC evaluates deliverables by checking whether they exist and produce output, not whether external integrations actually connect. A page showing "No posts yet" scores the same as a page with real CMS data.

**Fix** (project-agnostic — applies to any project with external dependencies):
1. **VRC service skepticism prompt**: When `state.context.services` is non-empty, add a VRC prompt clause: "External services are configured. Verify that deliverables show REAL data from these services, not fallback/placeholder content. A CMS page showing 'No posts yet' or a dashboard showing sample data is NOT verified — it may indicate a missing connection."
2. **Integration smoke test in critical eval**: Before the visual review, the critical evaluator should check: are external services responding with real data? Does the CMS have content? Does the API return non-empty responses? Flag placeholder/fallback content as a `blocking` gap.
3. **Exit gate service health upgrade**: Extend `_all_services_healthy()` (decision.py line 166) to check semantic correctness: not just "port is open" or "HTTP 200" but "response contains expected data structure." For example, a CMS health check should verify the content API returns at least one document.
4. **VRC re-evaluation trigger**: If `exit_gate` has failed 2+ times but VRC still shows >= 90%, force VRC to re-evaluate with increased skepticism prompt weight.

**Files**: `prompts/vrc.md`, `phases/critical_eval.py`, `decision.py` (`_all_services_healthy`), `phases/exit_gate.py`

**Expected impact**: Prevents shipping "working" code that doesn't actually work. Catches integration gaps where graceful degradation masks failures.

---

## Docker Containerization Integration (IMPLEMENTED)

When Docker is available and the project benefits from containerization (native dependencies, CMS frameworks, multi-service architectures), the loop now recommends and standardizes Docker usage across all agents. Addresses Windows compatibility issues from beep2b-v2 (`better-sqlite3` native compilation failure with Tina CMS) and beep2b-v3 (Payload CMS + SQLite + Slate/Lexical incompatibility).

**Detection**: `_detect_docker_recommendation()` in `discovery.py` checks Docker availability, compose file existence, native dependency signals (`better-sqlite3`, `sharp`, `canvas`, `bcrypt`, `argon2`), and CMS packages (`payload`, `sanity`, `strapi`, `directus`, `tinacms`, `prisma`). Returns `recommended`, `optional`, `required`, `unavailable`, or `disabled`.

**Script generation**: Pre-loop gate `docker_setup` spawns a BUILDER session with `docker_setup.md` prompt to create `.telic-docker/` directory with standardized management scripts: `docker-up.sh`, `docker-down.sh`, `docker-health.sh`, `docker-logs.sh`. If no `docker-compose.yml` exists, the Builder generates one from sprint context.

**Agent awareness**: `{DOCKER_CONTEXT}` placeholder injected into `system.md` via `_format_docker_context()` in `claude.py`. All agents see Docker mode status, script paths, usage rules, and container service list. Downstream prompts (`execute.md`, `plan.md`, `discover_context.md`, `generate_verifications.md`, `critical_eval_browser.md`) include Docker-specific guidance.

**SERVICE_FIX**: Docker-aware service fix tries `docker-up.sh` script directly (no LLM needed) before falling back to Builder agent with Docker-specific diagnostic context.

**Lifecycle**: Containers stopped via `docker-down.sh` after delivery report generation. Docker environment section included in delivery report.

**CLI**: `--docker-mode auto|always|never` (default: `auto`).

See `discovery.py:_detect_docker_recommendation()`, `phases/preloop.py:_setup_docker_environment()`, `claude.py:_format_docker_context()`, `phases/execute.py:do_service_fix()`, `render.py:_cleanup_docker()`, `config.py:docker_mode/docker_compose_timeout`, `state.py:SprintContext.docker`, `prompts/docker_setup.md`.

---

## Post-Delivery Documentation Generation (IMPLEMENTED)

After the value loop delivers and the exit gate passes, the loop automatically generates or updates production-quality project documentation in the project root. A BUILDER agent reads the codebase, sprint context, and any existing docs, then writes README.md, docs/ARCHITECTURE.md, and Architecture Decision Records (ADRs) in MADR format.

**Pre-computation**: `_precompute_doc_context()` in `phases/docs.py` scans for existing docs inventory, extracts package metadata (from `package.json` or `pyproject.toml`), tech stack from sprint context, and source file tree — reducing agent turns.

**Brownfield-aware**: If docs already exist, the agent reads them first and updates only sections affected by the sprint. Never deletes content that hasn't been verified as stale.

**Non-blocking**: Doc generation failure prints a warning but does NOT block delivery. The delivery report is already committed before docs run.

**Idempotent**: Uses `docs_generated` gate pattern — safe to resume after crash.

**Wired at 3 call sites**: `main.py` (exit gate pass + max iterations), `phases/epic.py` (after all epics complete).

**CLI**: `--no-docs` flag disables documentation generation.

See `phases/docs.py:generate_project_docs()`, `prompts/generate_docs.md`, `config.py:generate_docs`.

---

# Backlog — Beep2b-v3 Post-Mortem (2026-02-21)

Sprint stats: 157 iterations, 1.67M tokens, ~17 hrs wall clock (including 1h46m rate-limit dead time). 44/49 tasks delivered, 5 descoped. VRC 92%. 12 crashes across 3 categories. QC 0/0 for third consecutive web app sprint.

**Implementation status (2026-02-21)**: P0 DONE, P1 DONE, P2 DONE, P3 DONE, P4 DONE.

---

## P0: Rate-Limit Detection + Smart Sleep (IMPLEMENTED)

**Problem**: Claude Max session allowance exhausted at iteration 34 (21:40). Three crash-restart cycles (iters 34-36), then 55 wasted iterations (37-91) burning ~1h46m of wall-clock time with zero progress. The auto-restart wrapper treated rate limits identically to transient failures.

**Root cause**: No distinction between rate-limit errors and other SDK failures. Linear backoff (10s, 20s) is far too short for an hourly reset window.

**Fix**:
1. `RateLimitError` exception class in `claude.py` — detects "You've hit your limit" pattern
2. `_send_async()` raises `RateLimitError` instead of `RuntimeError` for rate limits
3. `send()` does NOT retry on `RateLimitError` — propagates to caller
4. `run_value_loop()` catches `RateLimitError`, parses reset time from hint (e.g. "resets 11pm"), sleeps until window resets (+2min buffer, capped at 2hr)
5. Records `rate_limit_wait` in progress log (not a crash)

**Files**: `claude.py`, `main.py`

---

## P1: Robust Browser Eval Detection (IMPLEMENTED)

**Problem**: `_needs_browser_eval()` returned False for beep2b-v3 because `state.context.environment` was empty (`{}`). Browser critical evaluation was completely skipped. Many visual/UX defects shipped undetected: ~5K lines CSS duplication, Payload CMS admin non-functional, blog error state, 19 debug artifacts.

**Root cause**: `_needs_browser_eval` relied solely on `environment.get("tools_found", [])` which was empty when context discovery didn't populate it.

**Fix**: Three-signal detection:
1. Original: check `environment.tools_found` for "node"/"npx"
2. Fallback: `shutil.which("npx")` — checks PATH directly
3. Fallback: `package.json` exists in `effective_project_dir`

**Files**: `phases/critical_eval.py`

---

## P2: Windows-Compatible QC Runner (IMPLEMENTED)

**Problem**: `run_tests_parallel()` passed `.sh` script paths directly to `subprocess.run()`, which on Windows tries to execute them as Win32 executables → `OSError: [WinError 193]`. QC has been broken for 3 consecutive web app sprints (beep2b, beep2b-v2, beep2b-v3).

**Root cause**: No platform-aware script execution.

**Fix**: `_build_script_command()` routes scripts by extension:
- `.py` → `[sys.executable, script_path]`
- `.sh` → `[bash, script_path]` (finds Git Bash via `shutil.which`)
- Fallback: returns `bash "script"` as shell command
- `FileNotFoundError` caught with descriptive message

**Files**: `phases/execute.py`

---

## P3: Interactive Pause stdin Check (IMPLEMENTED)

**Problem**: Decision engine chose `interactive_pause` at iteration 146, which calls `input()`. In batch/unattended mode, this crashes with `EOFError`. Crashed 5 consecutive times (iters 147-151) before loop recovered.

**Root cause**: No stdin detection before calling `input()`.

**Fix**: `_is_interactive()` checks `sys.stdin.isatty()`. In non-interactive mode, HUMAN_ACTION tasks are descoped with resolution note instead of blocking the loop.

**Files**: `phases/pause.py`

---

## P4: Exit Gate Counter Persistence (IMPLEMENTED)

**Problem**: Delivery report showed "Exit gate attempts: 0" but 6 exit gates actually ran. Counter reset per-epic in `epic.py`.

**Root cause**: `state.exit_gate_attempts` resets at each epic boundary for safety valve logic, but no cumulative counter exists.

**Fix**: Added `exit_gate_attempts_total` to `LoopState`. Incremented alongside per-epic counter. Delivery report uses total.

**Files**: `state.py`, `phases/exit_gate.py`, `render.py`

---

## P5: Coherence Findings → Automatic Task Creation (BACKLOG)

**Problem**: Coherence check found high-leverage issues (5K-line CSS duplication, dead CMS collection) but only logged them — never created remediation tasks. Issues shipped.

**Proposed fix**: When `do_full_coherence_eval` finds findings with `leverage >= 7/10`, auto-create tasks similar to VRC gap→task mechanism. Guard with retry cap to prevent infinite reopen.

**Files**: `phases/coherence.py`, `tools.py`

---

## P6: QC Adaptation for Web Apps (BACKLOG)

**Problem**: `generate_qc` produced zero usable verifications for 3 consecutive web app sprints. The QC generator creates shell scripts that don't match the deliverable type — web apps need HTTP smoke tests and Playwright assertions, not pytest or bash checks.

**Proposed fix**:
1. Inject `deliverable_type` and `project_type` into `generate_verifications.md` prompt
2. For web apps: instruct QC to generate HTTP endpoint checks (curl/fetch) and Playwright assertions
3. Fallback: if agent generates no verifications, create platform-appropriate smoke tests (HTTP 200 checks for all routes)

**Files**: `phases/qc.py`, `prompts/generate_verifications.md`

---

## P7: Token Budget Awareness / Preemptive Rate-Limit Pause (BACKLOG)

**Problem**: Even with smart sleep on rate-limit errors, the loop has no visibility into how close it is to the Claude Max allowance. It only learns about the limit after hitting it.

**Proposed fix**: Track cumulative tokens per time window. If approaching an estimated threshold, proactively pause before the next expensive action (BUILDER, EVALUATOR) to avoid mid-task interruption. Requires estimating the per-window token budget (may need user config).
