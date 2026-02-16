"""Git operations: branching, safe commits, checkpoints, sensitive file protection, and rollback.

This module is the loop's safety net and audit trail. Every change is tracked,
every known-good state is checkpointed, and the loop can roll back when fixing
forward is more expensive than reverting.

Key operations
--------------
setup_sprint_branch(config, state)
    Create feature branch at sprint start. Detects protected branches,
    stashes uncommitted changes, creates telic-loop/{sprint}-{timestamp}.

safe_commit(config, state, message)
    Selective staging with sensitive file protection. Never uses `git add -A`.
    Stages tracked modifications and new files from safe directories only.
    Scans for and unstages sensitive files before committing.

create_checkpoint(state, label)
    Record a known-good state (commit hash + completed tasks + passing verifications).
    Called after QC passes, pre-loop completion, course correction, and rollback.

execute_rollback(config, state, checkpoint, reason)
    Git reset to checkpoint, synchronize loop state (revert tasks to pending,
    reset verifications), commit the rollback, and save state.

ensure_gitignore(sprint_dir)
    Auto-maintain .gitignore with common sensitive file patterns.

check_sensitive_files(state)
    Scan staged files against sensitive patterns. Returns list of matches.
    Called before every commit — matches are unstaged and logged.

Git Commit Triggers
-------------------
| When                  | Creates Checkpoint? |
|-----------------------|---------------------|
| Pre-loop complete     | Yes                 |
| After task execution  | No (wait for QC)    |
| After QC pass (all)   | Yes                 |
| After service fix     | No                  |
| After course correct  | Yes                 |
| After rollback        | Yes (new baseline)  |
| Exit gate pass        | Yes                 |
| Delivery complete     | Yes                 |

Rollback
--------
During course correction, if the corrector diagnoses compounding regressions
or an architectural wrong turn, it can request a rollback to a checkpoint.
The orchestrator calls execute_rollback() which:

1. git reset --hard {checkpoint_hash}
2. Reverted tasks reset to "pending" (retry_count preserved)
3. Verifications reset to checkpoint state
4. Rollback recorded in state.git.rollbacks
5. New commit created on top (audit trail)
6. State saved to disk

Safety constraints:
- Cannot roll back past pre-loop checkpoint
- Cannot roll back across epic boundaries
- Max rollbacks per sprint configurable (default 3)
- retry_count preserved so loop doesn't retry same approach
"""
