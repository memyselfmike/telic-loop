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
