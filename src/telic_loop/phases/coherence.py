"""System coherence evaluation (quick + full)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import CoherenceReport, LoopState


def quick_coherence_check(config: LoopConfig, state: LoopState) -> CoherenceReport | None:
    """Quick coherence check: Dimensions 1 (Structural Integrity) and 2 (Interaction Coherence).

    Automated analysis — no LLM invocation needed.
    Runs every coherence_quick_interval tasks.
    """
    from ..state import CoherenceReport

    state.tasks_since_last_coherence += 1
    if state.tasks_since_last_coherence < config.coherence_quick_interval:
        return None

    state.tasks_since_last_coherence = 0
    timestamp = datetime.now().isoformat()

    structural = _assess_structural_integrity(config)
    interaction = _assess_interaction_coherence(config, state)

    statuses = [structural["status"], interaction["status"]]
    if "CRITICAL" in statuses:
        overall = "CRITICAL"
    elif "WARNING" in statuses:
        overall = "WARNING"
    else:
        overall = "HEALTHY"

    report = CoherenceReport(
        iteration=state.iteration,
        mode="quick",
        timestamp=timestamp,
        dimensions={
            "structural_integrity": structural,
            "interaction_coherence": interaction,
        },
        overall=overall,
    )
    state.coherence_history.append(report)

    if overall == "CRITICAL":
        print("  COHERENCE CRITICAL — structural issues detected")
        state.coherence_critical_pending = True

    return report


def do_full_coherence_eval(
    config: LoopConfig, state: LoopState, claude: Claude,
) -> bool:
    """Full 7-dimension coherence evaluation using Opus.

    Runs at epic boundaries and pre-exit-gate.
    """
    from ..claude import AgentRole, load_prompt
    from ..state import CoherenceReport

    previous = state.coherence_history[-1] if state.coherence_history else None

    session = claude.session(
        AgentRole.EVALUATOR,
        system_extra=(
            "Evaluate system-level coherence across all 7 dimensions. "
            "Focus on emergent properties: issues that arise from feature "
            "INTERACTIONS, not from any individual feature being wrong."
        ),
    )

    prompt = load_prompt("coherence_eval",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        EVAL_MODE="full",
        ITERATION=state.iteration,
        FEATURE_COUNT=sum(1 for t in state.tasks.values() if t.status == "done"),
        PREVIOUS_REPORT=(
            json.dumps(previous.__dict__) if previous else "None (first evaluation)"
        ),
    )
    session.send(prompt)

    result = state.agent_results.get("coherence")
    if result:
        report = CoherenceReport(
            iteration=state.iteration,
            mode="full",
            timestamp=datetime.now().isoformat(),
            dimensions=result.get("dimensions", {}),
            overall=result.get("overall", "HEALTHY"),
            top_findings=result.get("top_findings", []),
        )
        state.coherence_history.append(report)
        state.tasks_since_last_coherence = 0
        state.coherence_critical_pending = False

        if report.overall == "CRITICAL":
            print("  COHERENCE CRITICAL — system-level issues detected")

        return report.overall != "HEALTHY"

    state.coherence_critical_pending = False
    return False


# ---------------------------------------------------------------------------
# Automated dimension assessors
# ---------------------------------------------------------------------------

def _assess_structural_integrity(config: LoopConfig) -> dict:
    """Analyze project structure for dependency issues and module health. No LLM."""
    findings: list[str] = []
    project_dir = config.effective_project_dir

    py_files = list(project_dir.rglob("*.py"))

    # Check for circular imports
    import_graph: dict[str, list[str]] = {}
    for f in py_files:
        try:
            content = f.read_text(errors="ignore")
            imports = [
                line.split()[1].split(".")[0]
                for line in content.split("\n")
                if line.startswith("import ") or line.startswith("from ")
            ]
            import_graph[f.stem] = imports
        except Exception:
            continue

    for module, imports in import_graph.items():
        for imp in imports:
            if imp in import_graph and module in import_graph.get(imp, []):
                findings.append(f"Circular import: {module} <-> {imp}")

    # Check for large modules (files > 500 lines)
    for f in py_files:
        try:
            lines = len(f.read_text(errors="ignore").split("\n"))
            if lines > 500:
                findings.append(f"Large module ({lines} lines): {f.name}")
        except Exception:
            continue

    status = "WARNING" if findings else "HEALTHY"
    return {"status": status, "findings": findings, "trend": "stable"}


def _assess_interaction_coherence(config: LoopConfig, state: LoopState) -> dict:
    """Check cross-cutting concern consistency. No LLM."""
    findings: list[str] = []
    project_dir = config.effective_project_dir

    py_files = list(project_dir.rglob("*.py"))

    # Check for inconsistent error handling patterns
    bare_excepts = 0
    specific_excepts = 0
    for f in py_files:
        try:
            content = f.read_text(errors="ignore")
            bare_excepts += content.count("except:")
            bare_excepts += content.count("except Exception:")
            specific_excepts += (
                content.count("except ") - content.count("except:")
                - content.count("except Exception:")
            )
        except Exception:
            continue

    if bare_excepts > specific_excepts and bare_excepts > 3:
        findings.append(
            f"Inconsistent error handling: {bare_excepts} bare/generic excepts "
            f"vs {specific_excepts} specific"
        )

    # Check task churn (tasks oscillating between states)
    churn_tasks = [t for t in state.tasks.values() if t.retry_count >= 3]
    if churn_tasks:
        findings.append(
            f"{len(churn_tasks)} tasks with 3+ retries — potential interaction issue"
        )

    status = "WARNING" if findings else "HEALTHY"
    if any("churn" in f for f in findings):
        status = "CRITICAL"
    return {"status": status, "findings": findings, "trend": "stable"}
