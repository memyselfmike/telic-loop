#!/usr/bin/env python3
"""
Verification: Time Entries API - manual entry, date filtering, project data join
PRD Reference: Section 3.2 (Time Entries endpoints)
Vision Goal: Track Time Effortlessly - manual backfill, see today's entries
Category: integration
"""
import sys
import os
import asyncio
from datetime import date, timedelta

SPRINT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, SPRINT_DIR)
sys.path.insert(0, os.path.dirname(SPRINT_DIR))

print("=== Integration: Entries API ===")

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
            "name": "Design Work", "client_name": "Beta Inc", "hourly_rate": 120.0, "color": "#d29922"
        })
        if resp.status_code != 201:
            print(f"FAIL: Could not create test project: {resp.text}")
            sys.exit(1)
        project_id = resp.json()["id"]
        project_color = "#d29922"

        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        # Test 1: POST /api/entries - create manual entry for today
        resp = await client.post("/api/entries", json={
            "project_id": project_id,
            "description": "Logo design",
            "start_time": f"{today}T09:00:00",
            "end_time": f"{today}T10:30:00"
        })
        if resp.status_code == 201:
            entry = resp.json()
            entry_id = entry.get("id")
            if entry.get("duration_seconds") == 5400:
                print(f"PASS: POST /api/entries creates manual entry with correct duration_seconds=5400")
            else:
                failures.append(f"FAIL: duration_seconds should be 5400, got: {entry.get('duration_seconds')}. Entry: {entry}")
        else:
            failures.append(f"FAIL: POST /api/entries returned {resp.status_code}: {resp.text}")
            entry_id = None

        # Test 2: EntryResponse includes project_name and project_color
        if entry_id:
            resp = await client.get(f"/api/entries?date={today}")
            if resp.status_code == 200:
                entries = resp.json()
                if entries:
                    first = entries[0]
                    if first.get("project_name") == "Design Work":
                        print("PASS: Entry response includes project_name='Design Work'")
                    else:
                        failures.append(f"FAIL: project_name missing or wrong: {first}")
                    if first.get("project_color") == project_color:
                        print(f"PASS: Entry response includes project_color='{project_color}'")
                    else:
                        failures.append(f"FAIL: project_color missing or wrong: {first}")
                else:
                    failures.append(f"FAIL: GET /api/entries?date={today} returned empty list")
            else:
                failures.append(f"FAIL: GET /api/entries?date={today} returned {resp.status_code}")

        # Test 3: POST /api/entries for yesterday
        resp = await client.post("/api/entries", json={
            "project_id": project_id,
            "description": "Yesterday's meeting",
            "start_time": f"{yesterday}T14:00:00",
            "end_time": f"{yesterday}T15:00:00"
        })
        if resp.status_code == 201:
            print(f"PASS: POST /api/entries creates entry for yesterday ({yesterday})")
        else:
            failures.append(f"FAIL: Manual entry for yesterday returned {resp.status_code}: {resp.text}")

        # Test 4: Date filter only returns entries for that date
        resp = await client.get(f"/api/entries?date={today}")
        if resp.status_code == 200:
            today_entries = resp.json()
            dates_in_response = set(e.get("start_time", "")[:10] for e in today_entries)
            if all(d == today for d in dates_in_response):
                print(f"PASS: GET /api/entries?date={today} returns only today's entries ({len(today_entries)} entries)")
            else:
                failures.append(f"FAIL: Date filter returned entries from other dates: {dates_in_response}")
        else:
            failures.append(f"FAIL: Date filter returned {resp.status_code}")

        # Test 5: Date range filter
        from_date = yesterday
        to_date = today
        resp = await client.get(f"/api/entries?from={from_date}&to={to_date}")
        if resp.status_code == 200:
            range_entries = resp.json()
            if len(range_entries) >= 2:
                print(f"PASS: GET /api/entries?from={from_date}&to={to_date} returns {len(range_entries)} entries (both dates)")
            else:
                failures.append(f"FAIL: Date range should return >= 2 entries, got {len(range_entries)}")
        else:
            failures.append(f"FAIL: Date range filter returned {resp.status_code}: {resp.text}")

        # Test 6: DELETE /api/entries/{id}
        if entry_id:
            resp = await client.delete(f"/api/entries/{entry_id}")
            if resp.status_code == 204:
                print(f"PASS: DELETE /api/entries/{entry_id} returns 204")
            else:
                failures.append(f"FAIL: DELETE /api/entries/{entry_id} returned {resp.status_code}")

        # Test 7: DELETE project with entries returns 409
        resp = await client.delete(f"/api/projects/{project_id}")
        if resp.status_code == 409:
            print("PASS: DELETE /api/projects with entries returns 409 Conflict")
        else:
            failures.append(f"FAIL: Deleting project with entries should return 409, got {resp.status_code}")

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
        print("\n=== ALL ENTRIES API INTEGRATION TESTS PASSED ===")
        sys.exit(0)

asyncio.run(run())
