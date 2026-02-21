"""Generate markdown artifacts (IMPLEMENTATION_PLAN, VALUE_CHECKLIST, DELIVERY_REPORT) from structured state."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import LoopConfig
    from .state import LoopState


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
            if t.status == "done":
                check = "x"
            elif t.status == "blocked":
                check = "B"
            else:
                check = " "
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
        status_icon = {"done": "[x]", "blocked": "[B]", "descoped": "[D]"}.get(t.status, "[ ]")
        lines.append(f"- {status_icon} **{t.task_id}**: {t.description}")

    lines.append("\n## Verifications")
    for v in state.verifications.values():
        status_icon = {"passed": "[x]", "failed": "[!]"}.get(v.status, "[ ]")
        lines.append(f"- {status_icon} {v.verification_id} ({v.category})")

    config.value_checklist.parent.mkdir(parents=True, exist_ok=True)
    config.value_checklist.write_text("\n".join(lines), encoding="utf-8")


def generate_delivery_report(config: LoopConfig, state: LoopState) -> None:
    """Generate DELIVERY_REPORT.md from full state."""
    from .git import git_commit

    vrc = state.latest_vrc
    passed = len([v for v in state.verifications.values() if v.status == "passed"])
    done = len([t for t in state.tasks.values() if t.status == "done"])

    lines = [
        f"# Delivery Report: {config.sprint}",
        "",
        "## Summary",
        f"- Value score: {vrc.value_score:.0%}" if vrc else "- Value score: N/A",
        f"- Tasks completed: {done}/{len(state.tasks)}",
        f"- QC checks: {passed}/{len(state.verifications)} passing",
        f"- Iterations: {state.iteration}",
        f"- Exit gate attempts: {state.exit_gate_attempts_total}",
        f"- Tokens used: {state.total_tokens_used:,}"
        f" ({state.total_input_tokens:,} in / {state.total_output_tokens:,} out)",
        "",
    ]

    # Phase usage breakdown
    phase_stats: dict[str, dict] = {}
    for entry in state.progress_log:
        phase = entry.get("action", "unknown")
        inp = entry.get("input_tokens", 0)
        out = entry.get("output_tokens", 0)
        dur = entry.get("duration_sec", 0.0)
        if phase not in phase_stats:
            phase_stats[phase] = {"calls": 0, "input": 0, "output": 0, "time": 0.0}
        phase_stats[phase]["calls"] += 1
        phase_stats[phase]["input"] += inp
        phase_stats[phase]["output"] += out
        phase_stats[phase]["time"] += dur

    if phase_stats:
        lines.append("## Phase Usage")
        lines.append("")
        lines.append("| Phase | Calls | Input Tokens | Output Tokens | Time |")
        lines.append("|-------|-------|-------------|--------------|------|")
        for phase, s in sorted(
            phase_stats.items(),
            key=lambda x: x[1]["input"] + x[1]["output"],
            reverse=True,
        ):
            mins, secs = divmod(int(s["time"]), 60)
            time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
            lines.append(
                f"| {phase} | {s['calls']} | {s['input']:,} | {s['output']:,} | {time_str} |"
            )
        lines.append("")

    # Crash summary
    if state.crash_log:
        lines.append("## Crash Summary")
        lines.append("")
        lines.append(f"Total crashes: {len(state.crash_log)}")
        lines.append("")
        lines.append("| Time | Phase | Type | Error |")
        lines.append("|------|-------|------|-------|")
        for crash in state.crash_log:
            ts = crash.get("timestamp", "?")[:19]
            phase = crash.get("phase", "?")
            ctype = crash.get("crash_type", "?")
            error = crash.get("error", "?")[:80]
            lines.append(f"| {ts} | {phase} | {ctype} | {error} |")
        lines.append("")

    # Docker section
    docker = state.context.docker
    if docker.get("enabled"):
        lines.append("## Docker Environment")
        lines.append(f"- Mode: Docker containers")
        compose = docker.get("compose_file", "docker-compose.yml")
        lines.append(f"- Compose file: {compose}")
        lines.append(f"- Scripts: {docker.get('scripts_dir', '.telic-docker')}/")
        for svc in docker.get("services", []):
            if isinstance(svc, dict):
                lines.append(f"  - {svc.get('name', '?')}: port {svc.get('port', '?')}")
            else:
                lines.append(f"  - {svc}")
        lines.append("")

    lines += [
        "## Deliverables",
    ]
    for t in state.tasks.values():
        status = {
            "done": "DELIVERED",
            "descoped": "DESCOPED",
            "blocked": "BLOCKED",
        }.get(t.status, t.status)
        lines.append(f"- [{status}] {t.task_id}: {t.description}")
        if t.status == "descoped":
            lines.append(f"  Reason: {t.blocked_reason}")

    report_path = config.sprint_dir / "DELIVERY_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")

    # Docker cleanup — stop containers after delivery
    _cleanup_docker(config, state)

    git_commit(
        config, state,
        f"telic-loop({config.sprint}): Delivery complete"
        + (f" -- {vrc.value_score:.0%} value" if vrc else ""),
    )


def _cleanup_docker(config: LoopConfig, state: LoopState) -> None:
    """Stop Docker containers after delivery report is generated."""
    import subprocess

    docker = state.context.docker
    if not docker.get("enabled"):
        return

    scripts_dir = config.effective_project_dir / docker.get("scripts_dir", ".telic-docker")
    docker_down = scripts_dir / "docker-down.sh"
    if not docker_down.exists():
        return

    try:
        subprocess.run(
            ["bash", str(docker_down)],
            capture_output=True, text=True, timeout=60,
            cwd=str(config.effective_project_dir),
        )
        print("  Docker containers stopped")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        print(f"  Docker cleanup warning: {exc}")
