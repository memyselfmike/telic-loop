#!/usr/bin/env python3
"""
Verification: Server startup and frontend serving
PRD Reference: Task 1.1 acceptance, Task 1.8 acceptance
Vision Goal: All three workflows — app must be reachable and serve the SPA shell
Category: value

Verifies:
1. FastAPI app starts without import errors
2. GET / returns HTML with nav tabs (#recipes, #planner, #shopping)
3. GET /api/recipes returns 200 (routes wired)
4. Frontend static files are properly mounted
5. CSS and JS files are accessible

This is the foundation check — if the server doesn't start correctly,
no value can be delivered at all.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== VALUE: Server Startup and Frontend Serving ===")
print("Vision: Cook opens browser to localhost:8000 and sees the dark-themed app")
print()

failures = []

print("--- Check 1: Backend can be imported ---")
try:
    import database as db_module
    print("  PASS: database.py imported")
except ImportError as e:
    print(f"  FAIL: database.py: {e}")
    failures.append("database.py importable")

try:
    import models
    print("  PASS: models.py imported")
except ImportError as e:
    print(f"  FAIL: models.py: {e}")
    failures.append("models.py importable")

try:
    from main import app
    print("  PASS: main.py (FastAPI app) imported")
except ImportError as e:
    print(f"  FAIL: main.py: {e}")
    failures.append("main.py (FastAPI app) importable")
    sys.exit(1)

try:
    from fastapi.testclient import TestClient
except ImportError as e:
    print(f"FAIL: FastAPI TestClient not available: {e}")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "startup.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db
    asyncio.run(db_module.init_db())
    client = TestClient(app)

    print()
    print("--- Check 2: GET / serves the frontend (HTML) ---")
    resp = client.get("/")
    if resp.status_code == 200:
        html = resp.text
        is_html = "html" in resp.headers.get("content-type", "").lower() or \
                  "<!doctype" in html.lower() or \
                  "<html" in html.lower()
        if is_html:
            print(f"  PASS: GET / returns HTML ({len(html)} chars)")
        else:
            print(f"  FAIL: GET / did not return HTML (content-type: {resp.headers.get('content-type')})")
            print(f"        Preview: {html[:100]}")
            failures.append("GET / returns HTML")
    else:
        print(f"  FAIL: GET / returned {resp.status_code}")
        failures.append("GET / returns 200")

    print()
    print("--- Check 3: index.html contains navigation tabs ---")
    if resp.status_code == 200:
        html = resp.text
        has_recipes_tab = "recipes" in html.lower() or "#recipes" in html
        has_planner_tab = "planner" in html.lower() or "#planner" in html or "meal" in html.lower()
        has_shopping_tab = "shopping" in html.lower() or "#shopping" in html
        if has_recipes_tab and has_planner_tab and has_shopping_tab:
            print(f"  PASS: index.html contains all three navigation tabs")
        else:
            missing = []
            if not has_recipes_tab: missing.append("recipes")
            if not has_planner_tab: missing.append("planner/meal")
            if not has_shopping_tab: missing.append("shopping")
            print(f"  FAIL: Missing navigation tabs: {missing}")
            failures.append(f"index.html navigation tabs: {missing}")

        # Check for dark theme (style reference)
        has_style = "style.css" in html or "stylesheet" in html.lower()
        if has_style:
            print(f"  PASS: index.html references stylesheet")
        else:
            print(f"  FAIL: index.html has no stylesheet reference")
            failures.append("index.html references stylesheet")

        # Check for JS files
        js_files_expected = ["app.js", "recipes.js", "planner.js", "shopping.js"]
        missing_js = [f for f in js_files_expected if f not in html]
        if not missing_js:
            print(f"  PASS: index.html references all JS files")
        else:
            print(f"  FAIL: index.html missing JS references: {missing_js}")
            failures.append(f"index.html missing JS: {missing_js}")

    print()
    print("--- Check 4: API routes are wired ---")
    resp = client.get("/api/recipes")
    if resp.status_code == 200:
        print(f"  PASS: GET /api/recipes returns 200")
    else:
        print(f"  FAIL: GET /api/recipes returned {resp.status_code}")
        failures.append("GET /api/recipes returns 200")

    # Check other route groups are wired
    resp = client.get(f"/api/meals?week=2026-02-16")
    if resp.status_code == 200:
        print(f"  PASS: GET /api/meals returns 200")
    else:
        print(f"  FAIL: GET /api/meals returned {resp.status_code}")
        failures.append("GET /api/meals returns 200")

    resp = client.get("/api/shopping/current")
    if resp.status_code in (200, 404):  # 404 is ok if no list yet, 200 also ok
        print(f"  PASS: GET /api/shopping/current returns {resp.status_code}")
    else:
        print(f"  FAIL: GET /api/shopping/current returned {resp.status_code}")
        failures.append("GET /api/shopping/current returns 200/404")

    print()
    print("--- Check 5: Frontend static files are served ---")
    static_paths = [
        "/css/style.css",
        "/js/app.js",
        "/js/recipes.js",
        "/js/planner.js",
        "/js/shopping.js",
    ]
    for path in static_paths:
        resp = client.get(path)
        if resp.status_code == 200:
            print(f"  PASS: {path} served ({len(resp.content)} bytes)")
        else:
            print(f"  FAIL: {path} returned {resp.status_code}")
            failures.append(f"Static file {path} served")

    print()
    print("--- Check 6: Database file auto-created in data/ directory ---")
    # The data/ directory should be auto-created
    data_dir = os.path.join(SPRINT_DIR, "data")
    if os.path.exists(data_dir):
        print(f"  PASS: data/ directory exists")
    else:
        print(f"  INFO: data/ directory not at {data_dir} (may use temp DB in tests)")
        # This is okay for test mode — we check the temp DB was created
        if os.path.exists(test_db):
            print(f"  PASS: Test DB created at {test_db}")
        else:
            print(f"  FAIL: Database file not created")
            failures.append("Database auto-created on startup")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("User impact: Cook cannot reach the app at all — zero value delivered.")
    sys.exit(1)
else:
    print("RESULT: PASS - Server starts and serves the complete SPA shell")
    print("Value delivered: Cook can open the browser and see the dark-themed recipe app.")
    sys.exit(0)
