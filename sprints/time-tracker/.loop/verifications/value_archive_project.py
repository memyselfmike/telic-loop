#!/usr/bin/env python3
"""
Verification: Archive project - disappears from timer dropdown, history preserved
PRD Reference: Section 3.1 (PUT /api/projects/{id} with archived=true), Section 4.2 (active projects in dropdown)
Vision Goal 2: Manage Client Projects - archived projects don't appear in active timer dropdown
Vision Proof: User archives a project and it disappears from timer dropdown but its historical
              entries remain visible in reports and weekly view
Category: value
"""
import sys
import os
import asyncio
from datetime import date

SPRINT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, SPRINT_DIR)
sys.path.insert(0, os.path.dirname(SPRINT_DIR))

print("=== Value: Archive Project Workflow ===")
print("Simulating: Freelancer archives a project, it leaves the dropdown, entries stay in history")
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

        print("Step 1: Create project and log some time...")
        resp = await client.post("/api/projects", json={
            "name": "Old Client Project", "client_name": "Epsilon Co", "hourly_rate": 90.0, "color": "#f778ba"
        })
        if resp.status_code != 201:
            print(f"FAIL: Could not create project: {resp.text}")
            sys.exit(1)
        project_id = resp.json()["id"]

        resp = await client.post("/api/entries", json={
            "project_id": project_id,
            "description": "Final deliverable",
            "start_time": f"{today}T08:00:00",
            "end_time": f"{today}T10:00:00"
        })
        if resp.status_code != 201:
            failures.append(f"FAIL: Could not create entry: {resp.text}")
        else:
            entry_id = resp.json()["id"]
            print(f"       -> Created entry id={entry_id}")

        resp = await client.get("/api/projects?active=true")
        active_before = resp.json() if resp.status_code == 200 else []
        active_ids_before = [p["id"] for p in active_before]
        if project_id in active_ids_before:
            print(f"       -> Project visible in active dropdown BEFORE archive ({len(active_before)} active)")
        else:
            failures.append("FAIL: Project not in active list before archiving")

        print("Step 2: Freelancer archives the project...")
        resp = await client.put(f"/api/projects/{project_id}", json={"archived": True})
        if resp.status_code == 200:
            p = resp.json()
            if p.get("archived") == True:
                print("       -> Project archived successfully")
            else:
                failures.append(f"FAIL: archived field not set to True: {p}")
        else:
            failures.append(f"FAIL: Archive request returned {resp.status_code}: {resp.text}")

        print("Step 3: Checking timer dropdown - archived project must not appear...")
        resp = await client.get("/api/projects?active=true")
        active_after = resp.json() if resp.status_code == 200 else []
        active_ids_after = [p["id"] for p in active_after]
        if project_id not in active_ids_after:
            print(f"       -> PASS: Archived project removed from timer dropdown")
        else:
            failures.append(f"FAIL: Archived project still in active list: {active_ids_after}")

        print("Step 4: Checking that historical entries are preserved in the database...")
        resp = await client.get(f"/api/entries?date={today}")
        if resp.status_code == 200:
            entries = resp.json()
            entry_project_ids = [e["project_id"] for e in entries]
            if project_id in entry_project_ids:
                print(f"       -> PASS: Historical entries still accessible after archive ({len(entries)} entries today)")
            else:
                failures.append(f"FAIL: Entries for archived project not visible. Found project_ids: {entry_project_ids}")
        else:
            failures.append(f"FAIL: Could not fetch entries after archive: {resp.status_code}")

        resp = await client.get("/api/projects")
        all_projects = resp.json() if resp.status_code == 200 else []
        all_ids = [p["id"] for p in all_projects]
        if project_id in all_ids:
            print("       -> PASS: Archived project still visible in full project list")
        else:
            failures.append("FAIL: Archived project missing from full project list")

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
        print("=== ARCHIVE PROJECT VALUE PROOF PASSED ===")
        sys.exit(0)

asyncio.run(run())
