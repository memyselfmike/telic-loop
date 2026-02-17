"""Execution pattern monitoring and strategy reasoning."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState, ProcessMonitorState

_SOURCE_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte",
    ".html", ".css", ".scss", ".less",
    ".java", ".kt", ".go", ".rs", ".c", ".cpp", ".h",
    ".rb", ".php", ".sh", ".sql",
}

_SKIP_DIRS: set[str] = {
    ".", "node_modules", "__pycache__", ".venv", "venv",
    ".git", ".tox", "dist", "build", ".next", ".nuxt",
}


def update_process_metrics(state: LoopState, action: str, made_progress: bool) -> None:
    """Layer 0: Update process monitor metrics from current state. Called every iteration."""
    pm = state.process_monitor
    alpha = 0.3

    # Value velocity EMA
    vrc_scores = [v.value_score for v in state.vrc_history]
    vrc_delta = vrc_scores[-1] - vrc_scores[-2] if len(vrc_scores) >= 2 else 0
    pm.value_velocity_ema = alpha * vrc_delta + (1 - alpha) * pm.value_velocity_ema

    # Token efficiency EMA
    if state.iteration > 1:
        avg_tokens_per_iter = state.total_tokens_used / state.iteration
        efficiency = vrc_delta / max(avg_tokens_per_iter, 1)
        pm.token_efficiency_ema = alpha * efficiency + (1 - alpha) * pm.token_efficiency_ema

    # CUSUM for efficiency deviation
    baseline_efficiency = vrc_delta / max(state.total_tokens_used / max(state.iteration, 1), 1)
    pm.cusum_efficiency = max(0, pm.cusum_efficiency + (pm.token_efficiency_ema - baseline_efficiency))

    # Task churn
    for task in state.tasks.values():
        if task.retry_count >= 2:
            pm.churn_counts[task.task_id] = task.retry_count

    # Error hash tracking
    for v in state.verifications.values():
        if v.status == "failed" and v.failures:
            latest = v.failures[-1]
            h = _hash_error(latest.stderr or latest.stdout or "unknown")
            if h not in pm.error_hashes:
                pm.error_hashes[h] = {"count": 0, "tasks": []}
            pm.error_hashes[h]["count"] = len([
                f for f in v.failures
                if _hash_error(f.stderr or f.stdout or "unknown") == h
            ])

    # File touch tracking — rebuild from scratch each time to stay correct.
    # Count how many distinct done tasks touched each file (not per-iteration).
    pm.file_touches = {}
    for task in state.tasks.values():
        if task.status == "done":
            for f in task.files_created + task.files_modified:
                pm.file_touches[f] = pm.file_touches.get(f, 0) + 1


def scan_file_line_counts(state: LoopState, config: LoopConfig) -> None:
    """Scan sprint directory for source files and compute line counts + health warnings."""
    pm = state.process_monitor
    sprint_dir = Path(config.sprint_dir)

    if not sprint_dir.is_dir():
        return

    # Rotate: current → prev
    pm.file_line_counts_prev = dict(pm.file_line_counts)
    pm.file_line_counts = {}

    for path in sprint_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in _SOURCE_EXTENSIONS:
            continue
        # Skip hidden dirs and known junk
        parts = path.relative_to(sprint_dir).parts
        if any(p.startswith(".") or p in _SKIP_DIRS for p in parts[:-1]):
            continue
        try:
            line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError:
            continue
        rel = str(path.relative_to(sprint_dir)).replace("\\", "/")
        pm.file_line_counts[rel] = line_count

    # Generate warnings
    pm.code_health_warnings = []
    total_lines = sum(pm.file_line_counts.values()) or 1

    for rel, lines in pm.file_line_counts.items():
        prev = pm.file_line_counts_prev.get(rel, 0)
        growth = lines - prev

        if lines >= 500:
            pm.code_health_warnings.append(
                f"MONOLITH: {rel} is {lines} lines (threshold: 500)"
            )
        if prev > 0 and growth >= 150:
            pm.code_health_warnings.append(
                f"RAPID_GROWTH: {rel} grew +{growth} lines since last scan "
                f"({prev} → {lines})"
            )
        if lines / total_lines >= 0.50:
            pm.code_health_warnings.append(
                f"CONCENTRATION: {rel} holds {lines / total_lines:.0%} of total code "
                f"({lines}/{total_lines} lines)"
            )


def format_code_health(state: LoopState) -> str:
    """Format code health metrics for prompt injection. Returns empty string if no data."""
    pm = state.process_monitor

    if not pm.file_line_counts:
        return ""

    total_lines = sum(pm.file_line_counts.values())
    file_count = len(pm.file_line_counts)

    # Top 10 files by size with deltas
    ranked = sorted(pm.file_line_counts.items(), key=lambda x: -x[1])[:10]
    file_table = []
    for rel, lines in ranked:
        prev = pm.file_line_counts_prev.get(rel, 0)
        delta = lines - prev
        delta_str = f" (+{delta})" if delta > 0 else (f" ({delta})" if delta < 0 else "")
        file_table.append(f"  {lines:>5} lines{delta_str}  {rel}")

    sections = [
        f"Code Health: {file_count} source files, {total_lines} total lines",
        "Top files by size:",
        "\n".join(file_table),
    ]

    if pm.code_health_warnings:
        sections.append("Warnings:")
        for w in pm.code_health_warnings:
            sections.append(f"  ⚠ {w}")

    return "\n".join(sections)


def evaluate_process_triggers(state: LoopState, config: LoopConfig) -> str:
    """Layer 1: Returns GREEN, YELLOW, or RED."""
    pm = state.process_monitor
    iteration = state.iteration

    # Guards
    if iteration < config.process_monitor_min_iterations:
        return "GREEN"
    if iteration - pm.last_strategy_change_iteration < config.process_monitor_cooldown:
        return "GREEN"
    if config.token_budget:
        budget_pct = state.total_tokens_used / config.token_budget * 100
        if budget_pct >= 95:
            return "GREEN"

    triggers: list[tuple[str, str]] = []

    # Plateau: value velocity below threshold
    if pm.value_velocity_ema < config.pm_plateau_threshold:
        triggers.append(("plateau", "RED"))

    # Churn: task oscillating fail→fix→fail
    max_churn = max(pm.churn_counts.values(), default=0)
    if max_churn >= config.pm_churn_red:
        triggers.append(("churn", "RED"))
    elif max_churn >= config.pm_churn_yellow:
        triggers.append(("churn", "YELLOW"))

    # Error recurrence: same error hash N times
    max_error = max((e["count"] for e in pm.error_hashes.values()), default=0)
    if max_error >= config.pm_error_recurrence:
        triggers.append(("error_recurrence", "RED"))

    # Budget-value divergence
    if config.token_budget:
        budget_pct = state.total_tokens_used / config.token_budget * 100
        value_pct = (
            len([t for t in state.tasks.values() if t.status == "done"])
            / max(len(state.tasks), 1) * 100
        )
        if value_pct > 0 and budget_pct / value_pct >= config.pm_budget_value_ratio:
            triggers.append(("budget_divergence", "RED"))

    # File hotspot
    if pm.file_touches:
        max_touches = max(pm.file_touches.values())
        if max_touches > iteration * (config.pm_file_hotspot_pct / 100):
            triggers.append(("file_hotspot", "YELLOW"))

    # Code health: monolithic files or rapid growth
    if pm.code_health_warnings:
        monolith_count = sum(1 for w in pm.code_health_warnings if w.startswith("MONOLITH"))
        growth_count = sum(1 for w in pm.code_health_warnings if w.startswith("RAPID_GROWTH"))
        if monolith_count >= 3 or growth_count >= 2:
            triggers.append(("code_health", "YELLOW"))

    if any(level == "RED" for _, level in triggers):
        return "RED"
    if any(level == "YELLOW" for _, level in triggers):
        return "YELLOW"
    return "GREEN"


def maybe_run_strategy_reasoner(
    state: LoopState, config: LoopConfig, claude: Claude,
    action: str = "", made_progress: bool = True,
) -> None:
    """Run process monitor: metrics → triggers → strategy reasoner if RED."""
    from ..claude import AgentRole, load_prompt

    pm = state.process_monitor

    # Layer 0: metrics
    update_process_metrics(state, action=action, made_progress=made_progress)
    scan_file_line_counts(state, config)

    if pm.code_health_warnings:
        print(f"\n  CODE HEALTH — {len(pm.code_health_warnings)} warning(s):")
        for w in pm.code_health_warnings[:5]:
            print(f"    ⚠ {w}")

    # Layer 1: triggers
    new_status = evaluate_process_triggers(state, config)
    pm.status = new_status

    if new_status != "RED":
        return

    # Layer 2: Opus Strategy Reasoner
    print("\n  PROCESS MONITOR — RED trigger, invoking Strategy Reasoner")

    session = claude.session(
        AgentRole.REASONER,
        system_extra=load_prompt("process_monitor",
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
            ITERATION=state.iteration,
            BUDGET_PCT=_budget_pct(state, config),
            CURRENT_STRATEGY=json.dumps(pm.current_strategy, indent=2),
            METRICS_DASHBOARD=_format_metrics_dashboard(pm),
            TRIGGER_DETAILS=f"Process monitor status: {pm.status}",
            WINDOW_SIZE=config.process_monitor_min_iterations * 2,
            EXECUTION_HISTORY=_format_recent_history(state, window=config.process_monitor_min_iterations * 2),
            CURRENT_TEST_APPROACH=pm.current_strategy["test_approach"],
            CURRENT_FIX_APPROACH=pm.current_strategy["fix_approach"],
            CURRENT_EXECUTION_ORDER=pm.current_strategy["execution_order"],
            CURRENT_MAX_FIX=pm.current_strategy["max_fix_attempts"],
            CURRENT_RESEARCH_TRIGGER=pm.current_strategy["research_trigger"],
            CURRENT_SCOPE=pm.current_strategy["scope_per_task"],
            CURRENT_TRIAGE=pm.current_strategy["error_triage"],
        ),
    )

    session.send("Analyze process metrics and recommend strategy change.")

    # Result via report_strategy_change tool call
    change = state.agent_results.get("strategy_change")
    if change and change.get("action") == "STRATEGY_CHANGE":
        for dim, value in change.get("changes", {}).items():
            pm.current_strategy[dim] = value
        pm.last_strategy_change_iteration = state.iteration
        pm.strategy_history.append({
            "iteration": state.iteration,
            "changes": change.get("changes", {}),
            "reason": change.get("rationale", ""),
            "pattern": change.get("pattern", ""),
        })
        print(f"  Strategy changed: {change.get('changes', {})}")
    elif change and change.get("action") == "ESCALATE":
        print(f"  Process Monitor ESCALATION: {change.get('rationale', '')}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_error(error_text: str) -> str:
    """Hash an error message for deduplication. Strips line numbers, paths, timestamps."""
    normalized = re.sub(r'line \d+', 'line N', error_text)
    normalized = re.sub(r'[A-Z]:\\[^\s]+|/[^\s]+\.\w+', 'PATH', normalized)
    normalized = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', 'TIMESTAMP', normalized)
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def _budget_pct(state: LoopState, config: LoopConfig) -> float:
    if not config.token_budget:
        return 0.0
    return (state.total_tokens_used / config.token_budget) * 100


def _format_metrics_dashboard(pm: ProcessMonitorState) -> str:
    lines = [
        f"Value velocity (EMA): {pm.value_velocity_ema:.4f}",
        f"Token efficiency (EMA): {pm.token_efficiency_ema:.6f}",
        f"CUSUM efficiency: {pm.cusum_efficiency:.4f}",
        f"Status: {pm.status}",
    ]
    if pm.churn_counts:
        top_churn = sorted(pm.churn_counts.items(), key=lambda x: -x[1])[:5]
        lines.append(f"Task churn (top 5): {', '.join(f'{k}={v}' for k, v in top_churn)}")
    if pm.error_hashes:
        top_errors = sorted(pm.error_hashes.items(), key=lambda x: -x[1]["count"])[:3]
        error_parts = [f"{k}({v['count']}x)" for k, v in top_errors]
        lines.append(
            f"Recurring errors: {len(pm.error_hashes)} unique, "
            f"top: {', '.join(error_parts)}"
        )
    if pm.file_touches:
        hotspots = sorted(pm.file_touches.items(), key=lambda x: -x[1])[:5]
        lines.append(f"File hotspots: {', '.join(f'{k}({v}x)' for k, v in hotspots)}")
    if pm.file_line_counts:
        total = sum(pm.file_line_counts.values())
        lines.append(f"Source files: {len(pm.file_line_counts)}, total lines: {total}")
        top5 = sorted(pm.file_line_counts.items(), key=lambda x: -x[1])[:5]
        lines.append(f"Largest files: {', '.join(f'{k}({v}L)' for k, v in top5)}")
    if pm.code_health_warnings:
        lines.append(f"Code health warnings: {len(pm.code_health_warnings)}")
    return "\n".join(lines)


def _format_recent_history(state: LoopState, window: int = 10) -> str:
    recent = state.progress_log[-window:]
    if not recent:
        return "No execution history yet."
    lines: list[str] = []
    for entry in recent:
        lines.append(f"  [{entry['iteration']}] {entry['action']}: {entry['result']}")
    return "\n".join(lines)
