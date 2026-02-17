#!/usr/bin/env python3
"""
Verification: Core timer workflow - the primary value the freelancer uses every day
PRD Reference: Sections 3.2, 3.3
Vision Goal 1: Track Time Effortlessly - start timer, work, stop, entry saved automatically
Vision Goal 3: See Today at a Glance - today's entries with project color indicators
Vision Proof: User creates project, selects, clicks Start, sees live timer, clicks Stop,
              entry appears in today's list with correct duration and project color
Category: value
"""
import sys
import os
import asyncio
import time
from datetime import date

SPRINT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, SPRINT_DIR)
sys.path.insert(0, os.path.dirname(SPRINT_DIR))

print("=== Value: Core Timer Workflow ===")
print("Simulating: Freelancer creates project, starts timer, stops timer, sees entry in today's list")
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
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        today = date.today().isoformat()

        print("Step 1: Freelancer creates 'Website Redesign' project for Acme Corp at $150/hr...")
        resp = await client.post("/api/projects", json={
            "name": "Website Redesign",
            "client_name": "Acme Corp",
            "hourly_rate": 150.0,
            "color": "#58a6ff"
        })
        if resp.status_code != 201:
            print(f"FAIL: Could not create project: {resp.status_code} {resp.text}")
            sys.exit(1)
        project = resp.json()
        project_id = project["id"]
        print(f"       -> Project created: id={project_id}, rate=$150/hr, color=#58a6ff")

        print("Step 2: Freelancer opens timer dropdown - project must appear...")
        resp = await client.get("/api/projects?active=true")
        active_projects = resp.json() if resp.status_code == 200 else []
        active_ids = [p["id"] for p in active_projects]
        if project_id in active_ids:
            print(f"       -> Project visible in active dropdown ({len(active_projects)} active project(s))")
        else:
            failures.append("FAIL: Project not visible in active projects dropdown")

        print("Step 3: Freelancer selects project, types description, clicks Start...")
        start_time = time.time()
        resp = await client.post("/api/timer/start", json={
            "project_id": project_id,
            "description": "Homepage redesign - hero section"
        })
        if resp.status_code == 201:
            timer = resp.json()
            print(f"       -> Timer started: entry id={timer.get('id')}, start_time={timer.get('start_time')}")
        else:
            print(f"FAIL: Timer start failed: {resp.status_code} {resp.text}")
            sys.exit(1)

        print("Step 4: UI polls GET /api/timer - must show running timer with elapsed time...")
        await asyncio.sleep(2)
        resp = await client.get("/api/timer")
        if resp.status_code == 200:
            data = resp.json()
            timer_data = data.get("active_timer", data) if isinstance(data, dict) else data
            if timer_data and isinstance(timer_data, dict) and timer_data.get("id"):
                elapsed = timer_data.get("elapsed_seconds", 0)
                if elapsed >= 1:
                    print(f"       -> Timer showing: elapsed={elapsed}s, project_name={timer_data.get('project_name')}")
                else:
                    failures.append(f"FAIL: elapsed_seconds should be >= 1 after waiting 2s, got {elapsed}")
            else:
                failures.append(f"FAIL: Timer not visible in GET /api/timer after start: {data}")
        else:
            failures.append(f"FAIL: GET /api/timer returned {resp.status_code}")

        print("Step 5: Freelancer clicks Stop - entry must be saved with correct duration...")
        resp = await client.post("/api/timer/stop")
        if resp.status_code == 200:
            stopped_entry = resp.json()
            duration = stopped_entry.get("duration_seconds", 0)
            if duration >= 2:
                print(f"       -> Entry saved: duration={duration}s, end_time={stopped_entry.get('end_time')}")
            else:
                failures.append(f"FAIL: duration_seconds should be >= 2, got {duration}")
        else:
            print(f"FAIL: Timer stop failed: {resp.status_code} {resp.text}")
            sys.exit(1)

        print("Step 6: Today's entries list must show the entry with project color dot...")
        resp = await client.get(f"/api/entries?date={today}")
        if resp.status_code == 200:
            entries = resp.json()
            if entries:
                entry = entries[0]
                if entry.get("project_color") == "#58a6ff":
                    print(f"       -> Entry visible with correct project_color=#58a6ff")
                else:
                    failures.append(f"FAIL: project_color should be #58a6ff, got: {entry.get('project_color')}")
                if entry.get("project_name") == "Website Redesign":
                    print(f"       -> Entry has correct project_name='Website Redesign'")
                else:
                    failures.append(f"FAIL: project_name should be 'Website Redesign', got: {entry.get('project_name')}")
                if entry.get("description") == "Homepage redesign - hero section":
                    print(f"       -> Entry description preserved")
                else:
                    failures.append(f"FAIL: description mismatch: {entry.get('description')}")
            else:
                failures.append(f"FAIL: No entries found in today's list after stopping timer")
        else:
            failures.append(f"FAIL: GET /api/entries?date={today} returned {resp.status_code}")

        print("Step 7: Verifying timer is fully stopped (no running timer = server state is persisted)...")
        resp = await client.get("/api/timer")
        data = resp.json()
        timer_data = data.get("active_timer", data) if isinstance(data, dict) else data
        if timer_data is None or (isinstance(timer_data, dict) and not timer_data.get("id")):
            print("       -> Confirmed: no running timer (stopped entry is preserved in DB)")
        else:
            failures.append(f"FAIL: Timer still running after stop: {timer_data}")

        print()
        print("=== Value Proof: Timer Workflow Complete ===")

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
        print("=== ALL VALUE DELIVERY STEPS PASSED ===")
        sys.exit(0)

asyncio.run(run())
