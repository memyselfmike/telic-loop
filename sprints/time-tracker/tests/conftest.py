"""
Test fixtures for Freelancer Time Tracker.

Tests use in-process ASGI transport via httpx — no network port required.
Each test gets a fresh temporary SQLite database to ensure full isolation.
Playwright tests start a real server on a dynamically allocated free port.
"""

import os
import socket
import tempfile
import threading
from pathlib import Path
from typing import Generator

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Temp-database + in-process ASGI client (for API unit tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db(tmp_path) -> Path:
    """
    Create a temporary SQLite database file for a single test.

    The database is initialized with the full schema and deleted after the
    test completes (via pytest's tmp_path fixture).  No two tests share state.
    """
    db_file = tmp_path / "test_timetracker.db"
    # Initialize schema into the temp file
    from backend.database import init_db
    init_db(db_path=db_file)
    return db_file


@pytest.fixture
def app(tmp_db: Path):
    """
    Return a FastAPI app instance wired to the test's temporary database.

    Sets the DB_PATH environment variable so every call to get_db() / init_db()
    inside the app uses the isolated temp database.
    """
    old_db_path = os.environ.get("DB_PATH")
    os.environ["DB_PATH"] = str(tmp_db)
    try:
        from backend.main import create_app
        test_app = create_app()
        yield test_app
    finally:
        if old_db_path is None:
            os.environ.pop("DB_PATH", None)
        else:
            os.environ["DB_PATH"] = old_db_path


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """
    Synchronous TestClient using FastAPI's built-in test transport.
    Use this for API unit tests — no server port needed.
    Each test gets a fresh database via the `app` fixture.
    """
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Live server on a dynamic port (for Playwright / browser tests)
# ---------------------------------------------------------------------------

def _find_free_port() -> int:
    """Bind to port 0 and let the OS assign a free port, then return it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server_url(tmp_path_factory):
    """
    Start a real uvicorn server on a free port for Playwright tests.
    Yields the base URL (e.g. http://127.0.0.1:54321).
    Server is shut down after the test session completes.
    Uses a session-scoped temp database.
    """
    # Create a session-scoped temp database
    tmp_dir = tmp_path_factory.mktemp("live_server")
    db_file = tmp_dir / "live_test.db"

    from backend.database import init_db
    init_db(db_path=db_file)

    os.environ["DB_PATH"] = str(db_file)

    from backend.main import create_app
    port = _find_free_port()
    test_app = create_app()

    config = uvicorn.Config(
        app=test_app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    # Run in a background thread so pytest can continue
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to be ready
    import time
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.05)

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=5)
