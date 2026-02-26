"""Multi-turn task execution (Builder agent)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
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

def _resolve_script_path(script_path: str) -> Path:
    """Resolve script path to absolute Path object.

    Handles both absolute paths (like E:/Projects/...) and relative paths
    (like .loop/verifications/...). Relative paths are resolved by searching
    from the current working directory upwards until the file is found.

    This is a compatibility layer for old relative paths stored in state.
    New paths should be absolute (see qc.py fix).
    """
    p = Path(script_path)

    # If already absolute and exists, return it
    if p.is_absolute():
        return p

    # Try resolving relative to CWD first
    resolved = p.resolve()
    if resolved.exists():
        return resolved

    # Search upwards from CWD to find the script
    # (handles case where CWD is project root but script is in sprints/*/...)
    search_start = Path.cwd()
    for _ in range(5):  # max 5 levels up
        candidate = search_start / script_path
        if candidate.exists():
            return candidate.resolve()
        # Also try without leading dot if path starts with ./
        if script_path.startswith('./') or script_path.startswith('.\\'):
            candidate = search_start / script_path[2:]
            if candidate.exists():
                return candidate.resolve()
        if search_start.parent == search_start:
            break  # reached root
        search_start = search_start.parent

    # Search in sprint directories if CWD is project root
    # (handles relative paths like .loop/verifications/... stored in state)
    sprints_dir = Path.cwd() / "sprints"
    if sprints_dir.exists() and sprints_dir.is_dir():
        for sprint_dir in sprints_dir.iterdir():
            if sprint_dir.is_dir():
                candidate = sprint_dir / script_path
                if candidate.exists():
                    return candidate.resolve()

    # Fallback: return the original resolved path (will likely fail, but with clear error)
    return resolved


def _build_script_command(script_path: str) -> list[str] | str:
    """Build the correct command to run a verification script cross-platform.

    On Windows, .sh scripts can't be executed directly (WinError 193).
    Route them through bash (Git Bash / WSL) or convert to equivalent commands.
    .py scripts use sys.executable, .js scripts use node.
    Playwright test files (.spec.js, .test.js) use npx playwright test.

    IMPORTANT: script_path should use forward slashes (POSIX format) for bash compatibility.
    """
    import shutil
    import sys

    # Resolve to absolute path so the command works regardless of CWD.
    # Handles both absolute and relative paths correctly.
    p = _resolve_script_path(script_path)
    suffix = p.suffix.lower()

    if suffix == ".py":
        return [sys.executable, str(p)]

    if suffix == ".js":
        # Check if this is a Playwright test file
        if ".spec." in p.name or ".test." in p.name:
            # Playwright test files: return marker command that will be replaced in run_one
            # with proper relative path from project root. We can't compute the relative
            # path here because we don't know the working directory yet.
            # Use absolute path as fallback if run_one can't find project root.
            posix_path = p.as_posix()
            npx = shutil.which("npx")
            if npx:
                return [npx, "playwright", "test", posix_path]
            return ["npx", "playwright", "test", posix_path]

        # Regular JavaScript file - run with node
        node = shutil.which("node")
        if node:
            return [node, str(p)]
        return ["node", str(p)]

    if suffix == ".sh":
        # Bash requires forward slashes on all platforms
        posix_path = p.as_posix()
        if sys.platform == "win32":
            # Try Git Bash first (most common on Windows dev machines)
            git_bash = shutil.which("bash")
            if git_bash:
                return [git_bash, posix_path]
            # Fallback: try sh
            sh = shutil.which("sh")
            if sh:
                return [sh, posix_path]
            # Last resort: return shell=True with bash -c
            return f'bash "{posix_path}"'
        return ["bash", posix_path]

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
    base_port = 3100  # Avoid default 3000 to prevent collisions

    def run_one(
        test: VerificationState, port_offset: int,
    ) -> tuple[str, tuple[int, str, str]]:
        tmp_dir: str | None = None
        try:
            cmd = _build_script_command(test.script_path)
            use_shell = isinstance(cmd, str)
            script_path_resolved = _resolve_script_path(test.script_path)
            script_dir = script_path_resolved.parent

            # Guard against non-existent directory causing WinError 267
            # If script dir doesn't exist but script does, use script's actual parent
            if not script_dir.exists() and script_path_resolved.exists():
                script_dir = script_path_resolved.resolve().parent
            # If still doesn't exist, use CWD as fallback
            if not script_dir.exists():
                script_dir = Path.cwd()

            # Playwright tests MUST run from project root (where playwright.config.js lives)
            # Running from .loop/verifications/ causes "test() to be called here" errors
            # because Playwright can't find its config and loads tests in wrong context
            if ".spec." in script_path_resolved.name or ".test." in script_path_resolved.name:
                if script_path_resolved.suffix.lower() == ".js":
                    # Find project root by walking up from script dir to find playwright.config.js
                    project_root = script_dir
                    for parent in [script_dir] + list(script_dir.parents):
                        if (parent / "playwright.config.js").exists() or (parent / "playwright.config.ts").exists():
                            project_root = parent
                            break
                    script_dir = project_root

                    # CRITICAL: Rebuild command with relative path from project root
                    # Passing absolute path causes Playwright to load test in wrong context
                    try:
                        relative_path = script_path_resolved.relative_to(project_root)
                        # Convert to POSIX path (forward slashes) for cross-platform compatibility
                        relative_posix = relative_path.as_posix()
                        npx = shutil.which("npx")
                        if npx:
                            cmd = [npx, "playwright", "test", relative_posix]
                        else:
                            cmd = ["npx", "playwright", "test", relative_posix]
                        use_shell = False
                    except ValueError:
                        # Script is outside project root - use absolute path as fallback
                        pass

            # Isolated environment: unique port + temp data dir per test
            env = os.environ.copy()
            env["PORT"] = str(base_port + port_offset)
            tmp_dir = tempfile.mkdtemp(prefix=f"tl-test-{port_offset}-")
            env["TEST_DATA_DIR"] = tmp_dir

            proc = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=timeout,
                shell=use_shell,
                cwd=str(script_dir),
                env=env,
            )
            return test.verification_id, (
                proc.returncode, proc.stdout or "", proc.stderr or "",
            )
        except FileNotFoundError:
            return test.verification_id, (
                1, "", "No bash interpreter found — cannot run .sh scripts on this platform",
            )
        except OSError as e:
            return test.verification_id, (
                1, "", f"OS error running script: {e}",
            )
        except subprocess.TimeoutExpired:
            return test.verification_id, (1, "", "TIMEOUT")
        except Exception as e:
            return test.verification_id, (
                1, "", f"Unexpected error: {type(e).__name__}: {e}",
            )
        finally:
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(run_one, t, i): t for i, t in enumerate(tests)
        }
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
        script_path_resolved = _resolve_script_path(test.script_path)
        script_dir = script_path_resolved.parent

        # Guard against non-existent directory causing WinError 267
        # If script dir doesn't exist but script does, use script's actual parent
        if not script_dir.exists() and script_path_resolved.exists():
            script_dir = script_path_resolved.resolve().parent
        # If still doesn't exist, use CWD as fallback
        if not script_dir.exists():
            script_dir = Path.cwd()

        # Playwright tests MUST run from project root (where playwright.config.js lives)
        # Running from .loop/verifications/ causes "test() to be called here" errors
        # because Playwright can't find its config and loads tests in wrong context
        if ".spec." in script_path_resolved.name or ".test." in script_path_resolved.name:
            if script_path_resolved.suffix.lower() == ".js":
                # Find project root by walking up from script dir to find playwright.config.js
                project_root = script_dir
                for parent in [script_dir] + list(script_dir.parents):
                    if (parent / "playwright.config.js").exists() or (parent / "playwright.config.ts").exists():
                        project_root = parent
                        break
                script_dir = project_root

                # CRITICAL: Rebuild command with relative path from project root
                # Passing absolute path causes Playwright to load test in wrong context
                try:
                    relative_path = script_path_resolved.relative_to(project_root)
                    # Convert to POSIX path (forward slashes) for cross-platform compatibility
                    relative_posix = relative_path.as_posix()
                    npx = shutil.which("npx")
                    if npx:
                        cmd = [npx, "playwright", "test", relative_posix]
                    else:
                        cmd = ["npx", "playwright", "test", relative_posix]
                    use_shell = False
                except ValueError:
                    # Script is outside project root - use absolute path as fallback
                    pass

        proc = subprocess.run(
            cmd,
            capture_output=True, text=True,
            timeout=timeout,
            shell=use_shell,
            cwd=str(script_dir),
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except FileNotFoundError:
        return 1, "", "No bash interpreter found — cannot run .sh scripts on this platform"
    except OSError as e:
        return 1, "", f"OS error running script: {e}"
    except subprocess.TimeoutExpired:
        return 1, "", "TIMEOUT"
    except Exception as e:
        return 1, "", f"Unexpected error: {type(e).__name__}: {e}"


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
                stdout=(stdout or "")[:2000],
                stderr=(stderr or "")[:2000],
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
        script_content = ""
        if test.script_path:
            try:
                resolved_path = _resolve_script_path(test.script_path)
                if resolved_path.exists():
                    script_content = resolved_path.read_text(encoding="utf-8")
            except Exception:
                pass  # If resolution fails, leave script_content empty
        failing_details = [{
            "verification_id": test.verification_id,
            "last_error": test.last_error,
            "attempt_history": test.attempt_history,
            "script": script_content,
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

        # Re-fetch — _sync_state replaced state.verifications after session
        test = state.verifications.get(test_id)
        if not test:
            continue
        exit_code, stdout, stderr = run_test_script(
            test, config.regression_timeout // max(len(regressions), 1),
        )
        if exit_code == 0:
            test.status = "passed"
            state.regression_baseline.add(test_id)
