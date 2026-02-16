"""Pytest configuration and fixtures for todo app tests."""
import http.server
import socketserver
import threading
import time
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def http_server():
    """Start a local HTTP server serving the todo app directory."""
    # Get the sprint directory (parent of tests/)
    sprint_dir = Path(__file__).parent.parent

    # Find an available port
    port = 8765

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(sprint_dir), **kwargs)

        def log_message(self, format, *args):
            # Suppress server logs during tests
            pass

    # Create and start server
    with socketserver.TCPServer(("", port), Handler) as httpd:
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        # Give server time to start
        time.sleep(0.5)

        base_url = f"http://localhost:{port}"

        yield base_url

        # Shutdown server
        httpd.shutdown()


@pytest.fixture
def page(page, http_server):
    """Navigate to the todo app before each test with clean localStorage."""
    # Clear localStorage before each test to ensure independence
    page.goto(http_server)
    page.evaluate("localStorage.clear()")
    page.reload()

    yield page
