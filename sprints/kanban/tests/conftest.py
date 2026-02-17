"""
conftest.py — shared fixtures for the Kanban board Playwright test suite.

Starts a Python HTTP server serving sprints/kanban/ on a dynamic (OS-assigned) port,
waits for it to be ready, yields the base URL, then tears it down after tests.
"""
import os
import socket
import subprocess
import sys
import time
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest
from playwright.sync_api import Page, BrowserContext


# ─── Resolve the kanban directory (sprints/kanban/) relative to this file ───
KANBAN_DIR = Path(__file__).parent.parent.resolve()


class QuietHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler that suppresses request logs."""
    def log_message(self, format, *args):
        pass  # silence


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def base_url():
    """
    Session-scoped fixture: start an HTTP server serving KANBAN_DIR,
    yield the base URL, stop the server when all tests are done.
    """
    port = _get_free_port()

    # Change to the kanban directory so HTTP server resolves paths correctly
    server = HTTPServer(("127.0.0.1", port), QuietHandler)
    server.allow_reuse_address = True

    # Patch directory for SimpleHTTPRequestHandler
    original_dir = os.getcwd()
    os.chdir(str(KANBAN_DIR))

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"

    # Wait for server to be ready (up to 5 seconds)
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{url}/index.html", timeout=1)
            break
        except (urllib.error.URLError, ConnectionRefusedError):
            time.sleep(0.1)
    else:
        server.shutdown()
        os.chdir(original_dir)
        pytest.fail(f"HTTP server on port {port} did not become ready in 5 seconds")

    yield url

    server.shutdown()
    os.chdir(original_dir)


@pytest.fixture(autouse=True)
def clear_localstorage(page: Page, base_url: str):
    """
    Per-test fixture: navigate to the board and clear localStorage before each test
    to ensure tests start with a clean slate.
    """
    page.goto(f"{base_url}/index.html")
    page.evaluate("() => localStorage.clear()")
    page.reload()
    yield
