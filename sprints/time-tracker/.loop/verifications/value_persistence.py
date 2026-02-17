#!/usr/bin/env python3
"""
Verification: Data persistence across server restart
PRD Reference: Section 6 (Acceptance Criteria #5 - Time entries persist across server restart)
Vision Goal 6: Trust the Data - stopping and restarting server preserves all data
Vision Proof: User stops and restarts the server and all previously tracked time entries
              and projects are intact (SQLite persistence)
Category: value
"""
import sys
import os
import asyncio
import socket
import subprocess
import time
import tempfile

SPRINT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, SPRINT_DIR)
sys.path.insert(0, os.path.dirname(SPRINT_DIR))

print("=== Value: Data Persistence Across Server Restart ===")
print("Simulating: Freelancer tracks time, restarts server, data is still there")
print()

try:
    import httpx
    from httpx import AsyncClient
except ImportError:
    print("FAIL: httpx not installed")
    sys.exit(1)

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def wait_for_server(port, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.2)
    return False

async def run():
    failures = []

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        test_db = f.name
    os.unlink(test_db)

    try:
        from backend.database import init_db
    except ImportError as e:
        print(f"FAIL: Cannot import database: {e}")
        sys.exit(1)

    init_db(test_db)

    port1 = find_free_port()
    print(f"Step 1: Starting first server instance on port {port1}...")

    env = os.environ.copy()
    env["TEST_DB_PATH"] = test_db

    proc1 = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(port1), "--host", "127.0.0.1"],
        cwd=SPRINT_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    if not wait_for_server(port1):
        proc1.terminate()
        proc1.wait()
        os.unlink(test_db)
        print("FAIL: First server instance did not start within timeout")
        sys.exit(1)

    print(f"       -> Server 1 started (pid={proc1.pid})")

    project_id = None
    entry_id = None

    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port1}") as client:
        resp = await client.post("/api/projects", json={
            "name": "Persistent Project", "client_name": "Test Corp", "hourly_rate": 100.0
        })
        if resp.status_code == 201:
            project_id = resp.json()["id"]
            print(f"       -> Created project id={project_id}")
        else:
            failures.append(f"FAIL: Could not create project on server 1: {resp.text}")

        if project_id:
            from datetime import date
            today = date.today().isoformat()
            resp = await client.post("/api/entries", json={
                "project_id": project_id,
                "description": "Pre-restart work",
                "start_time": f"{today}T10:00:00",
                "end_time": f"{today}T11:00:00"
            })
            if resp.status_code == 201:
                entry_id = resp.json()["id"]
                print(f"       -> Created entry id={entry_id} (1 hour of work)")
            else:
                failures.append(f"FAIL: Could not create entry on server 1: {resp.text}")

    print("Step 2: Stopping server (simulating server restart)...")
    proc1.terminate()
    proc1.wait(timeout=5)
    print("       -> Server 1 stopped")

    port2 = find_free_port()
    print(f"Step 3: Starting second server instance on port {port2} with same database...")

    proc2 = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(port2), "--host", "127.0.0.1"],
        cwd=SPRINT_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    if not wait_for_server(port2):
        proc2.terminate()
        proc2.wait()
        os.unlink(test_db)
        print("FAIL: Second server instance did not start within timeout")
        sys.exit(1)

    print(f"       -> Server 2 started (pid={proc2.pid})")

    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port2}") as client:
        if project_id:
            resp = await client.get(f"/api/projects/{project_id}")
            if resp.status_code == 200:
                p = resp.json()
                if p.get("name") == "Persistent Project":
                    print(f"       -> Project still exists after restart: '{p['name']}'")
                else:
                    failures.append(f"FAIL: Project data corrupted after restart: {p}")
            else:
                failures.append(f"FAIL: Project {project_id} not found after restart: {resp.status_code}")

        if entry_id:
            from datetime import date
            today = date.today().isoformat()
            resp = await client.get(f"/api/entries?date={today}")
            if resp.status_code == 200:
                entries = resp.json()
                entry_ids = [e["id"] for e in entries]
                if entry_id in entry_ids:
                    print(f"       -> Entry {entry_id} still exists after restart")
                else:
                    failures.append(f"FAIL: Entry {entry_id} missing after restart. Found ids: {entry_ids}")
            else:
                failures.append(f"FAIL: Could not list entries after restart: {resp.status_code}")

    proc2.terminate()
    proc2.wait(timeout=5)
    print("       -> Server 2 stopped")

    try:
        os.unlink(test_db)
    except FileNotFoundError:
        pass

    if failures:
        for f in failures:
            print(f)
        print(f"\n=== VALUE DELIVERY FAILED: {len(failures)} step(s) failed ===")
        sys.exit(1)
    else:
        print()
        print("=== ALL PERSISTENCE VALUE DELIVERY STEPS PASSED ===")
        sys.exit(0)

asyncio.run(run())
