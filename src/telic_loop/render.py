"""Generate markdown artifacts (IMPLEMENTATION_PLAN, VALUE_CHECKLIST, DELIVERY_REPORT) from structured state."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import LoopConfig
    from .state import LoopState

# Centralized status icon maps
_TASK_ICONS = {"done": "x", "blocked": "B", "descoped": "D"}
_TASK_CHECKLIST_ICONS = {"done": "[x]", "blocked": "[B]", "descoped": "[D]"}
_VERIFICATION_ICONS = {"passed": "[x]", "failed": "[!]"}
_DELIVERABLE_LABELS = {"done": "DELIVERED", "descoped": "DESCOPED", "blocked": "BLOCKED"}


def render_plan_markdown(state: LoopState) -> str:
    """Render the implementation plan from structured state."""
    lines = [
        f"# Implementation Plan (rendered from state)\n",
        f"Generated: {datetime.now().isoformat()}\n",
    ]
    phases: dict[str, list] = {}
    for t in state.tasks.values():
        phases.setdefault(t.phase or "unphased", []).append(t)

    for phase_name, tasks in phases.items():
        lines.append(f"\n## {phase_name.title()}\n")
        for t in sorted(tasks, key=lambda x: x.task_id):
            check = _TASK_ICONS.get(t.status, " ")
            lines.append(f"- [{check}] **{t.task_id}**: {t.description}")
            if t.value:
                lines.append(f"  - Value: {t.value}")
            if t.acceptance:
                lines.append(f"  - Acceptance: {t.acceptance}")
            if t.dependencies:
                lines.append(f"  - Deps: {', '.join(t.dependencies)}")
            lines.append("")
    return "\n".join(lines)


def render_plan_snapshot(config: LoopConfig, state: LoopState) -> None:
    """Re-render the plan markdown from structured state."""
    config.plan_file.parent.mkdir(parents=True, exist_ok=True)
    config.plan_file.write_text(render_plan_markdown(state), encoding="utf-8")


def render_value_checklist(config: LoopConfig, state: LoopState) -> None:
    """Render VALUE_CHECKLIST.md from VRC + task + verification state."""
    lines = [
        f"# Value Checklist: {config.sprint}",
        f"Generated: {datetime.now().isoformat()}\n",
    ]

    vrc = state.latest_vrc
    if vrc:
        lines.append(f"## VRC Status")
        lines.append(f"- Value Score: {vrc.value_score:.0%}")
        lines.append(f"- Verified: {vrc.deliverables_verified}/{vrc.deliverables_total}")
        lines.append(f"- Blocked: {vrc.deliverables_blocked}")
        lines.append(f"- Recommendation: {vrc.recommendation}")
        lines.append(f"- Summary: {vrc.summary}")
        lines.append("")

    lines.append("## Tasks")
    for t in state.tasks.values():
        icon = _TASK_CHECKLIST_ICONS.get(t.status, "[ ]")
        lines.append(f"- {icon} **{t.task_id}**: {t.description}")

    lines.append("\n## Verifications")
    for v in state.verifications.values():
        icon = _VERIFICATION_ICONS.get(v.status, "[ ]")
        lines.append(f"- {icon} {v.verification_id} ({v.category})")

    config.value_checklist.parent.mkdir(parents=True, exist_ok=True)
    config.value_checklist.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Delivery report
# ---------------------------------------------------------------------------

def _build_summary_lines(config: LoopConfig, state: LoopState) -> list[str]:
    vrc = state.latest_vrc
    passed = sum(1 for v in state.verifications.values() if v.status == "passed")
    done = sum(1 for t in state.tasks.values() if t.status == "done")
    return [
        f"# Delivery Report: {config.sprint}",
        "",
        "## Summary",
        f"- Value score: {vrc.value_score:.0%}" if vrc else "- Value score: N/A",
        f"- Tasks completed: {done}/{len(state.tasks)}",
        f"- QC checks: {passed}/{len(state.verifications)} passing",
        f"- Iterations: {state.iteration}",
        f"- Exit gate attempts: {state.exit_gate_attempts}",
        f"- Tokens used: {state.total_tokens_used:,}"
        f" ({state.total_input_tokens:,} in / {state.total_output_tokens:,} out)",
        "",
    ]


def _build_phase_usage_lines(state: LoopState) -> list[str]:
    phase_stats: dict[str, dict] = {}
    for entry in state.progress_log:
        phase = entry.get("action", "unknown")
        if phase not in phase_stats:
            phase_stats[phase] = {"calls": 0, "input": 0, "output": 0, "time": 0.0}
        phase_stats[phase]["calls"] += 1
        phase_stats[phase]["input"] += entry.get("input_tokens", 0)
        phase_stats[phase]["output"] += entry.get("output_tokens", 0)
        phase_stats[phase]["time"] += entry.get("duration_sec", 0.0)

    if not phase_stats:
        return []

    lines = [
        "## Phase Usage", "",
        "| Phase | Calls | Input Tokens | Output Tokens | Time |",
        "|-------|-------|-------------|--------------|------|",
    ]
    for phase, s in sorted(phase_stats.items(),
                           key=lambda x: x[1]["input"] + x[1]["output"], reverse=True):
        mins, secs = divmod(int(s["time"]), 60)
        time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
        lines.append(f"| {phase} | {s['calls']} | {s['input']:,} | {s['output']:,} | {time_str} |")
    lines.append("")
    return lines


def _build_crash_summary_lines(state: LoopState) -> list[str]:
    if not state.crash_log:
        return []
    lines = [
        "## Crash Summary", "",
        f"Total crashes: {len(state.crash_log)}", "",
        "| Time | Phase | Type | Error |",
        "|------|-------|------|-------|",
    ]
    for crash in state.crash_log:
        ts = crash.get("timestamp", "?")[:19]
        phase = crash.get("phase", "?")
        ctype = crash.get("crash_type", crash.get("error_kind", "?"))
        error = crash.get("error", "?")[:80]
        lines.append(f"| {ts} | {phase} | {ctype} | {error} |")
    lines.append("")
    return lines


def _build_deliverables_lines(state: LoopState) -> list[str]:
    lines = ["## Deliverables"]
    for t in state.tasks.values():
        label = _DELIVERABLE_LABELS.get(t.status, t.status)
        lines.append(f"- [{label}] {t.task_id}: {t.description}")
        if t.status == "descoped":
            lines.append(f"  Reason: {t.blocked_reason}")
    return lines


def _build_eval_findings_lines(state: LoopState) -> list[str]:
    if not state.evaluation_findings:
        return []
    lines = [
        "## Evaluation Findings", "",
        "| Severity | Description | Evidence | Verdict |",
        "|----------|-------------|----------|---------|",
    ]
    for f in state.evaluation_findings:
        sev = f.get("severity", "?")
        desc = f.get("description", "")[:80]
        evidence = f.get("evidence", "")[:60]
        verdict = f.get("verdict", "")
        # Escape pipes in table cells
        desc = desc.replace("|", "\\|")
        evidence = evidence.replace("|", "\\|")
        lines.append(f"| {sev} | {desc} | {evidence} | {verdict} |")
    lines.append("")
    return lines


def generate_delivery_report(config: LoopConfig, state: LoopState) -> None:
    """Generate DELIVERY_REPORT.md from full state."""
    from .git import git_commit

    lines = _build_summary_lines(config, state)
    lines.extend(_build_phase_usage_lines(state))
    lines.extend(_build_eval_findings_lines(state))
    lines.extend(_build_crash_summary_lines(state))
    lines.extend(_build_deliverables_lines(state))

    report_path = config.sprint_dir / "DELIVERY_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")

    vrc = state.latest_vrc
    git_commit(
        config, state,
        f"telic-loop({config.sprint}): Delivery complete"
        + (f" -- {vrc.value_score:.0%} value" if vrc else ""),
    )
