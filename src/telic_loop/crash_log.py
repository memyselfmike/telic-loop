"""Crash logging: structured crash records to .crash_log.jsonl."""

from __future__ import annotations

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# Error classification constants
CRASH_SDK_TIMEOUT = "sdk_timeout"
CRASH_SDK_ERROR = "sdk_error"
CRASH_SDK_CONNECTION = "sdk_connection"
CRASH_STATE_CORRUPTION = "state_corruption"
CRASH_SUBPROCESS = "subprocess"
CRASH_HANDLER = "handler"
CRASH_UNKNOWN = "unknown"


def classify_error(exc: BaseException) -> str:
    """Classify an exception into a crash category."""
    msg = str(exc).lower()
    exc_type = type(exc).__name__

    if "timed out" in msg or "timeout" in msg:
        return CRASH_SDK_TIMEOUT
    if "sdk error" in msg:
        return CRASH_SDK_ERROR
    if isinstance(exc, ExceptionGroup) or exc_type == "CLIConnectionError":
        return CRASH_SDK_CONNECTION
    if "dacite" in msg or exc_type in ("JSONDecodeError", "DaciteError"):
        return CRASH_STATE_CORRUPTION
    if exc_type == "CalledProcessError":
        return CRASH_SUBPROCESS
    return CRASH_UNKNOWN


def log_crash(
    crash_file: Path,
    *,
    error: BaseException,
    phase: str = "",
    task_id: str = "",
    iteration: int = 0,
    tokens_used: int = 0,
    crash_type: str = "",
    extra: dict[str, Any] | None = None,
) -> dict:
    """Append a structured crash record to the crash log file.

    Returns the record dict for callers to store a condensed version in state.
    """
    if not crash_type:
        crash_type = classify_error(error)

    tb_lines = traceback.format_exception(error)

    record: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "crash_type": crash_type,
        "phase": phase,
        "task_id": task_id,
        "iteration": iteration,
        "tokens_used": tokens_used,
        "error_type": type(error).__name__,
        "error_message": str(error)[:500],
        "traceback": tb_lines,
    }
    if extra:
        record["extra"] = extra

    # Append to JSONL file
    try:
        crash_file.parent.mkdir(parents=True, exist_ok=True)
        with open(crash_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as write_err:
        print(f"  WARNING: Could not write crash log: {write_err}")

    # Print crash details to stdout
    print(f"  Crash type: {crash_type}")
    print(f"  Error: {type(error).__name__}: {error}")
    for line in tb_lines[-15:]:
        print(f"  {line}", end="")

    return record
