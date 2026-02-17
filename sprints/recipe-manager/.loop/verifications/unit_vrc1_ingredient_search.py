#!/usr/bin/env python3
"""
Verification: VRC-1 — Recipe search by ingredient name via SQL JOIN
PRD Reference: Section 3.1 (GET /api/recipes?search=), Task VRC-1
Vision Goal: "Build a Recipe Collection" - search by ingredient ("what can I make with chicken?")
Category: unit

The VRC-1 bug: GET /api/recipes?search=X only searches title and description fields.
The fix: LEFT JOIN with ingredients table, add OR i.item LIKE ?, use SELECT DISTINCT.

This test verifies the fix is in place by checking that:
1. Searching for an ingredient name returns recipes that have that ingredient
2. The search does not create duplicate results when multiple ingredients match
3. Combined filters (category + search by ingredient) still work with AND logic
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== VRC-1: Recipe Search by Ingredient Name ===")
print("PRD: GET /api/recipes?search= must search title, description, AND ingredient items")
print()

failures = []

try:
    from fastapi.testclient import TestClient
    import database as db_module
    print("OK: database module imported")
except ImportError as e:
    print(f"FAIL: Cannot import database module: {e}")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "vrc1_test.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db

    try:
        asyncio.run(db_module.init_db())
        print(f"OK: Fresh test DB initialized")
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
    print("--- Setup: Create recipes with distinct titles and ingredients ---")

    # Recipe 1: "Boring Title A" with "rolled oats" as ingredient
    r1 = client.post("/api/recipes", json={
        "title": "Boring Title A",
        "description": "A simple recipe",
        "category": "breakfast",
        "prep_time_minutes": 5,
        "cook_time_minutes": 10,
        "servings": 1,
        "instructions": "",
        "tags": "easy",
        "ingredients": [
            {"quantity": 1.0, "unit": "cup", "item": "rolled oats", "grocery_section": "pantry"},
            {"quantity": 2.0, "unit": "cup", "item": "almond milk", "grocery_section": "dairy"},
        ]
    })

    # Recipe 2: "Boring Title B" with "broccoli" as ingredient
    r2 = client.post("/api/recipes", json={
        "title": "Boring Title B",
        "description": "Another simple recipe",
        "category": "dinner",
        "prep_time_minutes": 15,
        "cook_time_minutes": 20,
        "servings": 2,
        "instructions": "",
        "tags": "quick",
        "ingredients": [
            {"quantity": 1.0, "unit": "lb", "item": "beef strips", "grocery_section": "meat"},
            {"quantity": 2.0, "unit": "cup", "item": "broccoli", "grocery_section": "produce"},
            {"quantity": 2.0, "unit": "tbsp", "item": "soy sauce", "grocery_section": "pantry"},
        ]
    })

    # Recipe 3: "Boring Title C" with multiple ingredients containing "tomato"
    # (used to test SELECT DISTINCT)
    r3 = client.post("/api/recipes", json={
        "title": "Boring Title C",
        "description": "Tomato heavy dish",
        "category": "dinner",
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "servings": 2,
        "instructions": "",
        "tags": "italian",
        "ingredients": [
            {"quantity": 2.0, "unit": "cup", "item": "cherry tomatoes", "grocery_section": "produce"},
            {"quantity": 1.0, "unit": "cup", "item": "sun-dried tomatoes", "grocery_section": "pantry"},
        ]
    })

    if any(r.status_code != 201 for r in [r1, r2, r3]):
        print(f"FAIL: Setup recipes not created: {r1.status_code}, {r2.status_code}, {r3.status_code}")
        db_module.DB_PATH = orig_db_path
        sys.exit(1)

    r1_id = r1.json()["id"]
    r2_id = r2.json()["id"]
    r3_id = r3.json()["id"]
    print(f"  OK: Recipes created: A={r1_id}, B={r2_id}, C={r3_id}")

    print()
    print("--- Test 1: Search by ingredient name finds recipe (not title/description match) ---")
    # "oats" is not in the title or description of Recipe A — only in ingredients
    resp = client.get("/api/recipes?search=oats")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r["title"] for r in results]
        if "Boring Title A" in titles:
            print(f"  PASS: search=oats finds 'Boring Title A' via ingredient 'rolled oats'")
        else:
            print(f"  FAIL (VRC-1): search=oats did NOT find 'Boring Title A'")
            print(f"        Got: {titles}")
            print(f"        This requires the ingredient search JOIN fix:")
            print(f"        LEFT JOIN ingredients i ON i.recipe_id = recipes.id")
            print(f"        OR i.item LIKE ? in WHERE clause")
            failures.append("VRC-1: search by ingredient name (oats)")
    else:
        print(f"  FAIL: GET /api/recipes?search=oats returned {resp.status_code}")
        failures.append("VRC-1: search endpoint returns 200")

    print()
    print("--- Test 2: Search by ingredient 'broccoli' finds correct recipe ---")
    resp = client.get("/api/recipes?search=broccoli")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r["title"] for r in results]
        if "Boring Title B" in titles:
            print(f"  PASS: search=broccoli finds 'Boring Title B' via ingredient")
        else:
            print(f"  FAIL (VRC-1): search=broccoli did NOT find 'Boring Title B'")
            print(f"        Got: {titles}")
            failures.append("VRC-1: search by ingredient name (broccoli)")
    else:
        print(f"  FAIL: GET /api/recipes?search=broccoli returned {resp.status_code}")
        failures.append("VRC-1: search by broccoli returns 200")

    print()
    print("--- Test 3: Search does NOT return false positives ---")
    # "oats" is only in Recipe A (ingredient). Recipe B and C should NOT be returned.
    resp = client.get("/api/recipes?search=oats")
    if resp.status_code == 200:
        results = resp.json()
        false_positives = [r["title"] for r in results if r["title"] not in ["Boring Title A"]]
        # Filter out seed recipes that might legitimately have "oats" in them
        seed_oat_recipes = [t for t in false_positives if "oat" in t.lower() or "oatmeal" in t.lower()]
        real_false_positives = [t for t in false_positives if t not in seed_oat_recipes]
        if not real_false_positives:
            print(f"  PASS: No false positives for search=oats")
        else:
            print(f"  FAIL: False positives returned: {real_false_positives}")
            failures.append("VRC-1: search returns false positives")
    else:
        print(f"  SKIP: Could not test false positives (search failed)")

    print()
    print("--- Test 4: SELECT DISTINCT — recipe with multiple matching ingredients appears only once ---")
    resp = client.get("/api/recipes?search=tomato")
    if resp.status_code == 200:
        results = resp.json()
        # Recipe C has "cherry tomatoes" AND "sun-dried tomatoes" — should appear exactly once
        matching = [r for r in results if r["id"] == r3_id]
        if len(matching) == 1:
            print(f"  PASS: Recipe with 2 matching ingredients appears exactly once (SELECT DISTINCT working)")
        elif len(matching) == 0:
            print(f"  FAIL: Recipe C not found in search=tomato results (ingredient search not working)")
            failures.append("VRC-1: recipe with matching ingredient not found")
        else:
            print(f"  FAIL: Recipe C appears {len(matching)} times in results (missing SELECT DISTINCT)")
            failures.append("VRC-1: SELECT DISTINCT missing — duplicates in results")
    else:
        print(f"  FAIL: GET /api/recipes?search=tomato returned {resp.status_code}")
        failures.append("VRC-1: search=tomato returns 200")

    print()
    print("--- Test 5: Combined category + ingredient search (AND logic) ---")
    # search=broccoli in category=dinner should find Recipe B (dinner + broccoli ingredient)
    # but NOT Recipe A (breakfast + oats, not dinner)
    resp = client.get("/api/recipes?category=dinner&search=broccoli")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r["title"] for r in results]
        found_b = "Boring Title B" in titles
        found_a = "Boring Title A" in titles
        if found_b and not found_a:
            print(f"  PASS: Combined category=dinner&search=broccoli returns B only (AND logic)")
        elif found_b and found_a:
            print(f"  FAIL: AND logic broken — Recipe A (breakfast) appears in dinner+broccoli results")
            failures.append("VRC-1: combined filter AND logic (category excluded breakfast)")
        elif not found_b:
            print(f"  FAIL: Recipe B not found with category=dinner&search=broccoli: {titles}")
            failures.append("VRC-1: combined filter doesn't find matching recipe")
    else:
        print(f"  FAIL: Combined filter returned {resp.status_code}")
        failures.append("VRC-1: combined category+ingredient search returns 200")

    print()
    print("--- Test 6: Empty result for nonexistent ingredient ---")
    resp = client.get("/api/recipes?search=xyzzzy_nonexistent_ingredient")
    if resp.status_code == 200 and resp.json() == []:
        print(f"  PASS: No match for nonexistent ingredient returns []")
    elif resp.status_code == 200:
        print(f"  FAIL: Expected [], got {len(resp.json())} results")
        failures.append("VRC-1: no match returns []")
    else:
        print(f"  FAIL: Returned {resp.status_code}")
        failures.append("VRC-1: no match returns 200")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} VRC-1 test(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("Fix required in backend/routes/recipes.py list_recipes():")
    print("  1. Add: LEFT JOIN ingredients i ON i.recipe_id = recipes.id")
    print("  2. Add: OR i.item LIKE ? to WHERE clause (with same search param)")
    print("  3. Change: SELECT * to SELECT DISTINCT recipes.*")
    sys.exit(1)
else:
    print("RESULT: PASS - VRC-1 ingredient search works correctly")
    print("Value delivered: Cook can search 'chicken' and find all chicken recipes by ingredient.")
    sys.exit(0)
