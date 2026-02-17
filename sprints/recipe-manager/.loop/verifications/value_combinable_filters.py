#!/usr/bin/env python3
"""
Verification: Combinable search and filter — Value Proof #3
PRD Reference: Section 3.1 (GET /api/recipes filter params), Section 5 (Epic 1 criteria)
Vision Goal: "Searching and filtering is essential... filter by category, search by title or
ingredient ('what can I make with chicken?'), and filter by tag. These can combine — show me
all 'dinner' recipes tagged 'quick' that use 'pasta.'"
Category: value

This is Value Proof #3 from the sprint context:
"User filters recipes by category, searches by ingredient, and filters by tag --
all combinable -- and only matching recipes appear"

Verifies that:
1. ?category= alone filters correctly
2. ?tag= alone filters correctly
3. ?search= searches title, description, AND ingredient names (VRC-1)
4. All three combined with AND logic: only recipes matching ALL three appear
5. A cook can answer "what quick dinner recipes use chicken?" with a single query
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== VALUE: Combinable Recipe Filters (Value Proof #3) ===")
print("Vision: Cook can filter by category + search by ingredient + filter by tag — all at once")
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
    test_db = Path(tmpdir) / "filters.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db
    asyncio.run(db_module.init_db())
    client = TestClient(app)

    print("=== Scenario: Cook searching 'what quick dinner recipes use pasta?' ===")
    print()

    print("--- Setup: Create a controlled set of recipes ---")
    # Recipe 1: Quick dinner with pasta → SHOULD match ?category=dinner&search=pasta&tag=quick
    quick_pasta = {
        "title": "20-Minute Penne Arrabiata",
        "description": "Spicy Italian pasta",
        "category": "dinner",
        "prep_time_minutes": 5,
        "cook_time_minutes": 15,
        "servings": 2,
        "instructions": "Boil pasta. Make sauce. Combine.",
        "tags": "quick,italian,spicy",
        "ingredients": [
            {"quantity": 300.0, "unit": "g", "item": "penne pasta", "grocery_section": "pantry"},
            {"quantity": 3.0, "unit": "whole", "item": "garlic cloves", "grocery_section": "produce"},
            {"quantity": 1.0, "unit": "cup", "item": "tomato sauce", "grocery_section": "pantry"},
        ]
    }

    # Recipe 2: Quick dinner but NO pasta → should NOT match combined search
    quick_chicken = {
        "title": "Quick Chicken Stir Fry",
        "description": "Fast Asian-inspired dinner",
        "category": "dinner",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 2,
        "instructions": "Stir fry chicken with vegetables.",
        "tags": "quick,asian",
        "ingredients": [
            {"quantity": 1.0, "unit": "lb", "item": "chicken breast", "grocery_section": "meat"},
            {"quantity": 2.0, "unit": "cup", "item": "broccoli", "grocery_section": "produce"},
        ]
    }

    # Recipe 3: Pasta but NOT quick and NOT dinner → should NOT match combined search
    slow_pasta_lunch = {
        "title": "Slow Baked Lasagna",
        "description": "Sunday lunch special",
        "category": "lunch",
        "prep_time_minutes": 30,
        "cook_time_minutes": 90,
        "servings": 6,
        "instructions": "Layer and bake.",
        "tags": "weekend,italian,comfort",
        "ingredients": [
            {"quantity": 12.0, "unit": "whole", "item": "lasagna pasta sheets", "grocery_section": "pantry"},
            {"quantity": 1.0, "unit": "lb", "item": "ground beef", "grocery_section": "meat"},
            {"quantity": 2.0, "unit": "cup", "item": "ricotta", "grocery_section": "dairy"},
        ]
    }

    # Recipe 4: Quick tag + dinner + NO pasta anywhere (neither title, description, nor ingredients)
    # This verifies the filter correctly excludes it from ?search=pasta
    no_pasta_quick_dinner = {
        "title": "Quick Veggie Stir Fry",
        "description": "Fast and healthy vegetables",
        "category": "dinner",
        "prep_time_minutes": 10,
        "cook_time_minutes": 10,
        "servings": 2,
        "instructions": "Stir fry vegetables in hot wok.",
        "tags": "quick,healthy,vegetarian",
        "ingredients": [
            {"quantity": 2.0, "unit": "whole", "item": "zucchini", "grocery_section": "produce"},
            {"quantity": 1.0, "unit": "cup", "item": "marinara sauce", "grocery_section": "pantry"},
        ]
    }

    # Recipe 5: Breakfast with pasta ingredient — not dinner, no quick tag
    breakfast_pasta = {
        "title": "Savory Oat Porridge",
        "description": "A hearty breakfast",
        "category": "breakfast",
        "prep_time_minutes": 5,
        "cook_time_minutes": 10,
        "servings": 1,
        "instructions": "Cook oats in broth.",
        "tags": "healthy,vegetarian",
        "ingredients": [
            {"quantity": 1.0, "unit": "cup", "item": "rolled oats", "grocery_section": "pantry"},
            {"quantity": 100.0, "unit": "g", "item": "pasta", "grocery_section": "pantry"},  # has pasta!
            {"quantity": 1.0, "unit": "cup", "item": "vegetable broth", "grocery_section": "pantry"},
        ]
    }

    created = {}
    for name, recipe in [
        ("quick_pasta", quick_pasta),
        ("quick_chicken", quick_chicken),
        ("slow_pasta_lunch", slow_pasta_lunch),
        ("no_pasta_quick_dinner", no_pasta_quick_dinner),
        ("breakfast_pasta", breakfast_pasta),
    ]:
        resp = client.post("/api/recipes", json=recipe)
        if resp.status_code == 201:
            created[name] = resp.json()["id"]
            print(f"  OK: '{recipe['title']}' created (id={created[name]})")
        else:
            print(f"  FAIL: Could not create '{recipe['title']}': {resp.status_code}")
            failures.append(f"Setup: create recipe {name}")

    if len(failures) > 0:
        db_module.DB_PATH = orig_db_path
        sys.exit(1)

    print()
    print("--- Value Check 1: ?category=dinner returns only dinner recipes ---")
    resp = client.get("/api/recipes?category=dinner")
    if resp.status_code == 200:
        results = resp.json()
        result_titles = {r["title"] for r in results}
        # Should include: quick_pasta, quick_chicken, no_pasta_quick_dinner
        # Should NOT include: slow_pasta_lunch (lunch), breakfast_pasta (breakfast)
        expected_in = {"20-Minute Penne Arrabiata", "Quick Chicken Stir Fry", "Quick Veggie Stir Fry"}
        expected_out = {"Slow Baked Lasagna", "Savory Oat Porridge"}

        false_positives = expected_out.intersection(result_titles)
        missing = expected_in - result_titles

        if not false_positives and not missing:
            print(f"  PASS: ?category=dinner returns exactly the 3 dinner recipes")
        else:
            if false_positives:
                print(f"  FAIL: Non-dinner recipes appeared: {false_positives}")
                failures.append("?category=dinner excludes non-dinner recipes")
            if missing:
                print(f"  FAIL: Dinner recipes missing: {missing}")
                failures.append("?category=dinner includes all dinner recipes")
    else:
        print(f"  FAIL: GET /api/recipes?category=dinner returned {resp.status_code}")
        failures.append("?category=dinner returns 200")

    print()
    print("--- Value Check 2: ?tag=quick returns only quick-tagged recipes ---")
    resp = client.get("/api/recipes?tag=quick")
    if resp.status_code == 200:
        results = resp.json()
        result_titles = {r["title"] for r in results}
        # Recipes tagged "quick": quick_pasta, quick_chicken, no_pasta_quick_dinner
        # NOT tagged quick: slow_pasta_lunch, breakfast_pasta
        expected_in = {"20-Minute Penne Arrabiata", "Quick Chicken Stir Fry", "Quick Veggie Stir Fry"}
        expected_out = {"Slow Baked Lasagna", "Savory Oat Porridge"}

        false_positives = expected_out.intersection(result_titles)
        missing = expected_in - result_titles

        if not false_positives and not missing:
            print(f"  PASS: ?tag=quick returns all quick-tagged recipes only")
        else:
            if false_positives:
                print(f"  FAIL: Non-quick recipes appeared: {false_positives}")
                failures.append("?tag=quick excludes non-quick recipes")
            if missing:
                print(f"  FAIL: Quick recipes missing: {missing}")
                failures.append("?tag=quick includes all quick recipes")
    else:
        print(f"  FAIL: GET /api/recipes?tag=quick returned {resp.status_code}")
        failures.append("?tag=quick returns 200")

    print()
    print("--- Value Check 3: ?search=pasta searches ingredient items (VRC-1 requirement) ---")
    print("  (Requires VRC-1 fix: LEFT JOIN ingredients + SELECT DISTINCT)")
    resp = client.get("/api/recipes?search=pasta")
    if resp.status_code == 200:
        results = resp.json()
        result_titles = {r["title"] for r in results}
        # With VRC-1 fix, search hits ingredient items:
        # - "20-Minute Penne Arrabiata": has ingredient "penne pasta" → found via ingredient
        # - "Slow Baked Lasagna": has ingredient "lasagna pasta sheets" → found via ingredient
        # - "Savory Oat Porridge": has ingredient "pasta" → found via ingredient
        # Should NOT include: "Quick Chicken Stir Fry", "Quick Veggie Stir Fry" (no pasta anywhere)
        expected_in = {"20-Minute Penne Arrabiata", "Slow Baked Lasagna", "Savory Oat Porridge"}
        expected_out = {"Quick Chicken Stir Fry", "Quick Veggie Stir Fry"}

        false_positives = expected_out.intersection(result_titles)
        missing = expected_in - result_titles

        if not false_positives and not missing:
            print(f"  PASS: ?search=pasta finds all recipes with 'pasta' in title OR ingredient items")
        else:
            if false_positives:
                print(f"  FAIL: Recipes without pasta appeared: {false_positives}")
                failures.append("?search=pasta excludes non-pasta recipes")
            if missing:
                print(f"  FAIL: Pasta recipes not found by ingredient search: {missing}")
                print(f"        (VRC-1 fix needed: ingredient search JOIN not implemented)")
                failures.append("?search=pasta finds pasta recipes via ingredient (requires VRC-1)")
    else:
        print(f"  FAIL: GET /api/recipes?search=pasta returned {resp.status_code}")
        failures.append("?search=pasta returns 200")

    print()
    print("--- Value Check 4: COMBINED — ?category=dinner&search=pasta&tag=quick (AND logic) ---")
    print("  (Vision: 'show me all dinner recipes tagged quick that use pasta')")
    print("  (Requires VRC-1 fix for ingredient search to work correctly)")
    resp = client.get("/api/recipes?category=dinner&search=pasta&tag=quick")
    if resp.status_code == 200:
        results = resp.json()
        result_titles = {r["title"] for r in results}

        # With VRC-1 fix: ONLY "20-Minute Penne Arrabiata" matches ALL THREE:
        # - category=dinner ✓
        # - search=pasta (via ingredient "penne pasta") ✓
        # - tag=quick ✓
        expected_match = "20-Minute Penne Arrabiata"
        expected_excluded = {
            "Quick Chicken Stir Fry",    # no pasta anywhere
            "Slow Baked Lasagna",        # lunch, not quick
            "Quick Veggie Stir Fry",     # no pasta anywhere
            "Savory Oat Porridge",       # breakfast, no quick tag
        }

        found_correct = expected_match in result_titles
        false_positives = expected_excluded.intersection(result_titles)

        if found_correct and not false_positives:
            print(f"  PASS: Combined filters return exactly '{expected_match}'")
            print(f"        AND logic: dinner + pasta ingredient + quick tag all required")
        elif not found_correct and not false_positives:
            # This means VRC-1 is not implemented — combined returns [] because pasta search fails
            print(f"  FAIL: Combined filters returned no results (VRC-1 ingredient search not implemented)")
            print(f"        Once VRC-1 is fixed, '{expected_match}' should appear here")
            failures.append("COMBINED: VRC-1 required for pasta ingredient search in combined filter")
        elif found_correct and false_positives:
            print(f"  FAIL: AND logic broken — unexpected recipes appeared: {false_positives}")
            failures.append("COMBINED: AND logic excludes non-matching recipes")
        else:
            print(f"  FAIL: Expected '{expected_match}', got: {result_titles}")
            failures.append("COMBINED: correct recipe found with all three filters")
    else:
        print(f"  FAIL: GET /api/recipes?category=dinner&search=pasta&tag=quick returned {resp.status_code}")
        failures.append("COMBINED filters return 200")

    print()
    print("--- Value Check 5: Empty result when no recipe matches all three filters ---")
    # "vegetarian breakfast with chicken" — no recipe should match
    resp = client.get("/api/recipes?category=breakfast&search=chicken&tag=vegetarian")
    if resp.status_code == 200:
        results = resp.json()
        if results == []:
            print(f"  PASS: No-match combined filter returns [] (AND logic correct)")
        else:
            print(f"  FAIL: Expected [], got {len(results)} results: {[r.get('title') for r in results]}")
            failures.append("Combined no-match filter returns []")
    else:
        print(f"  FAIL: Combined no-match filter returned {resp.status_code}")
        failures.append("Combined no-match filter returns 200")

    print()
    print("--- Value Check 6: Single filter doesn't accidentally require others ---")
    # Just ?search=chicken should find quick_chicken regardless of category/tag
    resp = client.get("/api/recipes?search=chicken")
    if resp.status_code == 200:
        results = resp.json()
        result_titles = {r["title"] for r in results}
        # Should find "Quick Chicken Stir Fry" via title AND via ingredient "chicken breast"
        if "Quick Chicken Stir Fry" in result_titles:
            print(f"  PASS: ?search=chicken alone finds 'Quick Chicken Stir Fry'")
        else:
            print(f"  FAIL: ?search=chicken alone did not find 'Quick Chicken Stir Fry'. Got: {result_titles}")
            failures.append("?search=chicken standalone finds chicken recipe")
    else:
        print(f"  FAIL: GET /api/recipes?search=chicken returned {resp.status_code}")
        failures.append("?search=chicken returns 200")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} value check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("User impact: Cook cannot find recipes by ingredient name or combine filters —")
    print("the core 'what can I make with chicken?' search does not work.")
    print()
    print("Fix required:")
    print("  1. VRC-1: Add ingredient JOIN to GET /api/recipes?search= in routes/recipes.py")
    print("     LEFT JOIN ingredients i ON i.recipe_id = recipes.id")
    print("     OR i.item LIKE ? in WHERE clause, SELECT DISTINCT recipes.*")
    sys.exit(1)
else:
    print("RESULT: PASS - All combinable filter checks pass")
    print("Value delivered: Cook can ask 'what quick dinner recipes use pasta?' and get")
    print("the exact answer — category + ingredient search + tag all work together.")
    sys.exit(0)
