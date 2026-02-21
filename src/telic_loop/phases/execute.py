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
    """Pick the highest-priority ready task, scoped to the current epic."""
    from ..state import TaskState

    # Scope to current epic if running multi-epic
    if (state.vision_complexity == "multi_epic"
            and state.epics
            and state.current_epic_index < len(state.epics)):
        epic_id = state.epics[state.current_epic_index].epic_id
        pending = [
            t for t in state.tasks.values()
            if t.status == "pending" and t.epic_id == epic_id
        ]
    else:
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
    """Fix broken services using the Builder agent.

    When Docker mode is active, tries the docker-up.sh script first (fast,
    no LLM needed). Falls back to Builder agent if script fails.
    """
    import subprocess

    from ..claude import AgentRole
    from ..decision import _all_services_healthy

    docker = state.context.docker
    if docker.get("enabled"):
        scripts_dir = config.effective_project_dir / docker.get("scripts_dir", ".telic-docker")
        docker_up = scripts_dir / "docker-up.sh"

        if docker_up.exists():
            print("  Docker: running docker-up.sh...")
            try:
                result = subprocess.run(
                    ["bash", str(docker_up)],
                    capture_output=True, text=True,
                    timeout=config.docker_compose_timeout,
                    cwd=str(config.effective_project_dir),
                )
                if result.returncode == 0 and _all_services_healthy(config, state):
                    print("  Docker: services healthy after script")
                    return True
                if result.returncode != 0:
                    print(f"  Docker: docker-up.sh failed (exit {result.returncode})")
            except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
                print(f"  Docker: docker-up.sh error: {exc}")

        # Script failed — fall through to Builder agent with Docker context
        docker_health = scripts_dir / "docker-health.sh"
        docker_logs = scripts_dir / "docker-logs.sh"
        session = claude.session(AgentRole.BUILDER)
        session.send(
            f"Docker services are unhealthy. Diagnose and fix.\n\n"
            f"Docker config: {json.dumps(docker, indent=2)}\n"
            f"Services: {json.dumps(state.context.services, indent=2)}\n\n"
            f"Scripts directory: {scripts_dir}\n"
            f"Start: bash {docker_up}\n"
            f"Health: bash {docker_health}\n"
            f"Logs: bash {docker_logs}"
        )
    else:
        session = claude.session(AgentRole.BUILDER)
        session.send(f"Fix broken services:\n{json.dumps(state.context.services, indent=2)}")

    return _all_services_healthy(config, state)


# ---------------------------------------------------------------------------
# Regression testing
# ---------------------------------------------------------------------------

def _build_script_command(script_path: str) -> list[str] | str:
    """Build the correct command to run a verification script cross-platform.

    On Windows, .sh scripts can't be executed directly (WinError 193).
    Route them through bash (Git Bash / WSL) or convert to equivalent commands.
    .py scripts use sys.executable for portability.
    """
    import shutil
    import sys

    p = Path(script_path)
    suffix = p.suffix.lower()

    if suffix == ".py":
        return [sys.executable, str(p)]

    if suffix == ".sh":
        if sys.platform == "win32":
            # Try Git Bash first (most common on Windows dev machines)
            git_bash = shutil.which("bash")
            if git_bash:
                return [git_bash, str(p)]
            # Fallback: try sh
            sh = shutil.which("sh")
            if sh:
                return [sh, str(p)]
            # Last resort: return shell=True with bash -c
            return f'bash "{p}"'
        return ["bash", str(p)]

    # Default: try to execute directly
    return [str(p)]


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
            cmd = _build_script_command(test.script_path)
            use_shell = isinstance(cmd, str)
            proc = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=timeout,
                shell=use_shell,
                cwd=str(Path(test.script_path).parent),
            )
            return test.verification_id, (proc.returncode, proc.stdout, proc.stderr)
        except FileNotFoundError:
            return test.verification_id, (
                1, "", "No bash interpreter found — cannot run .sh scripts on this platform",
            )
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
        cmd = _build_script_command(test.script_path)
        use_shell = isinstance(cmd, str)
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True,
            timeout=timeout,
            shell=use_shell,
            cwd=str(Path(test.script_path).parent),
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 1, "", "No bash interpreter found — cannot run .sh scripts on this platform"
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
            "script": Path(test.script_path).read_text(encoding="utf-8") if test.script_path else "",
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
