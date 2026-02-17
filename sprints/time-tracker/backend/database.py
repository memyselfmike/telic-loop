"""
Freelancer Time Tracker — SQLite Database Layer

Provides connection management, schema creation, and migration on startup.

Usage:
    from backend.database import get_db, init_db

    # In FastAPI lifespan or startup:
    init_db()

    # In route handlers:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM projects").fetchall()

Configuration:
    DB_PATH environment variable overrides the default database location.
    Default: <sprint_dir>/data/timetracker.db
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

# ---------------------------------------------------------------------------
# Database path configuration
# ---------------------------------------------------------------------------

# The sprint root is two levels up from this file (backend/database.py → sprint/)
_SPRINT_DIR = Path(__file__).parent.parent

# Allow tests or operators to override the database path via environment variable.
# Tests pass a temp path to avoid touching the real database.
def _resolve_db_path() -> Path:
    env_path = os.environ.get("DB_PATH")
    if env_path:
        return Path(env_path)
    return _SPRINT_DIR / "data" / "timetracker.db"


# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

_DDL_PROJECTS = """
CREATE TABLE IF NOT EXISTS projects (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    client_name  TEXT    NOT NULL DEFAULT '',
    hourly_rate  REAL    NOT NULL DEFAULT 0.0,
    color        TEXT    NOT NULL DEFAULT '#58a6ff',
    archived     INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

_DDL_TIME_ENTRIES = """
CREATE TABLE IF NOT EXISTS time_entries (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id       INTEGER NOT NULL REFERENCES projects(id),
    description      TEXT    NOT NULL DEFAULT '',
    start_time       TEXT    NOT NULL,
    end_time         TEXT,               -- NULL while timer is running
    duration_seconds INTEGER,            -- computed on stop, NULL while running
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

# Index to speed up the most common queries (by date range and project)
_DDL_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_time_entries_project_id  ON time_entries(project_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_start_time  ON time_entries(start_time);
CREATE INDEX IF NOT EXISTS idx_time_entries_end_time    ON time_entries(end_time);
"""

# ---------------------------------------------------------------------------
# Connection factory
# ---------------------------------------------------------------------------

def _make_connection(db_path: Path) -> sqlite3.Connection:
    """
    Open a SQLite connection with recommended settings:
    - row_factory = sqlite3.Row  (access columns by name)
    - foreign_keys = ON          (SQLite does NOT enforce FKs by default)
    - journal_mode = WAL         (better concurrent read performance)
    """
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_db(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that yields a SQLite connection and commits/rolls back on exit.

    Args:
        db_path: Override the database path (useful in tests). When None, uses
                 DB_PATH env var or the default sprint data directory.

    Usage:
        with get_db() as conn:
            conn.execute("INSERT INTO projects (name) VALUES (?)", ("My Project",))
            # Commits automatically on normal exit; rolls back on exception.
    """
    resolved = db_path if db_path is not None else _resolve_db_path()
    conn = _make_connection(resolved)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema initialisation (idempotent)
# ---------------------------------------------------------------------------

def init_db(db_path: Path | None = None) -> Path:
    """
    Create the database file and tables if they do not already exist.

    This function is idempotent — calling it multiple times is safe (uses
    CREATE TABLE IF NOT EXISTS and CREATE INDEX IF NOT EXISTS).

    Args:
        db_path: Override the database file path. When None, falls back to
                 DB_PATH env var or the default sprint data directory.

    Returns:
        The resolved Path of the database file (useful for logging / tests).
    """
    resolved = db_path if db_path is not None else _resolve_db_path()

    # Ensure the parent directory exists (creates data/ automatically)
    resolved.parent.mkdir(parents=True, exist_ok=True)

    conn = _make_connection(resolved)
    try:
        conn.execute(_DDL_PROJECTS)
        conn.execute(_DDL_TIME_ENTRIES)
        # executescript requires explicit transaction management; use execute() loop instead
        for stmt in _DDL_INDEXES.strip().splitlines():
            stmt = stmt.strip()
            if stmt:
                conn.execute(stmt)
        conn.commit()
    finally:
        conn.close()

    return resolved
