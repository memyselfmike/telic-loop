#!/usr/bin/env python3
"""
Verification: User opens localhost:8000 and sees 5 seed recipes immediately
PRD Reference: Section 2.3 (Seed Data), Task 1.2 acceptance
Vision Goal: "Build a Recipe Collection" - populated app on first visit eliminates cold start
Category: value

This is the first value proof: the cook opens the app and immediately has
recipes to work with — they are not staring at an empty grid.

Verifies:
1. Server serves the frontend at /
2. GET /api/recipes returns 5 seed recipes on fresh DB
3. Each recipe has category (covers all 5 categories)
4. Each recipe has ingredients (not empty)
5. No duplicates on second startup (idempotent seeding)
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== VALUE: Seed Recipes on First Open ===")
print("Vision: User opens the app and sees 5 populated recipes immediately")
print()

failures = []

try:
    from fastapi.testclient import TestClient
    import database as db_module
    from main import app
    print("OK: FastAPI app imported")
except ImportError as e:
    print(f"FAIL: Cannot import app: {e}")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "fresh.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db

    # Simulate: first startup
    try:
        asyncio.run(db_module.init_db())
        print("OK: Fresh database initialized (simulating first startup)")
    except Exception as e:
        print(f"FAIL: init_db raised: {e}")
        sys.exit(1)

    client = TestClient(app)

    print()
    print("--- Value Check 1: Server serves frontend at / ---")
    resp = client.get("/")
    if resp.status_code == 200:
        content_type = resp.headers.get("content-type", "")
        # Should return HTML
        if "html" in content_type or "<html" in resp.text.lower() or "<!doctype" in resp.text.lower():
            print(f"  PASS: GET / returns HTML (content-type: {content_type})")
        else:
            print(f"  FAIL: GET / returned non-HTML (content-type: {content_type})")
            print(f"        First 100 chars: {resp.text[:100]}")
            failures.append("GET / serves HTML frontend")
    else:
        print(f"  FAIL: GET / returned {resp.status_code} (expected 200)")
        failures.append("GET / serves frontend (200)")

    print()
    print("--- Value Check 2: Fresh DB has exactly 5 seed recipes ---")
    resp = client.get("/api/recipes")
    if resp.status_code == 200:
        recipes = resp.json()
        count = len(recipes)
        if count == 5:
            print(f"  PASS: GET /api/recipes returns exactly 5 seed recipes")
        elif count > 5:
            print(f"  FAIL: Expected 5 seed recipes, got {count} (over-seeded?)")
            failures.append("Seed data: exactly 5 recipes")
        else:
            print(f"  FAIL: Expected 5 seed recipes, got {count}")
            failures.append("Seed data: exactly 5 recipes")
    else:
        print(f"  FAIL: GET /api/recipes returned {resp.status_code}")
        failures.append("GET /api/recipes on fresh DB returns 200")
        recipes = []

    print()
    print("--- Value Check 3: All 5 categories represented ---")
    categories = {r.get("category") for r in recipes}
    expected_cats = {"breakfast", "lunch", "dinner", "snack", "dessert"}
    missing = expected_cats - categories
    extra = categories - expected_cats
    if not missing and not extra:
        print(f"  PASS: All 5 categories present: {categories}")
    else:
        if missing:
            print(f"  FAIL: Missing categories: {missing}")
            failures.append(f"Seed data: missing categories {missing}")
        if extra:
            print(f"  FAIL: Unexpected categories: {extra}")
            failures.append(f"Seed data: unexpected categories {extra}")

    print()
    print("--- Value Check 4: Each seed recipe has ingredients ---")
    empty_recipes = []
    for r in recipes:
        rid = r.get("id")
        # Get full recipe with ingredients
        detail_resp = client.get(f"/api/recipes/{rid}")
        if detail_resp.status_code == 200:
            detail = detail_resp.json()
            ings = detail.get("ingredients", [])
            if len(ings) < 3:
                empty_recipes.append((r.get("title"), len(ings)))
        else:
            empty_recipes.append((r.get("title"), "error"))

    if not empty_recipes:
        print(f"  PASS: All seed recipes have at least 3 ingredients")
    else:
        print(f"  FAIL: These recipes have < 3 ingredients: {empty_recipes}")
        failures.append("Seed recipes have 3+ ingredients each")

    print()
    print("--- Value Check 5: Idempotent seeding (no duplicates on second init) ---")
    # Call init_db again - simulating server restart
    try:
        asyncio.run(db_module.init_db())
        resp2 = client.get("/api/recipes")
        if resp2.status_code == 200:
            count_after = len(resp2.json())
            if count_after == len(recipes):  # Same count as before
                print(f"  PASS: Second init_db() did not create duplicate seeds (still {count_after} recipes)")
            else:
                print(f"  FAIL: Seed count changed from {len(recipes)} to {count_after} after second startup")
                failures.append("Idempotent seeding: no duplicates on restart")
    except Exception as e:
        print(f"  FAIL: Second init_db() raised: {e}")
        failures.append("Idempotent seeding: second init_db() succeeds")

    print()
    print("--- Value Check 6: Recipe cards have required display fields ---")
    for r in recipes[:2]:  # Check first 2 seeds
        title = r.get("title")
        has_category = bool(r.get("category"))
        has_prep = "prep_time_minutes" in r
        has_cook = "cook_time_minutes" in r
        if has_category and has_prep and has_cook:
            print(f"  PASS: '{title}' has category, prep time, cook time")
        else:
            missing_fields = []
            if not has_category: missing_fields.append("category")
            if not has_prep: missing_fields.append("prep_time_minutes")
            if not has_cook: missing_fields.append("cook_time_minutes")
            print(f"  FAIL: '{title}' missing fields: {missing_fields}")
            failures.append(f"Recipe card fields: {title} missing {missing_fields}")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} value check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("User impact: Cook opens the app and sees an empty grid with no guidance.")
    sys.exit(1)
else:
    print("RESULT: PASS - User opens app and sees 5 populated seed recipes immediately")
    print("Value delivered: No cold start, cook can explore the app right away.")
    sys.exit(0)
