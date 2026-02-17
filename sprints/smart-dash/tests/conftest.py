"""
Pytest configuration for smart-dash tests.
Provides a session-scoped HTTP server fixture that serves the dashboard.
"""
import subprocess
import time
import socket
import pytest
from pathlib import Path


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


@pytest.fixture(scope="session")
def http_server():
    """
    Start a Python HTTP server serving from sprints/smart-dash/ on port 8000.
    The server runs for the entire test session and is torn down after all tests complete.
    """
    # Get the sprint directory (parent of tests/)
    sprint_dir = Path(__file__).parent.parent
    port = 8000

    # Check if port is already in use
    if is_port_in_use(port):
        # Try to use the existing server
        import urllib.request
        try:
            urllib.request.urlopen(f"http://localhost:{port}/index.html", timeout=2)
            print(f"\nPort {port} already in use and serving content - using existing server")
            yield f"http://localhost:{port}"
            return
        except Exception:
            # Port in use but not serving our content - fail
            pytest.fail(f"Port {port} is in use but not serving the expected content")

    # Start the HTTP server
    print(f"\nStarting HTTP server on port {port} serving from {sprint_dir}")
    server_process = subprocess.Popen(
        ["python", "-m", "http.server", str(port)],
        cwd=str(sprint_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for server to be ready
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            import urllib.request
            urllib.request.urlopen(f"http://localhost:{port}/index.html", timeout=1)
            print(f"HTTP server ready after {attempt + 1} attempts")
            break
        except Exception:
            if attempt == max_attempts - 1:
                server_process.kill()
                pytest.fail(f"HTTP server failed to start after {max_attempts} attempts")
            time.sleep(0.5)

    # Yield the base URL
    yield f"http://localhost:{port}"

    # Teardown: kill the server
    print("\nShutting down HTTP server")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()
        server_process.wait()


@pytest.fixture(autouse=True)
def clear_localStorage(page, http_server):
    """
    Clear localStorage before each test to ensure test isolation.
    This prevents tasks from one test affecting another.
    """
    # Navigate to the actual page first (localStorage is not accessible on about:blank)
    page.goto(f"{http_server}/index.html")
    page.evaluate("localStorage.clear()")
    # Reload to start fresh
    page.reload()
