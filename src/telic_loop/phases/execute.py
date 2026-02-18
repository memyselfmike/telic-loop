"""Multi-turn task execution (Builder agent)."""

from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import LoopConfig
    from ..state import LoopState, TaskState, VerificationState
    from ..claude import Claude


def pick_next_task(state: LoopState) -> TaskState | None:
    """Pick the highest-priority ready task."""
    from ..state import TaskState

    pending = [t for t in state.tasks.values() if t.status == "pending"]
    if not pending:
        return None

    # Descoped dependencies count as satisfied
    ready = [
        t for t in pending
        if all(
            state.tasks.get(dep, TaskState(task_id="")).status in ("done", "descoped")
            for dep in (t.dependencies or [])
        )
    ]
    if not ready:
        return None

    # Priority: exit_gate tasks first, then critical_eval, vrc, course_correction, plan
    priority = {
        "exit_gate": 0, "critical_eval": 1, "vrc": 2,
        "course_correction": 3, "plan": 4,
    }
    ready.sort(key=lambda t: priority.get(t.source, 99))
    return ready[0]


def do_execute(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Execute the next ready task using the Builder agent."""
    from ..claude import AgentRole, load_prompt
    from ..git import create_checkpoint, git_commit

    task = pick_next_task(state)
    if not task:
        return False

    task.status = "in_progress"
    print(f"  Executing: {task.task_id} — {task.description[:80]}")

    try:
        session = claude.session(AgentRole.BUILDER)
        prompt = load_prompt("execute",
            TASK=json.dumps(asdict(task), indent=2),
            SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
            PROJECT_DIR=str(config.effective_project_dir),
        )
        session.send(prompt)
    except Exception as e:
        print(f"  Builder agent failed: {e}")
        task.status = "pending"
        task.retry_count += 1
        return False

    # Re-fetch task from state — _sync_state reloaded from disk after session,
    # so the old local `task` reference is stale
    task = state.tasks.get(task.task_id, task)
    completed = task.status == "done"  # set by report_task_complete handler

    if not completed:
        task.retry_count += 1
        if task.retry_count >= config.max_task_retries:
            task.status = "blocked"
            task.blocked_reason = "Agent failed to complete after max retries"
        elif task.status == "in_progress":
            task.status = "pending"
        return False

    state.tasks_since_last_critical_eval += 1
    if task.source != "plan":
        state.mid_loop_tasks_since_health_check += 1

    git_commit(config, state, f"telic-loop({config.sprint}): {task.task_id} - completed")

    # Create checkpoint after successful task
    create_checkpoint(config, state, f"after-{task.task_id}")

    # Regression check
    if config.regression_after_every_task and state.regression_baseline:
        regressions = run_regression(config, state)
        if regressions:
            print(f"  REGRESSION: {len(regressions)} tests broke after {task.task_id}")
            _handle_regressions(regressions, task, config, state, claude)
            return False

    return True


def do_service_fix(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Fix broken services using the Builder agent."""
    from ..claude import AgentRole

    session = claude.session(AgentRole.BUILDER)
    session.send(f"Fix broken services:\n{json.dumps(state.context.services, indent=2)}")

    from ..decision import _all_services_healthy
    return _all_services_healthy(config, state)


# ---------------------------------------------------------------------------
# Regression testing
# ---------------------------------------------------------------------------

def run_tests_parallel(
    tests: list[VerificationState],
    timeout: int,
    max_workers: int | None = None,
) -> dict[str, tuple[int, str, str]]:
    """Run test scripts in parallel. Returns {test_id: (exit_code, stdout, stderr)}."""
    import os

    max_workers = max_workers or min(os.cpu_count() or 4, 10)
    results: dict[str, tuple[int, str, str]] = {}

    def run_one(test: VerificationState) -> tuple[str, tuple[int, str, str]]:
        try:
            proc = subprocess.run(
                [test.script_path],
                capture_output=True, text=True,
                timeout=timeout,
                cwd=str(Path(test.script_path).parent),
            )
            return test.verification_id, (proc.returncode, proc.stdout, proc.stderr)
        except subprocess.TimeoutExpired:
            return test.verification_id, (1, "", "TIMEOUT")

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(run_one, t): t for t in tests}
        for future in as_completed(futures):
            test_id, result = future.result()
            results[test_id] = result

    return results


def run_test_script(
    test: VerificationState, timeout: int,
) -> tuple[int, str, str]:
    """Run a single test script. Returns (exit_code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            [test.script_path],
            capture_output=True, text=True,
            timeout=timeout,
            cwd=str(Path(test.script_path).parent),
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "TIMEOUT"


def run_regression(config: LoopConfig, state: LoopState) -> list[str]:
    """Run regression tests. Returns list of newly-failing test IDs."""
    from ..state import FailureRecord

    tests_to_check = [
        state.verifications[tid]
        for tid in state.regression_baseline
        if tid in state.verifications and state.verifications[tid].script_path
    ]
    if not tests_to_check:
        return []

    results = run_tests_parallel(tests_to_check, config.regression_timeout)
    regressions: list[str] = []
    for test_id, (exit_code, stdout, stderr) in results.items():
        if exit_code != 0:
            regressions.append(test_id)
            v = state.verifications[test_id]
            v.status = "failed"
            v.failures.append(FailureRecord(
                timestamp=datetime.now().isoformat(),
                attempt=v.attempts + 1,
                exit_code=exit_code,
                stdout=stdout[:2000],
                stderr=stderr[:2000],
            ))
            state.regression_baseline.discard(test_id)
    return regressions


def _handle_regressions(
    regressions: list[str],
    causal_task: TaskState,
    config: LoopConfig,
    state: LoopState,
    claude: Claude,
) -> None:
    """Attempt to fix regressions caused by a task."""
    from ..claude import AgentRole, load_prompt
    from .research import get_research_context

    session = claude.session(AgentRole.FIXER)
    for test_id in regressions:
        test = state.verifications[test_id]
        failing_details = [{
            "verification_id": test.verification_id,
            "last_error": test.last_error,
            "attempt_history": test.attempt_history,
            "script": Path(test.script_path).read_text() if test.script_path else "",
        }]
        prompt = load_prompt("fix",
            SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
            ROOT_CAUSE=json.dumps({
                "cause": f"Regression caused by {causal_task.task_id}",
                "affected_tests": [test_id],
                "fix_suggestion": (
                    f"Test was passing before {causal_task.task_id}. "
                    f"Preserve new functionality while restoring the regression."
                ),
            }),
            FAILING_VERIFICATIONS=json.dumps(failing_details, indent=2),
            RESEARCH_CONTEXT=get_research_context(state),
        )
        session.send(prompt)

        exit_code, stdout, stderr = run_test_script(
            test, config.regression_timeout // max(len(regressions), 1),
        )
        if exit_code == 0:
            test.status = "passed"
            state.regression_baseline.add(test_id)
