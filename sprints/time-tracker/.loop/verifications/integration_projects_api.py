#!/usr/bin/env python3
"""
Verification: Projects API - CRUD operations, error handling
PRD Reference: Section 3.1 (Projects endpoints)
Vision Goal: Manage Client Projects - create, list, archive projects
Category: integration
"""
import sys
import os
import asyncio

SPRINT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, SPRINT_DIR)
sys.path.insert(0, os.path.dirname(SPRINT_DIR))

print("=== Integration: Projects API ===")

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
        import tempfile, os
    except ImportError as e:
        print(f"FAIL: Cannot import app: {e}")
        sys.exit(1)

    # Use a temp database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        test_db = f.name
    os.unlink(test_db)

    try:
        init_db(test_db)
        app = create_app(db_path=test_db)
    except TypeError:
        # create_app may not accept db_path - try env var approach
        os.environ['TEST_DB_PATH'] = test_db
        try:
            app = create_app()
        except Exception as e:
            print(f"FAIL: Cannot create app with test db: {e}")
            sys.exit(1)

    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # Test 1: POST /api/projects - create project
        resp = await client.post("/api/projects", json={
            "name": "Website Redesign",
            "client_name": "Acme Corp",
            "hourly_rate": 150.0,
            "color": "#58a6ff"
        })
        if resp.status_code == 201:
            project = resp.json()
            project_id = project.get('id')
            print(f"PASS: POST /api/projects returns 201, id={project_id}")
        else:
            failures.append(f"FAIL: POST /api/projects returned {resp.status_code}: {resp.text}")
            project_id = None

        # Test 2: GET /api/projects - list all
        resp = await client.get("/api/projects")
        if resp.status_code == 200:
            projects = resp.json()
            if isinstance(projects, list) and len(projects) >= 1:
                print(f"PASS: GET /api/projects returns list with {len(projects)} project(s)")
            else:
                failures.append(f"FAIL: GET /api/projects returned unexpected data: {projects}")
        else:
            failures.append(f"FAIL: GET /api/projects returned {resp.status_code}: {resp.text}")

        # Test 3: GET /api/projects?active=true - excludes archived
        resp = await client.get("/api/projects?active=true")
        if resp.status_code == 200:
            active = resp.json()
            if isinstance(active, list):
                print(f"PASS: GET /api/projects?active=true returns {len(active)} active project(s)")
            else:
                failures.append(f"FAIL: active filter returned unexpected data: {active}")
        else:
            failures.append(f"FAIL: GET /api/projects?active=true returned {resp.status_code}")

        # Test 4: GET /api/projects/{id}
        if project_id:
            resp = await client.get(f"/api/projects/{project_id}")
            if resp.status_code == 200:
                p = resp.json()
                if p.get('name') == 'Website Redesign':
                    print(f"PASS: GET /api/projects/{project_id} returns correct project")
                else:
                    failures.append(f"FAIL: GET /api/projects/{project_id} returned wrong data: {p}")
            else:
                failures.append(f"FAIL: GET /api/projects/{project_id} returned {resp.status_code}")

        # Test 5: GET nonexistent project returns 404
        resp = await client.get("/api/projects/99999")
        if resp.status_code == 404:
            print("PASS: GET /api/projects/99999 returns 404")
        else:
            failures.append(f"FAIL: Expected 404 for nonexistent project, got {resp.status_code}")

        # Test 6: PUT /api/projects/{id} - update
        if project_id:
            resp = await client.put(f"/api/projects/{project_id}", json={"hourly_rate": 175.0})
            if resp.status_code == 200:
                updated = resp.json()
                if updated.get('hourly_rate') == 175.0:
                    print(f"PASS: PUT /api/projects/{project_id} updates hourly_rate to 175.0")
                else:
                    failures.append(f"FAIL: PUT did not update hourly_rate: {updated}")
            else:
                failures.append(f"FAIL: PUT /api/projects/{project_id} returned {resp.status_code}: {resp.text}")

        # Test 7: Archive project via PUT
        if project_id:
            resp = await client.put(f"/api/projects/{project_id}", json={"archived": True})
            if resp.status_code == 200:
                archived_p = resp.json()
                if archived_p.get('archived') == True:
                    print("PASS: PUT /api/projects/{id} with archived=true archives project")
                else:
                    failures.append(f"FAIL: archived field not set: {archived_p}")
            else:
                failures.append(f"FAIL: Archive via PUT returned {resp.status_code}: {resp.text}")

        # Test 8: Archived project not in ?active=true list
        if project_id:
            resp = await client.get("/api/projects?active=true")
            active = resp.json() if resp.status_code == 200 else []
            active_ids = [p.get('id') for p in active]
            if project_id not in active_ids:
                print("PASS: Archived project excluded from ?active=true list")
            else:
                failures.append(f"FAIL: Archived project still in active list: {active_ids}")

        # Test 9: DELETE project with no entries returns 204
        resp2 = await client.post("/api/projects", json={"name": "Temp Project", "client_name": "", "hourly_rate": 0})
        if resp2.status_code == 201:
            temp_id = resp2.json()['id']
            del_resp = await client.delete(f"/api/projects/{temp_id}")
            if del_resp.status_code == 204:
                print(f"PASS: DELETE /api/projects/{temp_id} (no entries) returns 204")
            else:
                failures.append(f"FAIL: DELETE with no entries returned {del_resp.status_code}: {del_resp.text}")
        else:
            failures.append(f"FAIL: Could not create temp project for delete test")

    # Cleanup
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
        print("\n=== ALL PROJECTS API INTEGRATION TESTS PASSED ===")
        sys.exit(0)

asyncio.run(run())
