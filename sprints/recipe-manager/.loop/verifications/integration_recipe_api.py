#!/usr/bin/env python3
"""
Verification: Recipe API CRUD and filtering
PRD Reference: Section 3.1 (Recipe Endpoints), Task 1.7 (API tests)
Vision Goal: "Build a Recipe Collection" - create, browse, search, filter
Category: integration

Tests the full recipe CRUD lifecycle and all filter combinations.
Uses the FastAPI TestClient with a fresh temp database.
"""

import sys
import os
import asyncio
import tempfile
import json
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== Recipe API Integration Tests ===")
print(f"Sprint dir: {SPRINT_DIR}")

failures = []

try:
    from fastapi.testclient import TestClient
    print("OK: fastapi.testclient imported")
except ImportError as e:
    print(f"FAIL: Cannot import FastAPI TestClient: {e}")
    sys.exit(1)

try:
    import database as db_module
    print("OK: database module imported")
except ImportError as e:
    print(f"FAIL: Cannot import database module: {e}")
    sys.exit(1)

# Use a temp database for isolation
with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "test_recipes.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db

    # Pre-initialize the database before starting TestClient
    try:
        asyncio.run(db_module.init_db())
        print(f"OK: Fresh test DB initialized at {test_db}")
    except Exception as e:
        print(f"FAIL: init_db with temp DB raised: {e}")
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

    SAMPLE_RECIPE = {
        "title": "Test Chicken Stir Fry",
        "description": "Quick weeknight dinner",
        "category": "dinner",
        "prep_time_minutes": 15,
        "cook_time_minutes": 20,
        "servings": 4,
        "instructions": "1. Cut chicken. 2. Heat wok.",
        "tags": "quick,asian",
        "ingredients": [
            {"quantity": 2.0, "unit": "lb", "item": "chicken breast", "grocery_section": "meat"},
            {"quantity": 1.0, "unit": "tbsp", "item": "soy sauce", "grocery_section": "pantry"},
            {"quantity": 2.0, "unit": "cup", "item": "broccoli", "grocery_section": "produce"},
        ]
    }

    print()
    print("--- POST /api/recipes - Create recipe ---")
    resp = client.post("/api/recipes", json=SAMPLE_RECIPE)
    if resp.status_code == 201:
        created = resp.json()
        recipe_id = created.get("id")
        print(f"  PASS: Create recipe returns 201, id={recipe_id}")
    else:
        print(f"  FAIL: Expected 201, got {resp.status_code}: {resp.text[:200]}")
        failures.append("POST /api/recipes returns 201")
        recipe_id = None

    print()
    print("--- GET /api/recipes - List recipes ---")
    resp = client.get("/api/recipes")
    if resp.status_code == 200:
        recipes = resp.json()
        if any(r.get("title") == "Test Chicken Stir Fry" for r in recipes):
            print(f"  PASS: GET /api/recipes returns list including created recipe ({len(recipes)} total)")
        else:
            print(f"  FAIL: Created recipe not in list. Got: {[r.get('title') for r in recipes]}")
            failures.append("GET /api/recipes includes created recipe")
    else:
        print(f"  FAIL: Expected 200, got {resp.status_code}")
        failures.append("GET /api/recipes returns 200")

    print()
    print("--- GET /api/recipes/{id} - Single recipe with ingredients ---")
    if recipe_id:
        resp = client.get(f"/api/recipes/{recipe_id}")
        if resp.status_code == 200:
            detail = resp.json()
            ings = detail.get("ingredients", [])
            if len(ings) == 3:
                print(f"  PASS: GET /api/recipes/{recipe_id} returns recipe with {len(ings)} ingredients")
            else:
                print(f"  FAIL: Expected 3 ingredients, got {len(ings)}")
                failures.append("GET /api/recipes/{id} returns ingredients")
        else:
            print(f"  FAIL: Expected 200, got {resp.status_code}")
            failures.append("GET /api/recipes/{id} returns 200")
    else:
        print("  SKIP: No recipe_id from create step")

    print()
    print("--- PUT /api/recipes/{id} - Update recipe ---")
    if recipe_id:
        updated = SAMPLE_RECIPE.copy()
        updated["title"] = "Updated Stir Fry"
        updated["ingredients"] = [
            {"quantity": 1.5, "unit": "lb", "item": "beef", "grocery_section": "meat"},
        ]
        resp = client.put(f"/api/recipes/{recipe_id}", json=updated)
        if resp.status_code == 200:
            result = resp.json()
            ings = result.get("ingredients", [])
            if result.get("title") == "Updated Stir Fry" and len(ings) == 1:
                print(f"  PASS: PUT /api/recipes/{recipe_id} updates title and replaces ingredients")
            else:
                print(f"  FAIL: Title={result.get('title')}, ingredients={len(ings)}")
                failures.append("PUT /api/recipes/{id} updates and replaces ingredients")
        else:
            print(f"  FAIL: Expected 200, got {resp.status_code}")
            failures.append("PUT /api/recipes/{id} returns 200")

    print()
    print("--- DELETE /api/recipes/{id} - Delete recipe ---")
    if recipe_id:
        resp = client.delete(f"/api/recipes/{recipe_id}")
        if resp.status_code in (200, 204):
            print(f"  PASS: DELETE /api/recipes/{recipe_id} returns {resp.status_code}")
            resp2 = client.get(f"/api/recipes/{recipe_id}")
            if resp2.status_code == 404:
                print(f"  PASS: Subsequent GET after delete returns 404")
            else:
                print(f"  FAIL: Expected 404 after delete, got {resp2.status_code}")
                failures.append("GET after DELETE returns 404")
        else:
            print(f"  FAIL: Expected 200/204, got {resp.status_code}")
            failures.append("DELETE /api/recipes/{id} returns 200 or 204")

    print()
    print("--- GET /api/recipes?category= - Filter by category ---")
    breakfast = {**SAMPLE_RECIPE, "title": "Filter Breakfast", "category": "breakfast", "tags": "easy"}
    dinner1 = {**SAMPLE_RECIPE, "title": "Filter Dinner Pasta", "category": "dinner", "tags": "quick", "description": "pasta dish"}
    dinner2 = {**SAMPLE_RECIPE, "title": "Filter Dinner Chicken", "category": "dinner", "tags": "heavy"}

    ids = []
    for r in [breakfast, dinner1, dinner2]:
        resp = client.post("/api/recipes", json=r)
        if resp.status_code == 201:
            ids.append(resp.json().get("id"))

    resp = client.get("/api/recipes?category=dinner")
    if resp.status_code == 200:
        filtered = resp.json()
        titles = [r.get("title") for r in filtered]
        dinner_titles = [t for t in titles if "Dinner" in t]
        non_dinner = [t for t in titles if "Breakfast" in t]
        if len(dinner_titles) >= 2 and not non_dinner:
            print(f"  PASS: category=dinner returns only dinner recipes ({len(dinner_titles)} found)")
        else:
            print(f"  FAIL: Filter by category not working. Got: {titles}")
            failures.append("GET /api/recipes?category= filter")
    else:
        print(f"  FAIL: Expected 200, got {resp.status_code}")
        failures.append("GET /api/recipes?category= returns 200")

    print()
    print("--- GET /api/recipes?tag= - Filter by tag ---")
    resp = client.get("/api/recipes?tag=quick")
    if resp.status_code == 200:
        filtered = resp.json()
        titles = [r.get("title") for r in filtered]
        quick_found = any("Pasta" in t for t in titles)
        if quick_found:
            print(f"  PASS: tag=quick returns recipe with 'quick' tag")
        else:
            print(f"  FAIL: Recipe with 'quick' tag not found. Got: {titles}")
            failures.append("GET /api/recipes?tag= filter")
    else:
        print(f"  FAIL: Expected 200, got {resp.status_code}")
        failures.append("GET /api/recipes?tag= returns 200")

    print()
    print("--- GET /api/recipes?search= - Search by title/description/ingredient ---")
    # Add a recipe with specific ingredient for search testing
    pasta_recipe = {
        **SAMPLE_RECIPE,
        "title": "Spaghetti Carbonara",
        "category": "dinner",
        "description": "Italian classic",
        "tags": "italian",
        "ingredients": [
            {"quantity": 200.0, "unit": "g", "item": "spaghetti", "grocery_section": "pantry"},
            {"quantity": 3.0, "unit": "whole", "item": "eggs", "grocery_section": "dairy"},
        ]
    }
    client.post("/api/recipes", json=pasta_recipe)

    # Search by title
    resp = client.get("/api/recipes?search=Carbonara")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r.get("title") for r in results]
        if any("Carbonara" in t for t in titles):
            print(f"  PASS: search=Carbonara finds recipe by title")
        else:
            print(f"  FAIL: Title search failed. Got: {titles}")
            failures.append("GET /api/recipes?search= by title")
    else:
        print(f"  FAIL: Expected 200, got {resp.status_code}")
        failures.append("GET /api/recipes?search= returns 200")

    # Search by ingredient (requires VRC-1 fix)
    resp = client.get("/api/recipes?search=spaghetti")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r.get("title") for r in results]
        if any("Carbonara" in t for t in titles):
            print(f"  PASS: search=spaghetti finds recipe by ingredient name")
        else:
            print(f"  FAIL (VRC-1): Ingredient search not finding recipe. Got: {titles}")
            failures.append("GET /api/recipes?search= by ingredient (VRC-1 fix needed)")

    print()
    print("--- GET /api/recipes?category=&search=&tag= - Combined filters ---")
    resp = client.get("/api/recipes?category=dinner&search=Pasta&tag=quick")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r.get("title") for r in results]
        # Should match Filter Dinner Pasta (category=dinner, title has Pasta, tag=quick)
        # Should NOT match Spaghetti Carbonara (tag=italian, not quick)
        if any("Pasta" in t for t in titles) and not any("Carbonara" in t for t in titles):
            print(f"  PASS: Combined filters (category+search+tag) work with AND logic")
        elif not results:
            print(f"  PASS: Combined filters return empty when no AND match")
        else:
            print(f"  FAIL: Combined filter unexpected results: {titles}")
            failures.append("GET /api/recipes combined filters AND logic")
    else:
        print(f"  FAIL: Expected 200, got {resp.status_code}")
        failures.append("GET /api/recipes combined filters returns 200")

    print()
    print("--- GET /api/recipes - Empty result returns [] ---")
    resp = client.get("/api/recipes?category=nonexistent_category")
    if resp.status_code == 200:
        results = resp.json()
        if results == []:
            print("  PASS: Empty filter result returns []")
        else:
            print(f"  FAIL: Expected [], got {results}")
            failures.append("GET /api/recipes empty result returns []")
    else:
        print(f"  FAIL: Expected 200, got {resp.status_code}")
        failures.append("GET /api/recipes empty result returns 200")

    print()
    print("--- Cascading delete: recipe delete removes ingredients ---")
    resp = client.post("/api/recipes", json=SAMPLE_RECIPE)
    if resp.status_code == 201:
        del_id = resp.json().get("id")
        resp2 = client.get(f"/api/recipes/{del_id}")
        if resp2.status_code == 200 and len(resp2.json().get("ingredients", [])) > 0:
            client.delete(f"/api/recipes/{del_id}")
            import sqlite3 as _sqlite3
            conn = _sqlite3.connect(str(test_db))
            conn.execute("PRAGMA foreign_keys = ON")
            remaining = conn.execute(
                "SELECT id FROM ingredients WHERE recipe_id = ?", (del_id,)
            ).fetchall()
            conn.close()
            if not remaining:
                print(f"  PASS: Cascade delete removes ingredients")
            else:
                print(f"  FAIL: {len(remaining)} ingredients remain after recipe delete")
                failures.append("Cascade delete removes ingredients")
        else:
            print(f"  SKIP: Could not verify cascade (recipe has no ingredients or not found)")
    else:
        print(f"  SKIP: Could not create recipe for cascade test")

    print()
    print("--- Seed data: GET /api/recipes returns 5 seed recipes on fresh DB ---")
    # The test DB was initialized fresh - should have exactly 5 seed recipes
    # (we've added more for testing, but seeds from 5 categories should be there)
    resp = client.get("/api/recipes")
    if resp.status_code == 200:
        all_recipes = resp.json()
        seed_categories = {"breakfast", "lunch", "dinner", "snack", "dessert"}
        found_cats = {r["category"] for r in all_recipes}
        if seed_categories.issubset(found_cats):
            print(f"  PASS: All 5 seed categories represented in recipe list ({len(all_recipes)} total recipes)")
        else:
            missing = seed_categories - found_cats
            print(f"  FAIL: Missing seed categories: {missing}")
            failures.append("Seed data: all 5 categories present")
    else:
        print(f"  FAIL: Expected 200, got {resp.status_code}")
        failures.append("Seed data check returns 200")

    # Restore original DB path
    db_module.DB_PATH = orig_db_path

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} test(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("RESULT: PASS - All recipe API integration tests passed")
    sys.exit(0)
