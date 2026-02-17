#!/usr/bin/env python3
"""
Verification: Timer API - start, stop, auto-switch, elapsed time, persistence
PRD Reference: Section 3.3 (Timer endpoints)
Vision Goal: Track Time Effortlessly - start/stop timer, server-side state
Category: integration
"""
import sys
import os
import asyncio
import time

SPRINT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, SPRINT_DIR)
sys.path.insert(0, os.path.dirname(SPRINT_DIR))

print("=== Integration: Timer API ===")

try:
    import httpx
    from httpx import AsyncClient
except ImportError:
    print("FAIL: httpx not installed")
    sys.exit(1)

async def run():
    failures = []

    try:
        from backend.main import create_app
        from backend.database import init_db
        import tempfile
    except ImportError as e:
        print(f"FAIL: Cannot import app: {e}")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        test_db = f.name
    os.unlink(test_db)

    try:
        init_db(test_db)
        app = create_app(db_path=test_db)
    except TypeError:
        os.environ["TEST_DB_PATH"] = test_db
        app = create_app()

    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        resp = await client.post("/api/projects", json={
            "name": "Dev Work", "client_name": "Self", "hourly_rate": 100.0, "color": "#3fb950"
        })
        if resp.status_code != 201:
            print(f"FAIL: Could not create test project: {resp.status_code} {resp.text}")
            sys.exit(1)
        project_id = resp.json()["id"]

        # Test 1: GET /api/timer when no timer running returns null/None
        resp = await client.get("/api/timer")
        if resp.status_code == 200:
            data = resp.json()
            if data is None or data == {} or (isinstance(data, dict) and data.get("active_timer") is None):
                print("PASS: GET /api/timer returns null/none when no timer running")
            else:
                failures.append(f"FAIL: GET /api/timer should return null when no timer running, got: {data}")
        else:
            failures.append(f"FAIL: GET /api/timer returned {resp.status_code}: {resp.text}")

        # Test 2: POST /api/timer/start creates running timer
        resp = await client.post("/api/timer/start", json={"project_id": project_id, "description": "Building feature X"})
        if resp.status_code == 201:
            timer = resp.json()
            entry_id = timer.get("id")
            if "elapsed_seconds" in timer or "start_time" in timer:
                print(f"PASS: POST /api/timer/start returns 201 with timer entry id={entry_id}")
            else:
                failures.append(f"FAIL: Timer start response missing fields: {timer}")
        else:
            failures.append(f"FAIL: POST /api/timer/start returned {resp.status_code}: {resp.text}")
            entry_id = None

        await asyncio.sleep(1.5)

        # Test 3: GET /api/timer returns running timer with elapsed_seconds > 0
        resp = await client.get("/api/timer")
        if resp.status_code == 200:
            data = resp.json()
            timer_data = data.get("active_timer", data) if isinstance(data, dict) else data
            if timer_data and isinstance(timer_data, dict):
                elapsed = timer_data.get("elapsed_seconds", 0)
                if elapsed >= 1:
                    print(f"PASS: GET /api/timer returns running timer with elapsed_seconds={elapsed}")
                else:
                    failures.append(f"FAIL: elapsed_seconds should be >= 1, got: {elapsed}. Data: {timer_data}")
            else:
                failures.append(f"FAIL: GET /api/timer returned null/empty but timer should be running: {data}")
        else:
            failures.append(f"FAIL: GET /api/timer returned {resp.status_code}")

        # Test 4: POST /api/timer/stop stops the timer and returns completed entry
        resp = await client.post("/api/timer/stop")
        if resp.status_code == 200:
            stopped = resp.json()
            dur = stopped.get("duration_seconds")
            end = stopped.get("end_time")
            if dur is not None and end is not None:
                print(f"PASS: POST /api/timer/stop returns completed entry with duration_seconds={dur}")
            else:
                failures.append(f"FAIL: Stopped timer missing duration_seconds or end_time: {stopped}")
        else:
            failures.append(f"FAIL: POST /api/timer/stop returned {resp.status_code}: {resp.text}")

        # Test 5: GET /api/timer returns null after stop
        resp = await client.get("/api/timer")
        if resp.status_code == 200:
            data = resp.json()
            timer_data = data.get("active_timer", data) if isinstance(data, dict) else data
            if timer_data is None or (isinstance(timer_data, dict) and not timer_data.get("id")):
                print("PASS: GET /api/timer returns null after stopping")
            else:
                failures.append(f"FAIL: Timer still running after stop: {data}")
        else:
            failures.append(f"FAIL: GET /api/timer after stop returned {resp.status_code}")

        # Test 6: POST /api/timer/stop when no timer running returns 404
        resp = await client.post("/api/timer/stop")
        if resp.status_code == 404:
            print("PASS: POST /api/timer/stop with no running timer returns 404")
        else:
            failures.append(f"FAIL: Expected 404 when stopping non-existent timer, got {resp.status_code}: {resp.text}")

        # Test 7: Auto-switch - starting timer while one is running stops the old one
        resp = await client.post("/api/projects", json={"name": "Project B", "client_name": "Client B", "hourly_rate": 80.0})
        project_b_id = resp.json()["id"] if resp.status_code == 201 else None

        if project_b_id:
            await client.post("/api/timer/start", json={"project_id": project_id})
            await asyncio.sleep(0.5)

            resp = await client.post("/api/timer/start", json={"project_id": project_b_id})
            if resp.status_code == 201:
                new_timer = resp.json()
                if new_timer.get("project_id") == project_b_id:
                    print("PASS: Starting new timer auto-switches (old timer stopped, new one started)")
                else:
                    failures.append(f"FAIL: New timer has wrong project_id: {new_timer}")
            else:
                failures.append(f"FAIL: Auto-switch start returned {resp.status_code}: {resp.text}")

            resp = await client.get("/api/timer")
            data = resp.json()
            timer_data = data.get("active_timer", data) if isinstance(data, dict) else data
            if timer_data and isinstance(timer_data, dict) and timer_data.get("project_id") == project_b_id:
                print("PASS: Only one timer running after auto-switch (correct project)")
            else:
                failures.append(f"FAIL: Timer state after auto-switch unexpected: {data}")

            await client.post("/api/timer/stop")

    try:
        os.unlink(test_db)
    except FileNotFoundError:
        pass

    if failures:
        for f in failures:
            print(f)
        print(f"\n=== FAILED: {len(failures)} test(s) failed ===")
        sys.exit(1)
    else:
        print("\n=== ALL TIMER API INTEGRATION TESTS PASSED ===")
        sys.exit(0)

asyncio.run(run())
