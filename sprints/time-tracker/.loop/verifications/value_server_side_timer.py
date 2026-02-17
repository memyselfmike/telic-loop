#!/usr/bin/env python3
"""
Verification: Server-side timer state - timer persists across browser close/reopen
PRD Reference: Section 3.3 (Timer), Section 6 AC #3 (Timer survives browser close)
Vision Goal 6: Trust the Data - closing browser while timer is running, reopening shows timer still counting
Vision Proof: User closes browser tab, reopens app, previously started timer still running with accurate elapsed time
Category: value
"""
import sys
import os
import asyncio
import time
from datetime import datetime

SPRINT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, SPRINT_DIR)
sys.path.insert(0, os.path.dirname(SPRINT_DIR))

print("=== Value: Server-Side Timer Persistence ===")
print("Simulating: Freelancer starts timer, 'closes browser' (new client), elapsed time is accurate")
print()

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

    # Simulate "Browser Session 1" (freelancer starts timer)
    async with AsyncClient(transport=transport, base_url="http://test") as client1:
        resp = await client1.post("/api/projects", json={
            "name": "Consulting", "client_name": "Delta LLC", "hourly_rate": 250.0
        })
        if resp.status_code != 201:
            print(f"FAIL: Could not create project: {resp.text}")
            sys.exit(1)
        project_id = resp.json()["id"]

        print("Step 1: Freelancer starts timer in Browser Session 1...")
        resp = await client1.post("/api/timer/start", json={"project_id": project_id, "description": "Strategy call"})
        if resp.status_code != 201:
            print(f"FAIL: Timer start failed: {resp.text}")
            sys.exit(1)

        timer_data = resp.json()
        start_time_str = timer_data.get("start_time")
        print(f"       -> Timer started at: {start_time_str}")

    # Wait 3 seconds - simulating browser being closed
    print("Step 2: Freelancer 'closes the browser tab' (3 second pause)...")
    await asyncio.sleep(3)
    print("       -> 3 seconds elapsed since timer was started")

    # Simulate "Browser Session 2" (freelancer reopens app)
    async with AsyncClient(transport=transport, base_url="http://test") as client2:
        print("Step 3: Freelancer reopens the app - GET /api/timer must show running timer...")
        resp = await client2.get("/api/timer")

        if resp.status_code != 200:
            failures.append(f"FAIL: GET /api/timer returned {resp.status_code}")
        else:
            data = resp.json()
            timer_obj = data.get("active_timer", data) if isinstance(data, dict) else data

            if timer_obj is None or (isinstance(timer_obj, dict) and not timer_obj.get("id")):
                failures.append("FAIL: GET /api/timer returned null - timer was NOT preserved server-side!")
            elif isinstance(timer_obj, dict):
                elapsed = timer_obj.get("elapsed_seconds", 0)

                if elapsed >= 3:
                    print(f"       -> Timer still running! elapsed_seconds={elapsed} (started {elapsed}s ago)")
                else:
                    failures.append(f"FAIL: elapsed_seconds={elapsed} but expected >= 3s after 3s wait")

                if start_time_str:
                    try:
                        start_dt = datetime.fromisoformat(start_time_str)
                        now = datetime.now()
                        expected_elapsed = (now - start_dt).total_seconds()
                        if abs(elapsed - expected_elapsed) <= 2:
                            print(f"       -> elapsed_seconds is accurately computed from start_time (within 2s tolerance)")
                        else:
                            failures.append(f"FAIL: elapsed_seconds={elapsed} but expected ~{expected_elapsed:.0f}s from start_time={start_time_str}")
                    except ValueError:
                        pass

                print(f"       -> project_name: {timer_obj.get('project_name')}")

                await client2.post("/api/timer/stop")
            else:
                failures.append(f"FAIL: Unexpected timer data type: {type(timer_obj)}: {timer_obj}")

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
        print("=== SERVER-SIDE TIMER PERSISTENCE VALUE PROOF PASSED ===")
        sys.exit(0)

asyncio.run(run())
