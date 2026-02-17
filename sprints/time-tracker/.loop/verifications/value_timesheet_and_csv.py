#!/usr/bin/env python3
"""
Verification: Timesheet generation and CSV export - the invoicing workflow
PRD Reference: Section 3.4 (Reports), Section 4.5 (Reports View)
Vision Goal 5: Generate Timesheets - show hours by day/project with amounts, export CSV
Category: value
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

print("=== Value: Timesheet Generation and CSV Export ===")
print("Simulating: Freelancer generates This Week timesheet and exports CSV for invoicing")
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

        today = date.today()
        mon = today - timedelta(days=today.weekday())

        print("Step 1: Setting up projects and time entries for this week...")

        resp = await client.post("/api/projects", json={
            "name": "Website Redesign", "client_name": "Acme Corp", "hourly_rate": 150.0, "color": "#58a6ff"
        })
        if resp.status_code != 201:
            print(f"FAIL: Could not create project 1: {resp.text}")
            sys.exit(1)
        proj1_id = resp.json()["id"]

        resp = await client.post("/api/projects", json={
            "name": "Mobile App", "client_name": "Beta Inc", "hourly_rate": 200.0, "color": "#3fb950"
        })
        if resp.status_code != 201:
            print(f"FAIL: Could not create project 2: {resp.text}")
            sys.exit(1)
        proj2_id = resp.json()["id"]

        entries_data = [
            (proj1_id, "Homepage layout", mon.isoformat(), "T09:00:00", "T11:00:00"),
            (proj2_id, "API integration", mon.isoformat(), "T13:00:00", "T14:30:00"),
        ]

        if today != mon:
            entries_data.append((proj1_id, "CSS fixes", today.isoformat(), "T10:00:00", "T11:30:00"))

        created_entries = 0
        for proj_id, desc, day, start, end in entries_data:
            resp = await client.post("/api/entries", json={
                "project_id": proj_id,
                "description": desc,
                "start_time": f"{day}{start}",
                "end_time": f"{day}{end}"
            })
            if resp.status_code == 201:
                created_entries += 1
            else:
                failures.append(f"FAIL: Could not create entry {desc!r}: {resp.text}")

        unique_days = len(set(e[2] for e in entries_data))
        print(f"       -> Created {created_entries} time entries across {unique_days} day(s)")

        from_date = mon.isoformat()
        to_date = today.isoformat()
        print(f"Step 2: Generating timesheet for {from_date} to {to_date}...")

        resp = await client.get(f"/api/reports/timesheet?from={from_date}&to={to_date}")
        if resp.status_code != 200:
            failures.append(f"FAIL: Timesheet generation returned {resp.status_code}: {resp.text}")
        else:
            report = resp.json()
            print(f"       -> Report received with keys: {list(report.keys())}")

            if "entries" in report:
                entries = report["entries"]
                if len(entries) >= 2:
                    print(f"       -> PASS: Report contains {len(entries)} entries")
                else:
                    failures.append(f"FAIL: Report should have >= 2 entries, got {len(entries)}")
            else:
                failures.append("FAIL: Report missing entries field")

            if "project_totals" in report:
                totals = report["project_totals"]
                has_amount = any(
                    isinstance(v, dict) and v.get("amount", 0) > 0
                    for v in totals.values()
                ) if isinstance(totals, dict) else False

                if has_amount:
                    print("       -> PASS: project_totals includes billing amounts")
                else:
                    failures.append(f"FAIL: project_totals missing amounts: {totals}")
            else:
                failures.append("FAIL: Report missing project_totals field")

            grand_secs = report.get("grand_total_seconds", 0)
            if grand_secs > 0:
                hours_count = grand_secs / 3600
                print(f"       -> PASS: grand_total_seconds={grand_secs} ({hours_count:.1f} hours)")
            else:
                failures.append(f"FAIL: grand_total_seconds missing or zero: {grand_secs}")

            grand_amt = report.get("grand_total_amount", 0)
            if grand_amt > 0:
                print(f"       -> PASS: grand_total_amount={grand_amt:.2f}")
            else:
                failures.append(f"FAIL: grand_total_amount missing or zero: {grand_amt}")

        print("Step 3: Freelancer clicks Export CSV...")
        resp = await client.get(f"/api/reports/timesheet/csv?from={from_date}&to={to_date}")
        if resp.status_code != 200:
            failures.append(f"FAIL: CSV export returned {resp.status_code}: {resp.text}")
        else:
            csv_text = resp.text
            try:
                reader = csv.DictReader(io.StringIO(csv_text))
                required_cols = {"Date", "Project", "Client", "Description", "Hours", "Rate", "Amount"}
                actual_cols = set(reader.fieldnames or [])
                missing = required_cols - actual_cols

                if not missing:
                    print(f"       -> PASS: CSV has all required columns: {sorted(required_cols)}")
                else:
                    failures.append(f"FAIL: CSV missing columns: {missing}")

                rows = list(reader)
                if rows:
                    print(f"       -> PASS: CSV has {len(rows)} data rows")
                    sample = rows[0]
                    try:
                        hours_val = float(sample.get("Hours", 0))
                        rate_val = float(sample.get("Rate", 0))
                        amount_val = float(sample.get("Amount", 0))
                        expected_amount = hours_val * rate_val
                        if abs(amount_val - expected_amount) < 0.01:
                            print(f"       -> PASS: CSV Amount={amount_val:.2f} computed (Hours={hours_val} * Rate={rate_val})")
                        else:
                            failures.append(f"FAIL: Amount={amount_val} != Hours*Rate={expected_amount}")
                    except (ValueError, TypeError) as e:
                        failures.append(f"FAIL: Could not parse numeric fields in CSV row: {e}")
                else:
                    failures.append("FAIL: CSV has no data rows")
            except Exception as e:
                failures.append(f"FAIL: Could not parse CSV: {e}. Content: {csv_text[:200]}")

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
        print("=== TIMESHEET AND CSV VALUE PROOF PASSED ===")
        sys.exit(0)

asyncio.run(run())
