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

---

## P0: Exit Gate Fail-Fast and Timeout Control

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
2. **Wall-clock cap**: Add a configurable total timeout on the exit gate function (default 15 min). If checks haven't all passed by then, fail and move on. `exit_gate_wall_clock_sec: int = 900` in LoopConfig.
3. **Budget-aware short-circuit**: If token budget > 95%, skip non-essential checks (coherence, code quality) and run only regression + VRC.

**Files**: `phases/exit_gate.py`, `config.py`

**Expected savings**: ~100 min per multi-epic sprint

---

## P1: Per-Role SDK Timeout Configuration

**Problem**: A single global `sdk_query_timeout_sec` (300s) doesn't fit all roles. CLASSIFIER needs 60s. EVALUATOR needs 900s. BUILDER is fine at 300s. Multiple proposals (P0, P5) depend on role-appropriate timeouts.

**Root cause**: `ClaudeSession.timeout_sec` is set from the single `config.sdk_query_timeout_sec` value at `claude.py:151`. No per-role override exists.

**Fix**:
1. Add `sdk_timeout_by_role: dict[str, int]` to LoopConfig with sensible defaults:
   ```python
   sdk_timeout_by_role: dict[str, int] = field(default_factory=lambda: {
       "CLASSIFIER": 60,
       "BUILDER": 300,
       "FIXER": 300,
       "QC": 300,
       "REASONER": 300,
       "EVALUATOR": 900,
       "RESEARCHER": 300,
   })
   ```
2. In `Claude.session()`, look up `role.name` in the dict, falling back to the global default.

**Files**: `config.py`, `claude.py`

**Expected savings**: Enables P0 and P5 to work correctly. Prevents EVALUATOR timeouts without bloating timeout for fast roles.

---

## P2: Prevent Concurrent Loop Instances

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

## P3: Smarter VRC Frequency

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

## P4: Quality Task Auto-Descope Fix

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

## P5: Reliable Playwright Critical Evaluation

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

## P6: QC Generation Guard Audit

**Problem**: QC generation fired 3 times at iterations 8-10 with no completed tasks, wasting 17 min.

**Root cause**: The `min 3 tasks` guard at decision.py line 82-87 should prevent premature QC, but it triggered anyway. Likely the guard counts tasks from across all epics rather than scoped to the current epic, or the `generate_verifications_after` config (default 1) overrides `min_for_qc`.

**Fix**:
1. Audit `decide_next_action()` P3 logic (decision.py lines 78-88) to confirm it uses `_scoped_tasks()` for the done count, not global tasks.
2. Ensure `min_for_qc = min(3, len(scoped))` cannot evaluate to 0 or 1 for a new epic with no completed tasks.
3. Add a guard: don't attempt QC generation if 0 tasks have been completed in the current epic.

**Files**: `decision.py`

**Expected savings**: ~17 min per sprint (eliminates pointless early QC attempts)

---

## P7: VRC Accuracy and Skepticism

**Problem**: VRC reported 100% SHIP_READY for beep2b, but the Sanity CMS integration was non-functional (`projectId='placeholder'`, no real project created). Graceful degradation (showing fallback content) masked the failure — pages rendered without errors, so VRC counted them as working. This is a systemic gap: VRC verifies that deliverables **render** but not that they **function**.

**Root cause**: VRC evaluates deliverables by checking whether they exist and produce output, not whether external integrations actually connect. A page showing "No posts yet" scores the same as a page with real CMS data.

**Fix** (project-agnostic — applies to any project with external dependencies):
1. **VRC service skepticism prompt**: When `state.context.services` is non-empty, add a VRC prompt clause: "External services are configured. Verify that deliverables show REAL data from these services, not fallback/placeholder content. A CMS page showing 'No posts yet' or a dashboard showing sample data is NOT verified — it may indicate a missing connection."
2. **Integration smoke test in critical eval**: Before the visual review, the critical evaluator should check: are external services responding with real data? Does the CMS have content? Does the API return non-empty responses? Flag placeholder/fallback content as a `blocking` gap.
3. **Exit gate service health upgrade**: Extend `_all_services_healthy()` (decision.py line 166) to check semantic correctness: not just "port is open" or "HTTP 200" but "response contains expected data structure." For example, a CMS health check should verify the content API returns at least one document.
4. **VRC re-evaluation trigger**: If `exit_gate` has failed 2+ times but VRC still shows >= 90%, force VRC to re-evaluate with increased skepticism prompt weight.

**Files**: `prompts/vrc.md`, `phases/critical_eval.py`, `decision.py` (`_all_services_healthy`), `phases/exit_gate.py`

**Expected impact**: Prevents shipping "working" code that doesn't actually work. Catches integration gaps where graceful degradation masks failures.
