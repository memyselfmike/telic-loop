#!/usr/bin/env python3
"""
Verification: Reports API - timesheet generation, CSV export, correct totals
PRD Reference: Section 3.4 (Reports endpoints)
Vision Goal: Generate Timesheets - billable hours by project with amounts, CSV export
Category: integration
"""
import sys
import os
import asyncio
import csv
import io
from datetime import date, timedelta

SPRINT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, SPRINT_DIR)
sys.path.insert(0, os.path.dirname(SPRINT_DIR))

print("=== Integration: Reports API ===")

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
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        resp = await client.post("/api/projects", json={
            "name": "Branding Project", "client_name": "Gamma Ltd", "hourly_rate": 200.0, "color": "#bc8cff"
        })
        if resp.status_code != 201:
            print(f"FAIL: Could not create project: {resp.text}")
            sys.exit(1)
        project_id = resp.json()["id"]

        resp1 = await client.post("/api/entries", json={
            "project_id": project_id, "description": "Brand strategy",
            "start_time": f"{today}T09:00:00", "end_time": f"{today}T11:00:00"
        })
        resp2 = await client.post("/api/entries", json={
            "project_id": project_id, "description": "Logo concepts",
            "start_time": f"{today}T13:00:00", "end_time": f"{today}T14:30:00"
        })

        if resp1.status_code != 201 or resp2.status_code != 201:
            failures.append(f"FAIL: Could not create test entries: {resp1.status_code}, {resp2.status_code}")
        else:
            # Test 1: GET /api/reports/timesheet?from=DATE&to=DATE
            resp = await client.get(f"/api/reports/timesheet?from={today}&to={today}")
            if resp.status_code == 200:
                report = resp.json()
                if "entries" not in report and "project_totals" not in report:
                    failures.append(f"FAIL: Timesheet response missing required fields: {list(report.keys())}")
                else:
                    print("PASS: GET /api/reports/timesheet returns structured report")

                expected_seconds = 12600
                grand_total = report.get("grand_total_seconds", 0)
                if grand_total == expected_seconds:
                    print(f"PASS: grand_total_seconds={grand_total} (correct: 3.5 hours)")
                else:
                    failures.append(f"FAIL: grand_total_seconds={grand_total}, expected {expected_seconds}")

                expected_amount = 700.0
                grand_amount = report.get("grand_total_amount", 0)
                if abs(grand_amount - expected_amount) < 0.01:
                    print(f"PASS: grand_total_amount={grand_amount} (correct: $700)")
                else:
                    failures.append(f"FAIL: grand_total_amount={grand_amount}, expected {expected_amount}")
            else:
                failures.append(f"FAIL: GET /api/reports/timesheet returned {resp.status_code}: {resp.text}")

            # Test 2: GET /api/reports/timesheet/csv returns valid CSV
            resp = await client.get(f"/api/reports/timesheet/csv?from={today}&to={today}")
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                if "csv" in content_type or "text" in content_type:
                    print(f"PASS: CSV endpoint returns content-type: {content_type}")
                else:
                    failures.append(f"FAIL: CSV content-type unexpected: {content_type}")

                csv_text = resp.text
                reader = csv.DictReader(io.StringIO(csv_text))
                required_cols = {"Date", "Project", "Client", "Description", "Hours", "Rate", "Amount"}
                if reader.fieldnames:
                    actual_cols = set(reader.fieldnames)
                    missing = required_cols - actual_cols
                    if not missing:
                        print(f"PASS: CSV has all required columns: {required_cols}")
                    else:
                        failures.append(f"FAIL: CSV missing columns: {missing}. Has: {actual_cols}")

                    rows = list(reader)
                    if rows:
                        first_row = rows[0]
                        if first_row.get("Project") == "Branding Project":
                            print("PASS: CSV rows contain correct project name")
                        else:
                            failures.append(f"FAIL: CSV project name wrong: {first_row}")
                        if first_row.get("Client") == "Gamma Ltd":
                            print("PASS: CSV rows contain correct client name")
                        else:
                            failures.append(f"FAIL: CSV client name wrong: {first_row}")
                    else:
                        failures.append("FAIL: CSV has no data rows")
                else:
                    failures.append(f"FAIL: Could not parse CSV headers: {csv_text[:200]}")
            else:
                failures.append(f"FAIL: CSV export returned {resp.status_code}: {resp.text}")

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
        print("\n=== ALL REPORTS API INTEGRATION TESTS PASSED ===")
        sys.exit(0)

asyncio.run(run())
