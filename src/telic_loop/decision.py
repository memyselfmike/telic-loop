"""Decision engine: deterministic 'what should I do next?' from state."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import LoopConfig
    from .state import LoopState, TaskState


class Action(Enum):
    EXECUTE = "execute"
    GENERATE_QC = "generate_qc"
    RUN_QC = "run_qc"
    FIX = "fix"
    CRITICAL_EVAL = "critical_eval"
    COURSE_CORRECT = "course_correct"
    RESEARCH = "research"
    INTERACTIVE_PAUSE = "interactive_pause"
    SERVICE_FIX = "service_fix"
    COHERENCE_EVAL = "coherence_eval"
    EXIT_GATE = "exit_gate"


def _scoped_tasks(state: LoopState) -> dict[str, TaskState]:
    """Return tasks scoped to the current epic (or all tasks for single_run)."""
    if state.vision_complexity != "multi_epic" or not state.epics:
        return state.tasks
    if state.current_epic_index >= len(state.epics):
        return state.tasks
    current_epic_id = state.epics[state.current_epic_index].epic_id
    # Only include tasks explicitly tagged with this epic's ID.
    # Tasks with empty epic_id are unassigned and should NOT be in scope
    # (they need to be tagged by _run_epic_preloop first).
    return {
        tid: t for tid, t in state.tasks.items()
        if t.epic_id == current_epic_id
    }


def decide_next_action(config: LoopConfig, state: LoopState) -> Action:
    """Deterministic decision engine. No LLM. Pure state analysis."""
    from .state import PauseState, TaskState

    # P0: Paused for human action
    if state.pause is not None:
        return Action.INTERACTIVE_PAUSE

    # P1: Services must be running
    if state.context.services and not _all_services_healthy(config, state):
        return Action.SERVICE_FIX

    # P2: Stuck -> course correct
    course_correction_count = len(state.progress_log_count("course_correct"))
    if state.is_stuck(config):
        if course_correction_count >= config.max_course_corrections:
            if state.pause is None:
                state.pause = PauseState(
                    reason=f"Loop stuck after {config.max_course_corrections} course corrections",
                    instructions="The loop has exhausted its automatic recovery options. "
                                 "Please review the current state and provide guidance.",
                    requested_at="",
                )
            return Action.INTERACTIVE_PAUSE
        return Action.COURSE_CORRECT

    # Scope task queries to current epic
    scoped = _scoped_tasks(state)
    done_count = len([t for t in scoped.values() if t.status == "done"])
    pending_tasks = [t for t in scoped.values() if t.status == "pending"]

    # P3: Generate QC when enough tasks are done to be meaningful
    # Require at least 3 done tasks (or all tasks done) to avoid premature QC
    # that produces nothing and wastes the generation opportunity.
    min_for_qc = min(3, len(scoped))
    if (not state.verifications
            and done_count >= max(config.generate_verifications_after, min_for_qc)
            and state.gate_passed("plan_generated")
            and not state.gate_passed("verifications_generated")):
        return Action.GENERATE_QC

    # P4: Fix failing QC
    failing = [v for v in state.verifications.values() if v.status == "failed"]
    if failing:
        max_fix = state.process_monitor.current_strategy.get(
            "max_fix_attempts", config.max_fix_attempts,
        )
        fixable = [v for v in failing if v.attempts < max_fix]
        if fixable:
            return Action.FIX
        if not state.research_attempted_for_current_failures:
            return Action.RESEARCH
        return Action.COURSE_CORRECT

    # P5: Human blocked task
    human_blocked = [
        t for t in state.tasks.values()
        if t.status == "blocked" and t.blocked_reason.startswith("HUMAN_ACTION:")
    ]
    if human_blocked:
        return Action.INTERACTIVE_PAUSE

    # P6: Pending tasks with dependencies met
    ready = [
        t for t in pending_tasks
        if all(
            state.tasks.get(dep, TaskState(task_id="")).status in ("done", "descoped")
            for dep in (t.dependencies or [])
        )
    ]
    if ready:
        return Action.EXECUTE
    if pending_tasks:
        return Action.COURSE_CORRECT

    # P7: QC pending
    pending_v = [v for v in state.verifications.values() if v.status == "pending"]
    if pending_v:
        return Action.RUN_QC

    # P8: Critical eval due
    crit_eval_due = (
        state.tasks_since_last_critical_eval >= config.critical_eval_interval
        or (config.critical_eval_on_all_pass
            and all(v.status == "passed" for v in state.verifications.values()
                    if v.status != "blocked")
            and state.verifications
            and not any(vrc.value_score >= 0.9 for vrc in state.vrc_history))
    )
    if crit_eval_due:
        return Action.CRITICAL_EVAL

    # P8b: Coherence eval due
    if getattr(state, "coherence_critical_pending", False):
        return Action.COHERENCE_EVAL

    # P9: All done + all passing -> exit gate
    all_pass = all(
        v.status == "passed" for v in state.verifications.values()
        if v.status != "blocked"
    )
    if not pending_tasks:
        if state.verifications and all_pass:
            return Action.EXIT_GATE
        if not state.verifications:
            # No verifications exist — try to generate them before exiting
            if not state.gate_passed("verifications_generated"):
                return Action.GENERATE_QC
            # QC was attempted but produced nothing — allow exit gate
            # only after sufficient tasks are done (not on first attempt)
            if done_count >= max(3, len(scoped) // 2):
                return Action.EXIT_GATE

    return Action.COURSE_CORRECT


def _all_services_healthy(config: LoopConfig, state: LoopState) -> bool:
    """Check if all required services are healthy."""
    import socket

    import requests

    for name, service in state.context.services.items():
        if "health_url" in service:
            url = service["health_url"]
            # Skip URLs with unresolved template variables — can't health-check them
            if "{" in url:
                continue
            try:
                r = requests.get(url, timeout=5)
                if r.status_code != 200:
                    return False
            except requests.RequestException:
                return False
        elif service.get("health_type") == "tcp":
            port = service.get("port", 0)
            if port == 0:
                continue  # Dynamic port not yet assigned — skip
            if not _is_port_open("localhost", port):
                return False
    return True


def _is_port_open(host: str, port: int) -> bool:
    """Check if a TCP port is accepting connections."""
    import socket
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (ConnectionRefusedError, TimeoutError, OSError):
        return False
