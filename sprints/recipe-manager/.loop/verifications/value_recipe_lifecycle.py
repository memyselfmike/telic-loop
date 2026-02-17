#!/usr/bin/env python3
"""
Verification: Complete recipe management lifecycle
PRD Reference: Section 5 (Epic 1 Acceptance Criteria)
Vision Goal: "Build a Recipe Collection" - full CRUD + search/filter workflow
Category: value

Proves the core value chain:
"The cook creates recipes... can edit any recipe, delete ones they don't want,
browse their full collection... filter by category, search by title or ingredient,
filter by tag. These can combine."

This simulates what a real user does with their recipe collection.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== VALUE: Complete Recipe Collection Lifecycle ===")
print("Vision: Cook manages their recipe collection — create, find, edit, delete")
print()

failures = []

try:
    from fastapi.testclient import TestClient
    import database as db_module
    from main import app
except ImportError as e:
    print(f"FAIL: Cannot import app: {e}")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "lifecycle.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db
    asyncio.run(db_module.init_db())
    client = TestClient(app)

    print("=== Scenario: Cook builds their recipe collection ===")
    print()

    print("--- Step 1: Cook creates a pasta recipe with ingredients ---")
    pasta = {
        "title": "Spaghetti Carbonara",
        "description": "Classic Italian creamy pasta",
        "category": "dinner",
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "servings": 4,
        "instructions": "1. Boil pasta. 2. Cook bacon. 3. Mix eggs and cheese. 4. Combine.",
        "tags": "italian,quick,comfort",
        "ingredients": [
            {"quantity": 400.0, "unit": "g", "item": "spaghetti", "grocery_section": "pantry"},
            {"quantity": 200.0, "unit": "g", "item": "bacon", "grocery_section": "meat"},
            {"quantity": 4.0, "unit": "whole", "item": "eggs", "grocery_section": "dairy"},
            {"quantity": 100.0, "unit": "g", "item": "parmesan", "grocery_section": "dairy"},
            {"quantity": 2.0, "unit": "whole", "item": "garlic cloves", "grocery_section": "produce"},
        ]
    }
    resp = client.post("/api/recipes", json=pasta)
    if resp.status_code == 201:
        pasta_id = resp.json()["id"]
        print(f"  PASS: Pasta recipe created (id={pasta_id})")
    else:
        print(f"  FAIL: Create pasta recipe: {resp.status_code}")
        failures.append("Create recipe returns 201")
        pasta_id = None

    print()
    print("--- Step 2: Cook adds a chicken recipe for search testing ---")
    chicken = {
        "title": "Lemon Herb Chicken",
        "description": "Baked chicken with herbs",
        "category": "dinner",
        "prep_time_minutes": 15,
        "cook_time_minutes": 45,
        "servings": 4,
        "instructions": "1. Marinate. 2. Bake at 400F for 45 min.",
        "tags": "healthy,easy",
        "ingredients": [
            {"quantity": 2.0, "unit": "lb", "item": "chicken thighs", "grocery_section": "meat"},
            {"quantity": 1.0, "unit": "whole", "item": "lemon", "grocery_section": "produce"},
            {"quantity": 2.0, "unit": "tbsp", "item": "olive oil", "grocery_section": "pantry"},
        ]
    }
    resp = client.post("/api/recipes", json=chicken)
    chicken_id = resp.json()["id"] if resp.status_code == 201 else None
    if chicken_id:
        print(f"  PASS: Chicken recipe created (id={chicken_id})")
    else:
        print(f"  FAIL: Create chicken recipe: {resp.status_code}")
        failures.append("Create second recipe")

    print()
    print("--- Step 3: Cook browses collection and sees both recipes ---")
    resp = client.get("/api/recipes")
    if resp.status_code == 200:
        recipes = resp.json()
        user_recipes = [r for r in recipes if r["category"] == "dinner"]
        user_titles = [r["title"] for r in user_recipes]
        if "Spaghetti Carbonara" in user_titles and "Lemon Herb Chicken" in user_titles:
            print(f"  PASS: Cook sees both dinner recipes: {user_titles}")
        else:
            print(f"  FAIL: Missing recipes in collection. Got: {user_titles}")
            failures.append("Collection shows created recipes")
    else:
        print(f"  FAIL: GET /api/recipes: {resp.status_code}")
        failures.append("Browse collection returns 200")

    print()
    print("--- Step 4: Cook searches 'chicken' - finds by title and ingredient ---")
    # Search by title
    resp = client.get("/api/recipes?search=chicken")
    if resp.status_code == 200:
        results = [r["title"] for r in resp.json()]
        if "Lemon Herb Chicken" in results:
            print(f"  PASS: Search 'chicken' finds recipe by title")
        else:
            print(f"  FAIL: Search 'chicken' did not find Lemon Herb Chicken: {results}")
            failures.append("Search by title finds recipe")

    # Search by ingredient (spaghetti is in pasta recipe ingredients)
    resp = client.get("/api/recipes?search=spaghetti")
    if resp.status_code == 200:
        results = [r["title"] for r in resp.json()]
        if "Spaghetti Carbonara" in results:
            print(f"  PASS: Search 'spaghetti' finds recipe by ingredient name")
        else:
            print(f"  FAIL: Search by ingredient 'spaghetti' failed: {results}")
            failures.append("Search by ingredient name finds recipe")

    print()
    print("--- Step 5: Cook filters by tag 'quick' + category 'dinner' ---")
    resp = client.get("/api/recipes?category=dinner&tag=quick")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r["title"] for r in results]
        # Carbonara is dinner+quick; Lemon Chicken is dinner+healthy (not quick)
        carbonara_found = "Spaghetti Carbonara" in titles
        lemon_excluded = "Lemon Herb Chicken" not in titles
        if carbonara_found and lemon_excluded:
            print(f"  PASS: Combined filter (dinner+quick) returns Carbonara only")
        elif carbonara_found:
            print(f"  FAIL: Tag filter not excluding non-'quick' recipes: {titles}")
            failures.append("Combined tag+category filter excludes non-matching")
        else:
            print(f"  FAIL: Combined filter not finding quick dinner: {titles}")
            failures.append("Combined tag+category filter finds matching recipe")

    print()
    print("--- Step 6: Cook views recipe detail with full ingredients ---")
    if pasta_id:
        resp = client.get(f"/api/recipes/{pasta_id}")
        if resp.status_code == 200:
            detail = resp.json()
            ings = detail.get("ingredients", [])
            has_all_fields = all(k in detail for k in ["title", "description", "category", "instructions", "tags"])
            has_ingredients = len(ings) == 5
            if has_all_fields and has_ingredients:
                print(f"  PASS: Recipe detail has all fields and 5 ingredients")
            else:
                missing = [k for k in ["title", "description", "category", "instructions", "tags"] if k not in detail]
                print(f"  FAIL: Detail missing fields: {missing}, ingredients: {len(ings)}")
                failures.append("Recipe detail has all fields and ingredients")
        else:
            print(f"  FAIL: GET /api/recipes/{pasta_id}: {resp.status_code}")
            failures.append("Recipe detail returns 200")

    print()
    print("--- Step 7: Cook edits the pasta recipe (fixes ingredient amount) ---")
    if pasta_id:
        updated = pasta.copy()
        updated["servings"] = 6  # Made it for more people
        updated["ingredients"] = [
            {"quantity": 600.0, "unit": "g", "item": "spaghetti", "grocery_section": "pantry"},
            {"quantity": 300.0, "unit": "g", "item": "bacon", "grocery_section": "meat"},
            {"quantity": 6.0, "unit": "whole", "item": "eggs", "grocery_section": "dairy"},
            {"quantity": 150.0, "unit": "g", "item": "parmesan", "grocery_section": "dairy"},
            {"quantity": 3.0, "unit": "whole", "item": "garlic cloves", "grocery_section": "produce"},
        ]
        resp = client.put(f"/api/recipes/{pasta_id}", json=updated)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("servings") == 6 and len(result.get("ingredients", [])) == 5:
                print(f"  PASS: Recipe edit updated servings and replaced ingredients")
            else:
                print(f"  FAIL: Edit result: servings={result.get('servings')}, ings={len(result.get('ingredients', []))}")
                failures.append("Edit recipe updates fields and replaces ingredients")
        else:
            print(f"  FAIL: PUT /api/recipes/{pasta_id}: {resp.status_code}")
            failures.append("Edit recipe returns 200")

    print()
    print("--- Step 8: Cook deletes a recipe they no longer want ---")
    if chicken_id:
        resp = client.delete(f"/api/recipes/{chicken_id}")
        if resp.status_code in (200, 204):
            # Verify it's gone
            resp2 = client.get(f"/api/recipes/{chicken_id}")
            if resp2.status_code == 404:
                # Verify collection no longer shows it
                resp3 = client.get("/api/recipes")
                all_titles = [r["title"] for r in resp3.json()]
                if "Lemon Herb Chicken" not in all_titles:
                    print(f"  PASS: Deleted recipe gone from collection")
                else:
                    print(f"  FAIL: Deleted recipe still in collection")
                    failures.append("Deleted recipe removed from collection")
            else:
                print(f"  FAIL: Deleted recipe returns {resp2.status_code} (expected 404)")
                failures.append("Deleted recipe returns 404")
        else:
            print(f"  FAIL: DELETE /api/recipes/{chicken_id}: {resp.status_code}")
            failures.append("Delete recipe returns 200 or 204")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} value check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("User impact: Cook cannot manage their recipe collection effectively.")
    sys.exit(1)
else:
    print("RESULT: PASS - Complete recipe collection lifecycle works end-to-end")
    print("Value delivered: Cook can build, browse, search, edit, and delete their recipe collection.")
    sys.exit(0)
