"""Git operations: branching, safe commits, checkpoints, sensitive file protection, and rollback."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import LoopConfig
    from .state import GitCheckpoint, LoopState

_SAFE_SOURCE_DIRS = ["src", "tests", "test", "lib", "docs"]


# ---------------------------------------------------------------------------
# Git subprocess helper
# ---------------------------------------------------------------------------

def _run_git(*args: str, check: bool = False) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=check,
    )
    return result.stdout.strip()


def _run_git_quiet(*args: str) -> int:
    """Run a git command silently, return exit code."""
    devnull = subprocess.DEVNULL
    result = subprocess.run(["git", *args], stdout=devnull, stderr=devnull)
    return result.returncode


# ---------------------------------------------------------------------------
# Branch management
# ---------------------------------------------------------------------------

def setup_sprint_branch(config: LoopConfig, state: LoopState) -> None:
    """Create feature branch at sprint start."""
    current_branch = _run_git("rev-parse", "--abbrev-ref", "HEAD")
    state.git.original_branch = current_branch

    if current_branch in state.git.protected_branches:
        print(f"  WARNING: On protected branch '{current_branch}' — creating feature branch")

    # Stash uncommitted changes
    if _run_git("status", "--porcelain"):
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        stash_msg = f"telic-loop-auto-stash-{ts}"
        _run_git("stash", "push", "-m", stash_msg, check=True)
        state.git.had_stashed_changes = True
        state.git.stash_ref = stash_msg
        print(f"  Stashed uncommitted changes: {stash_msg}")

    # Create feature branch
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"telic-loop/{config.sprint}-{ts}"
    _run_git("checkout", "-b", branch_name, check=True)
    state.git.branch_name = branch_name
    state.git.last_commit_hash = _run_git("rev-parse", "HEAD")
    print(f"  Created branch: {branch_name}")


# ---------------------------------------------------------------------------
# Safe commits
# ---------------------------------------------------------------------------

def _stage_safe_files(config: LoopConfig, state: LoopState) -> None:
    """Stage modified tracked files and new files from safe directories."""
    _run_git_quiet("add", "-u")
    for d in _get_safe_directories(config, state):
        if Path(d).exists():
            _run_git_quiet("add", str(d))


def _unstage_sensitive_files(state: LoopState) -> None:
    """Remove sensitive files from the staging area."""
    staged = _run_git("diff", "--cached", "--name-only").splitlines()
    for f in staged:
        if _matches_sensitive_pattern(f, state.git.sensitive_patterns):
            _run_git_quiet("reset", "HEAD", f)
            print(f"  WARNING: Unstaged sensitive file: {f}")


def git_commit(config: LoopConfig, state: LoopState, message: str) -> None:
    """Create a safe git commit. Never uses 'git add -A'."""
    _stage_safe_files(config, state)
    _unstage_sensitive_files(state)

    if _run_git_quiet("diff", "--cached", "--quiet") != 0:
        _run_git("commit", "-m", message, check=True)
        state.git.last_commit_hash = _run_git("rev-parse", "HEAD")


def create_checkpoint(config: LoopConfig, state: LoopState, label: str) -> None:
    """Record a known-good state (commit hash + completed tasks + passing verifications)."""
    from .state import GitCheckpoint

    vrc = state.latest_vrc
    checkpoint = GitCheckpoint(
        commit_hash=state.git.last_commit_hash,
        timestamp=datetime.now().isoformat(),
        label=label,
        tasks_completed=[
            t.task_id for t in state.tasks.values() if t.status == "done"
        ],
        verifications_passing=[
            v.verification_id for v in state.verifications.values()
            if v.status == "passed"
        ],
        value_score=vrc.value_score if vrc else 0.0,
    )
    state.git.checkpoints.append(checkpoint)


def _write_rollback_wal(config: LoopConfig, state: LoopState,
                        checkpoint: GitCheckpoint, reason: str) -> tuple[Path, dict]:
    """Write WAL entry before rollback. Returns (wal_path, wal_data)."""
    wal_path = config.state_file.with_suffix(".rollback_wal")
    wal_data = {
        "status": "started",
        "from_hash": state.git.last_commit_hash,
        "to_hash": checkpoint.commit_hash,
        "to_label": checkpoint.label,
        "reason": reason,
        "iteration": state.iteration,
    }
    wal_path.parent.mkdir(parents=True, exist_ok=True)
    wal_path.write_text(json.dumps(wal_data, indent=2), encoding="utf-8")
    return wal_path, wal_data


def _reset_git_tree(commit_hash: str) -> None:
    """Hard-reset git to a specific commit and clean untracked files."""
    _run_git("reset", "--hard", commit_hash, check=True)
    _run_git("clean", "-fd", check=True)


def _revert_tasks_to_checkpoint(state: LoopState, checkpoint: GitCheckpoint,
                                 reason: str) -> set[str]:
    """Reset tasks completed after checkpoint back to pending. Returns reverted IDs."""
    completed = {t.task_id for t in state.tasks.values() if t.status == "done"}
    reverted = completed - set(checkpoint.tasks_completed)
    for task_id in reverted:
        task = state.tasks.get(task_id)
        if task:
            task.status = "pending"
            task.completed_at = ""
            task.files_created = []
            task.files_modified = []
            task.completion_notes = f"Rolled back at iteration {state.iteration}: {reason}"
    return reverted


def _reset_verifications_to_checkpoint(state: LoopState,
                                        checkpoint: GitCheckpoint) -> None:
    """Reset verifications to checkpoint state."""
    for vid, v in state.verifications.items():
        if vid in checkpoint.verifications_passing:
            v.status = "passed"
        else:
            v.status = "pending"
            v.failures = []
    state.regression_baseline = set(checkpoint.verifications_passing)


def execute_rollback(
    config: LoopConfig, state: LoopState, checkpoint: GitCheckpoint, reason: str,
) -> None:
    """Roll back git and synchronize loop state using WAL pattern."""
    wal_path, wal_data = _write_rollback_wal(config, state, checkpoint, reason)

    _reset_git_tree(checkpoint.commit_hash)
    reverted = _revert_tasks_to_checkpoint(state, checkpoint, reason)
    _reset_verifications_to_checkpoint(state, checkpoint)

    state.git.rollbacks.append({
        "from_hash": wal_data["from_hash"],
        "to_hash": checkpoint.commit_hash,
        "to_label": checkpoint.label,
        "reason": reason,
        "iteration": state.iteration,
        "tasks_reverted": list(reverted),
    })
    state.git.last_commit_hash = checkpoint.commit_hash

    git_commit(config, state, f"telic-loop({config.sprint}): Rollback to {checkpoint.label}: {reason}")
    state.save(config.state_file)
    wal_path.unlink(missing_ok=True)


def ensure_gitignore(sprint_dir: Path) -> None:
    """Auto-maintain .gitignore with common sensitive file patterns."""
    gitignore = sprint_dir / ".gitignore"
    patterns = [
        ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx",
        "__pycache__/", "*.pyc", ".loop_state.json.tmp",
        ".loop.lock", ".rollback_wal",
        ".playwright-mcp/", ".loop/screenshots/", "eval/",
        ".crash_log.jsonl",
    ]
    existing = set()
    if gitignore.exists():
        existing = set(gitignore.read_text(encoding="utf-8").splitlines())

    new_patterns = [p for p in patterns if p not in existing]
    if new_patterns:
        with open(gitignore, "a", encoding="utf-8") as f:
            for p in new_patterns:
                f.write(f"\n{p}")


def check_sensitive_files(state: LoopState) -> list[str]:
    """Scan staged files against sensitive patterns."""
    staged = _run_git("diff", "--cached", "--name-only").splitlines()
    return [f for f in staged if _matches_sensitive_pattern(f, state.git.sensitive_patterns)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_safe_directories(config: LoopConfig, state: LoopState) -> list[str]:
    """Derive safe directories for staging new files."""
    safe = [str(config.sprint_dir)]
    project_dir = config.effective_project_dir
    if project_dir != config.sprint_dir:
        safe.append(str(project_dir))
    for d in _SAFE_SOURCE_DIRS:
        candidate = project_dir / d
        if candidate.exists():
            safe.append(str(candidate))
    return safe


def _matches_sensitive_pattern(filepath: str, patterns: list[str]) -> bool:
    """Check if a file path matches any sensitive pattern."""
    name = Path(filepath).name
    return any(fnmatch(name, pat) or fnmatch(filepath, pat) for pat in patterns)
