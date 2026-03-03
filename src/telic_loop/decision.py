"""Decision engine: deterministic 'what should I do next?' from state."""

from __future__ import annotations

import re
import sys
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import LoopConfig
    from .state import LoopState, TaskState


_PLATFORM_ERROR_RE = re.compile(
    r"mktemp.*not found|ps -p.*not found|ps:.*not found|lsof.*not found"
    r"|ENOENT.*[A-Z]:[\\/]|/tmp/tmp\."
    r"|is not recognized as .* command"
    r"|gawk.*not found|WinError"
    r"|cannot use gawk builtin",
    re.IGNORECASE,
)


def _has_platform_failures(state: LoopState) -> bool:
    """Check if failing verifications have Windows/MSYS-specific errors."""
    if sys.platform != "win32":
        return False
    for v in state.verifications.values():
        if v.status != "failed" or not v.failures:
            continue
        last = v.failures[-1]
        if _PLATFORM_ERROR_RE.search(f"{last.stdout}\n{last.stderr}"):
            return True
    return False


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

    # Scope task queries to current epic (needed by multiple priorities below)
    scoped = _scoped_tasks(state)
    done_count = len([t for t in scoped.values() if t.status == "done"])
    pending_tasks = [t for t in scoped.values() if t.status == "pending"]

    # P1: Services must be running — but only after bootstrap.
    # The bootstrap gate ensures services were initialized in preloop.
    # If bootstrap hasn't run, services can't possibly be healthy.
    if (state.context.services
            and done_count > 0
            and state.gate_passed("service_bootstrap")
            and not _all_services_healthy(config, state)):
        return Action.SERVICE_FIX

    # P2: Stuck -> course correct
    # Skip when there are failing verifications — P4 has its own bounded
    # exhaustion path (FIX → RESEARCH → COURSE_CORRECT → block).
    # P2 firing here just wastes course_correction budget without helping.
    has_failing_verifications = any(
        v.status == "failed" for v in state.verifications.values()
    )
    course_correction_count = len(state.progress_log_count("course_correct"))
    if state.is_stuck(config) and not has_failing_verifications:
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

    # P3: Generate QC after BUILD completes
    # Verifications test the COMPLETE feature set, not half-built scaffolding.
    # Guard: if QC generation has failed 3+ times total, stop trying.
    total_qc_fails = sum(
        1 for e in state.progress_log
        if e.get("action") == "generate_qc" and e.get("result") == "no_progress"
    )
    if (not pending_tasks
            and not state.verifications
            and done_count > 0
            and state.gate_passed("plan_generated")
            and not state.gate_passed("verifications_generated")
            and total_qc_fails < 3):
        return Action.GENERATE_QC

    # P4: Fix failing QC
    failing = [v for v in state.verifications.values() if v.status == "failed"]
    if failing:
        max_fix = state.process_monitor.current_strategy.get(
            "max_fix_attempts", config.max_fix_attempts,
        )
        fixable = [v for v in failing if v.attempts < max_fix]
        if fixable:
            # Platform error fast-path: if failures are Windows/MSYS-specific,
            # skip FIX and go directly to COURSE_CORRECT → regenerate_tests.
            if (_has_platform_failures(state)
                    and not state.course_correct_attempted_for_current_failures
                    and state.qc_generation_count < config.max_qc_regenerations):
                return Action.COURSE_CORRECT
            return Action.FIX
        if not state.research_attempted_for_current_failures:
            return Action.RESEARCH
        # Give course_correct one chance per failure set, but skip if
        # QC regeneration cap already reached (regeneration won't help)
        if (not state.course_correct_attempted_for_current_failures
                and state.qc_generation_count < config.max_qc_regenerations):
            return Action.COURSE_CORRECT
        # Both research and course_correct exhausted (or QC cap reached)
        # — mark unfixable tests as blocked and move on
        for v in failing:
            if v.attempts >= max_fix:
                v.status = "blocked"
        # Fall through to P5+ (may reach EXIT_GATE)

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
    # Guard: stop retrying critical eval after 3 no_progress results (same pattern as QC)
    total_crit_eval_fails = sum(
        1 for e in state.progress_log
        if e.get("action") == "critical_eval" and e.get("result") == "no_progress"
    )
    crit_eval_due = (
        not pending_tasks
        and total_crit_eval_fails < 3
        and (
            state.tasks_since_last_critical_eval >= config.critical_eval_interval
            or (config.critical_eval_on_all_pass
                and all(v.status == "passed" for v in state.verifications.values()
                        if v.status != "blocked")
                and state.verifications
                and not (state.vrc_history and state.vrc_history[-1].value_score >= 0.9))
        )
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
            # But skip if QC generation has already failed 3+ times total
            if not state.gate_passed("verifications_generated") and total_qc_fails < 3:
                return Action.GENERATE_QC
            # QC was attempted but produced nothing — allow exit gate
            # when enough tasks are done (at least half, or all if < 3)
            if done_count >= min(3, len(scoped)):
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
