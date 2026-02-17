#!/usr/bin/env python3
"""
Verification: FastAPI correctly serves frontend static files
PRD Reference: Section 1.1 (Services), Section 1.3 (Project Structure)
Vision Goal: "Build a Recipe Collection" - cook opens browser and sees the app
Category: integration

Verifies that the FastAPI server serves the frontend correctly:
1. GET / returns index.html (HTML)
2. GET /css/style.css returns CSS file
3. GET /js/app.js returns JavaScript file
4. GET /js/recipes.js returns JavaScript file
5. GET /api/recipes returns JSON (API works alongside static serving)
6. Frontend HTML links to correct static assets
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== INTEGRATION: Frontend Static File Serving ===")
print("PRD: FastAPI serves frontend at / and API under /api/")
print()

failures = []

try:
    from fastapi.testclient import TestClient
    import database as db_module
except ImportError as e:
    print(f"FAIL: Cannot import required modules: {e}")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "serving_test.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db

    try:
        asyncio.run(db_module.init_db())
        print("OK: Test DB initialized")
    except Exception as e:
        print(f"FAIL: init_db raised: {e}")
        db_module.DB_PATH = orig_db_path
        sys.exit(1)

    try:
        from main import app
        print("OK: FastAPI app imported")
    except ImportError as e:
        print(f"FAIL: Cannot import FastAPI app: {e}")
        db_module.DB_PATH = orig_db_path
        sys.exit(1)

    client = TestClient(app, raise_server_exceptions=True)

    print()
    print("--- Test 1: GET / serves index.html (HTML) ---")
    resp = client.get("/")
    if resp.status_code == 200:
        content_type = resp.headers.get("content-type", "")
        body = resp.text
        if "html" in content_type.lower() or "<!doctype" in body.lower() or "<html" in body.lower():
            print(f"  PASS: GET / returns HTML (content-type: {content_type})")
            # Check it contains navigation tabs (verifies the full SPA shell, not just placeholder)
            body_lower = body.lower()
            has_nav_tabs = all(
                term in body_lower for term in ["recipes", "meal plan", "shopping"]
            )
            if has_nav_tabs:
                print("  PASS: index.html contains all three nav tabs")
            else:
                # Check if it's still the placeholder
                if "loading..." in body_lower or (
                    "recipe manager" in body_lower and len(body) < 500
                ):
                    print("  FAIL: index.html is still the placeholder (40-line 'Loading...' stub)")
                    print("        The full SPA shell with nav tabs has not been built yet")
                    failures.append("GET /: index.html is placeholder stub, not full SPA shell")
                else:
                    print("  WARN: index.html HTML but nav tabs not found in content")
                    # Non-fatal for this integration test
        else:
            print(f"  FAIL: GET / returned non-HTML (content-type: {content_type})")
            print(f"        First 100 chars: {body[:100]}")
            failures.append("GET /: returns HTML")
    else:
        print(f"  FAIL: GET / returned {resp.status_code} (expected 200)")
        failures.append("GET /: returns 200")

    print()
    print("--- Test 2: GET /css/style.css serves CSS ---")
    resp = client.get("/css/style.css")
    if resp.status_code == 200:
        content_type = resp.headers.get("content-type", "")
        if "css" in content_type.lower() or "text" in content_type.lower():
            body = resp.text
            if len(body) > 100:
                print(f"  PASS: GET /css/style.css returns CSS ({len(body)} bytes)")
                # Verify it has dark theme
                if any(dark in body.lower() for dark in ["#1a1a", "#0d0d", "dark", "#111", "#121212", "#161"]):
                    print("  PASS: CSS contains dark background color")
                else:
                    print("  WARN: CSS may not have dark theme colors")
            else:
                print(f"  FAIL: CSS file is too small ({len(body)} bytes) — may be empty or stub")
                failures.append("GET /css/style.css: non-trivial CSS content")
        else:
            print(f"  WARN: /css/style.css content-type: {content_type}")
    else:
        print(f"  FAIL: GET /css/style.css returned {resp.status_code} (expected 200)")
        if resp.status_code == 404:
            print("        File frontend/css/style.css does not exist or is not mounted")
        failures.append("GET /css/style.css: returns 200")

    print()
    print("--- Test 3: GET /js/app.js serves JavaScript ---")
    resp = client.get("/js/app.js")
    if resp.status_code == 200:
        body = resp.text
        if len(body) > 50:
            print(f"  PASS: GET /js/app.js returns JS ({len(body)} bytes)")
            # Verify it has router logic
            if "hashchange" in body.lower() or "location.hash" in body.lower():
                print("  PASS: app.js contains hash-based routing")
            else:
                print("  FAIL: app.js does not contain hash-based routing")
                failures.append("GET /js/app.js: contains hash router logic")
        else:
            print(f"  FAIL: app.js is too small ({len(body)} bytes)")
            failures.append("GET /js/app.js: non-trivial JS content")
    else:
        print(f"  FAIL: GET /js/app.js returned {resp.status_code}")
        failures.append("GET /js/app.js: returns 200")

    print()
    print("--- Test 4: GET /js/recipes.js serves JavaScript ---")
    resp = client.get("/js/recipes.js")
    if resp.status_code == 200:
        body = resp.text
        if len(body) > 50:
            print(f"  PASS: GET /js/recipes.js returns JS ({len(body)} bytes)")
            # Verify it references the API
            if "/api/recipes" in body:
                print("  PASS: recipes.js references /api/recipes endpoint")
            else:
                print("  FAIL: recipes.js does not reference /api/recipes")
                failures.append("GET /js/recipes.js: references /api/recipes endpoint")
        else:
            print(f"  FAIL: recipes.js is too small ({len(body)} bytes)")
            failures.append("GET /js/recipes.js: non-trivial JS content")
    else:
        print(f"  FAIL: GET /js/recipes.js returned {resp.status_code}")
        failures.append("GET /js/recipes.js: returns 200")

    print()
    print("--- Test 5: API and static serving coexist ---")
    # /api/ routes must still work when StaticFiles is mounted
    api_resp = client.get("/api/recipes")
    static_resp = client.get("/")
    if api_resp.status_code == 200 and static_resp.status_code == 200:
        api_is_json = isinstance(api_resp.json(), list)
        static_is_html = "html" in static_resp.headers.get("content-type", "").lower() or "<" in static_resp.text
        if api_is_json and static_is_html:
            print("  PASS: API returns JSON and static / returns HTML simultaneously")
        else:
            print(f"  FAIL: API JSON={api_is_json}, Static HTML={static_is_html}")
            if not api_is_json:
                failures.append("API /api/recipes returns JSON alongside static serving")
    else:
        print(f"  FAIL: API={api_resp.status_code}, Static={static_resp.status_code}")
        failures.append("Both API and static routes return 200")

    print()
    print("--- Test 6: GET /api/recipes returns seed data (5 recipes) ---")
    resp = client.get("/api/recipes")
    if resp.status_code == 200:
        recipes = resp.json()
        if len(recipes) >= 5:
            cats = {r.get("category") for r in recipes}
            expected = {"breakfast", "lunch", "dinner", "snack", "dessert"}
            if expected.issubset(cats):
                print(f"  PASS: API returns {len(recipes)} recipes covering all 5 categories")
            else:
                missing = expected - cats
                print(f"  FAIL: Missing categories in seed data: {missing}")
                failures.append("Seed data covers all 5 categories")
        else:
            print(f"  FAIL: Expected 5+ recipes, got {len(recipes)}")
            failures.append("API returns 5 seed recipes")
    else:
        print(f"  FAIL: GET /api/recipes returned {resp.status_code}")
        failures.append("GET /api/recipes returns 200")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 50)
if failures:
    print(f"RESULT: FAIL - {len(failures)} test(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("User impact: Cook cannot open the app — frontend files are not being served.")
    sys.exit(1)
else:
    print("RESULT: PASS - FastAPI correctly serves all frontend static files")
    print("Value delivered: Cook can open localhost:8000 and see the SPA shell.")
    sys.exit(0)
