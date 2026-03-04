"""Cross-platform test execution infrastructure.

The outer loop uses this to independently verify results — the builder
never grades its own work. Extracted from V3's phases/execute.py.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import VerificationState


def _resolve_script_path(script_path: str) -> Path:
    """Resolve script path to absolute Path object.

    Handles both absolute paths and relative paths. Relative paths are
    resolved by searching from CWD upwards until the file is found.
    """
    p = Path(script_path)

    if p.is_absolute():
        return p

    resolved = p.resolve()
    if resolved.exists():
        return resolved

    # Search upwards from CWD
    search_start = Path.cwd()
    for _ in range(5):
        candidate = search_start / script_path
        if candidate.exists():
            return candidate.resolve()
        if script_path.startswith('./') or script_path.startswith('.\\'):
            candidate = search_start / script_path[2:]
            if candidate.exists():
                return candidate.resolve()
        if search_start.parent == search_start:
            break
        search_start = search_start.parent

    # Search in sprint directories
    sprints_dir = Path.cwd() / "sprints"
    if sprints_dir.exists() and sprints_dir.is_dir():
        for sprint_dir in sprints_dir.iterdir():
            if sprint_dir.is_dir():
                candidate = sprint_dir / script_path
                if candidate.exists():
                    return candidate.resolve()

    return resolved


def _build_script_command(script_path: str) -> list[str] | str:
    """Build the correct command to run a verification script cross-platform.

    On Windows, .sh scripts can't be executed directly (WinError 193).
    Route them through bash (Git Bash / WSL) or convert to equivalent commands.
    """
    p = _resolve_script_path(script_path)
    suffix = p.suffix.lower()

    if suffix == ".py":
        return [sys.executable, str(p)]

    if suffix == ".js":
        if ".spec." in p.name or ".test." in p.name:
            posix_path = p.as_posix()
            npx = shutil.which("npx")
            if npx:
                return [npx, "playwright", "test", posix_path]
            return ["npx", "playwright", "test", posix_path]
        node = shutil.which("node")
        if node:
            return [node, str(p)]
        return ["node", str(p)]

    if suffix == ".sh":
        posix_path = p.as_posix()
        if sys.platform == "win32":
            # Convert Windows path to Git Bash format
            if len(posix_path) >= 3 and posix_path[1] == ':' and posix_path[2] == '/':
                drive = posix_path[0].lower()
                posix_path = f"/{drive}{posix_path[2:]}"

            git_bash = shutil.which("bash")
            if git_bash:
                return [git_bash, posix_path]
            sh = shutil.which("sh")
            if sh:
                return [sh, posix_path]
            return f'bash "{posix_path}"'
        return ["bash", posix_path]

    return [str(p)]


def run_tests_parallel(
    tests: list[VerificationState],
    timeout: int,
    max_workers: int | None = None,
) -> dict[str, tuple[int, str, str]]:
    """Run test scripts in parallel. Returns {test_id: (exit_code, stdout, stderr)}."""
    max_workers = max_workers or min(os.cpu_count() or 4, 10)
    results: dict[str, tuple[int, str, str]] = {}
    base_port = 3100

    def run_one(
        test: VerificationState, port_offset: int,
    ) -> tuple[str, tuple[int, str, str]]:
        tmp_dir: str | None = None
        try:
            cmd = _build_script_command(test.script_path)
            use_shell = isinstance(cmd, str)
            script_path_resolved = _resolve_script_path(test.script_path)
            script_dir = script_path_resolved.parent

            if not script_dir.exists() and script_path_resolved.exists():
                script_dir = script_path_resolved.resolve().parent
            if not script_dir.exists():
                script_dir = Path.cwd()

            # Playwright tests MUST run from project root
            if ".spec." in script_path_resolved.name or ".test." in script_path_resolved.name:
                if script_path_resolved.suffix.lower() == ".js":
                    project_root = script_dir
                    for parent in [script_dir] + list(script_dir.parents):
                        if (parent / "playwright.config.js").exists() or (parent / "playwright.config.ts").exists():
                            project_root = parent
                            break
                    script_dir = project_root

                    try:
                        relative_path = script_path_resolved.relative_to(project_root)
                        relative_posix = relative_path.as_posix()
                        npx = shutil.which("npx")
                        if npx:
                            cmd = [npx, "playwright", "test", relative_posix]
                        else:
                            cmd = ["npx", "playwright", "test", relative_posix]
                        use_shell = False
                    except ValueError:
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
