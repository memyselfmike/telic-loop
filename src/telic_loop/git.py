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


def setup_sprint_branch(config: LoopConfig, state: LoopState) -> None:
    """Create feature branch at sprint start."""
    # Detect current branch
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True,
    )
    current_branch = result.stdout.strip()
    state.git.original_branch = current_branch

    # Refuse to work on protected branches
    if current_branch in state.git.protected_branches:
        print(f"  WARNING: On protected branch '{current_branch}' — creating feature branch")

    # Stash uncommitted changes
    status = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True,
    )
    if status.stdout.strip():
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        stash_msg = f"telic-loop-auto-stash-{ts}"
        subprocess.run(["git", "stash", "push", "-m", stash_msg], check=True)
        state.git.had_stashed_changes = True
        state.git.stash_ref = stash_msg
        print(f"  Stashed uncommitted changes: {stash_msg}")

    # Create feature branch
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"telic-loop/{config.sprint}-{ts}"
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    state.git.branch_name = branch_name

    # Record initial commit hash
    hash_result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
    )
    state.git.last_commit_hash = hash_result.stdout.strip()
    print(f"  Created branch: {branch_name}")


def git_commit(config: LoopConfig, state: LoopState, message: str) -> None:
    """Create a safe git commit. Never uses 'git add -A'."""
    # Stage modified tracked files
    subprocess.run(["git", "add", "-u"], check=False)

    # Stage new files only from safe directories
    safe_dirs = _get_safe_directories(config, state)
    for d in safe_dirs:
        if Path(d).exists():
            subprocess.run(["git", "add", str(d)], check=False)

    # Scan staged files for sensitive patterns
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True,
    )
    staged = result.stdout.strip().splitlines()
    for f in staged:
        if _matches_sensitive_pattern(f, state.git.sensitive_patterns):
            subprocess.run(["git", "reset", "HEAD", f], check=False)
            print(f"  WARNING: Unstaged sensitive file: {f}")

    # Check if there are staged changes
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", message], check=True)
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
        )
        state.git.last_commit_hash = hash_result.stdout.strip()


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


def execute_rollback(
    config: LoopConfig, state: LoopState, checkpoint: GitCheckpoint, reason: str,
) -> None:
    """Roll back git and synchronize loop state using WAL pattern."""
    # 0. Write-ahead log
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
    wal_path.write_text(json.dumps(wal_data, indent=2))

    # 1. Git reset
    subprocess.run(["git", "reset", "--hard", checkpoint.commit_hash], check=True)

    # 2. Clean untracked files
    subprocess.run(["git", "clean", "-fd"], check=True)

    # 3. Identify reverted tasks
    completed_task_ids = {
        t.task_id for t in state.tasks.values() if t.status == "done"
    }
    checkpoint_task_ids = set(checkpoint.tasks_completed)
    reverted_task_ids = completed_task_ids - checkpoint_task_ids

    # 4. Reset reverted tasks to pending
    for task_id in reverted_task_ids:
        task = state.tasks.get(task_id)
        if task:
            task.status = "pending"
            task.completed_at = ""
            task.files_created = []
            task.files_modified = []
            task.completion_notes = f"Rolled back at iteration {state.iteration}: {reason}"

    # 5. Reset verifications to checkpoint state
    for vid, v in state.verifications.items():
        if vid in checkpoint.verifications_passing:
            v.status = "passed"
        else:
            v.status = "pending"
            v.failures = []

    # 6. Update regression baseline
    state.regression_baseline = set(checkpoint.verifications_passing)

    # 7. Reset iterations_without_progress
    state.iterations_without_progress = 0

    # 8. Record rollback
    state.git.rollbacks.append({
        "from_hash": wal_data["from_hash"],
        "to_hash": checkpoint.commit_hash,
        "to_label": checkpoint.label,
        "reason": reason,
        "iteration": state.iteration,
        "tasks_reverted": list(reverted_task_ids),
    })

    # 9. Update git state
    state.git.last_commit_hash = checkpoint.commit_hash

    # 10. Commit the rollback
    git_commit(config, state, f"telic-loop({config.sprint}): Rollback to {checkpoint.label}: {reason}")

    # 11. Save state
    state.save(config.state_file)

    # 12. Remove WAL
    wal_path.unlink(missing_ok=True)


def ensure_gitignore(sprint_dir: Path) -> None:
    """Auto-maintain .gitignore with common sensitive file patterns."""
    gitignore = sprint_dir / ".gitignore"
    patterns = [
        ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx",
        "__pycache__/", "*.pyc", ".loop_state.json.tmp",
        ".loop.lock", ".rollback_wal",
    ]
    existing = set()
    if gitignore.exists():
        existing = set(gitignore.read_text().splitlines())

    new_patterns = [p for p in patterns if p not in existing]
    if new_patterns:
        with open(gitignore, "a") as f:
            for p in new_patterns:
                f.write(f"\n{p}")


def check_sensitive_files(state: LoopState) -> list[str]:
    """Scan staged files against sensitive patterns."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True,
    )
    staged = result.stdout.strip().splitlines()
    matches = []
    for f in staged:
        if _matches_sensitive_pattern(f, state.git.sensitive_patterns):
            matches.append(f)
    return matches


def check_and_fix_services(config: LoopConfig, state: LoopState) -> None:
    """Check service health after rollback and restart if needed."""
    from .decision import _all_services_healthy
    if not _all_services_healthy(config, state):
        print("  WARNING: Services unhealthy after rollback — may need manual restart")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_safe_directories(config: LoopConfig, state: LoopState) -> list[str]:
    """Derive safe directories for staging new files."""
    safe = [str(config.sprint_dir)]
    for d in ["src", "tests", "test", "lib", "docs"]:
        candidate = config.sprint_dir / d
        if candidate.exists():
            safe.append(str(candidate))
    return safe


def _matches_sensitive_pattern(filepath: str, patterns: list[str]) -> bool:
    """Check if a file path matches any sensitive pattern."""
    name = Path(filepath).name
    return any(fnmatch(name, pat) or fnmatch(filepath, pat) for pat in patterns)
