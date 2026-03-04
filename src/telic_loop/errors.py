"""Error classification, exponential backoff, failure trail, and JSONL crash logging.

Zeroclaw-inspired crash handling. No imports from other telic_loop modules
(avoids circular deps). Uses type(exc).__name__ string comparison instead of
isinstance for RateLimitError.
"""

from __future__ import annotations

import json
import re
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

_NON_RETRYABLE_PATTERNS = [
    "authentication",
    "unauthorized",
    "forbidden",
    "invalid api key",
    "context window exceeded",
    "context_length_exceeded",
    "max_tokens",
    "json.decoder.jsondecodeerror",
    "dacite",
    "wrapperconfig",
    "missingvalueserror",
]

_RATE_LIMIT_PATTERNS = [
    "rate limit",
    "rate_limit",
    "too many requests",
    "quota exceeded",
    "you've hit your limit",
    "you have hit your limit",
    "429",
]


def classify_error(exc: Exception) -> str:
    """Classify an exception as 'retryable', 'rate_limit', or 'non_retryable'.

    Unknown errors default to 'retryable' — the per-phase crash budget
    is the safety net for persistent failures.
    """
    exc_type = type(exc).__name__
    msg = str(exc).lower()

    # RateLimitError from agent.py
    if exc_type == "RateLimitError":
        return "rate_limit"

    # Check message for rate limit patterns
    if any(p in msg for p in _RATE_LIMIT_PATTERNS):
        return "rate_limit"

    # Check for non-retryable patterns
    if any(p in msg for p in _NON_RETRYABLE_PATTERNS):
        return "non_retryable"

    # Auth-related exception types
    if exc_type in ("AuthenticationError", "PermissionError"):
        return "non_retryable"

    # JSON/data corruption
    if exc_type in ("JSONDecodeError", "MissingValueError", "WrongTypeError"):
        return "non_retryable"

    # Default: retryable (phase budget is the safety net)
    return "retryable"


# ---------------------------------------------------------------------------
# Backoff
# ---------------------------------------------------------------------------

def backoff_seconds(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    """Exponential backoff: min(base * 2^attempt, cap)."""
    return min(base * (2 ** attempt), cap)


def parse_retry_after(error_text: str, cap: float = 30.0) -> float | None:
    """Extract a retry-after hint (seconds) from an error message.

    Looks for patterns like 'retry after 5s', 'retry in 10 seconds',
    'Retry-After: 30'.
    """
    match = re.search(
        r"retry[- ]?after[:\s]+(\d+)\s*s?(?:econds?)?",
        error_text,
        re.IGNORECASE,
    )
    if match:
        return min(float(match.group(1)), cap)

    match = re.search(
        r"retry\s+in\s+(\d+)\s*s(?:econds?)?",
        error_text,
        re.IGNORECASE,
    )
    if match:
        return min(float(match.group(1)), cap)

    return None


# ---------------------------------------------------------------------------
# Failure trail
# ---------------------------------------------------------------------------

@dataclass
class AttemptRecord:
    """One retry attempt within a FailureTrail."""
    attempt: int
    error_kind: str       # retryable | rate_limit | non_retryable
    error_type: str       # type(exc).__name__
    reason: str           # str(exc)[:200]
    duration: float       # seconds
    backoff: float        # seconds slept before next attempt


@dataclass
class FailureTrail:
    """Accumulates AttemptRecords across retries of a single operation."""
    attempts: list[AttemptRecord] = field(default_factory=list)

    def record(
        self,
        attempt: int,
        error_kind: str,
        exc: Exception,
        duration: float,
        backoff: float,
    ) -> None:
        self.attempts.append(AttemptRecord(
            attempt=attempt,
            error_kind=error_kind,
            error_type=type(exc).__name__,
            reason=str(exc)[:200],
            duration=duration,
            backoff=backoff,
        ))

    def to_dicts(self) -> list[dict[str, Any]]:
        return [asdict(a) for a in self.attempts]


# ---------------------------------------------------------------------------
# JSONL crash logging
# ---------------------------------------------------------------------------

def log_crash_jsonl(
    crash_file: Path,
    *,
    error: Exception,
    phase: str,
    iteration: int,
    error_kind: str = "",
    failure_trail: FailureTrail | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a full crash record to a JSONL file. Returns the record dict."""
    if not error_kind:
        error_kind = classify_error(error)

    record: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "phase": phase,
        "iteration": iteration,
        "error_kind": error_kind,
        "error_type": type(error).__name__,
        "error": str(error)[:500],
        "traceback": traceback.format_exception(error),
    }

    if failure_trail and failure_trail.attempts:
        record["failure_trail"] = failure_trail.to_dicts()

    if extra:
        record.update(extra)

    crash_file.parent.mkdir(parents=True, exist_ok=True)
    with open(crash_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")

    return record
