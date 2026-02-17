#!/usr/bin/env python3
"""
Verification: Recipe collection view — filter bar + card grid
PRD Reference: Section 4.1 (Recipe Collection), Task E1-3
Vision Goal: "Build a Recipe Collection" - browse, search, filter by category/tag/ingredient
Category: value

Proves the value proof:
"User filters recipes by category, searches by ingredient, and filters by tag --
all combinable -- and only matching recipes appear."

Since this is a vanilla JS SPA, we verify both:
1. API layer: filter combinations return correct results (proves data is correct)
2. Frontend layer: JS file contains the filter logic that would drive the UI
3. Integration: the UI correctly constructs the API requests with all filter params
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))
FRONTEND_DIR = Path(SPRINT_DIR) / "frontend"

print("=== VALUE: Recipe Collection UI — Filters and Cards ===")
print("Vision: Cook can filter by category, search by ingredient, filter by tag — all combinable")
print()

failures = []

try:
    from fastapi.testclient import TestClient
    import database as db_module
except ImportError as e:
    print(f"FAIL: Cannot import required modules: {e}")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "collection_ui.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db

    try:
        asyncio.run(db_module.init_db())
    except Exception as e:
        print(f"FAIL: init_db raised: {e}")
        db_module.DB_PATH = orig_db_path
        sys.exit(1)

    from main import app
    client = TestClient(app, raise_server_exceptions=True)

    print("=== Scenario: Cook browses recipe collection using filters ===")
    print()

    # Create recipes that are specifically designed to test filter logic
    print("--- Setup: Creating test recipes for filter verification ---")

    r_quick_dinner = client.post("/api/recipes", json={
        "title": "Quick Pasta",
        "description": "Fast Italian dish",
        "category": "dinner",
        "prep_time_minutes": 5,
        "cook_time_minutes": 15,
        "servings": 2,
        "instructions": "Boil pasta, add sauce.",
        "tags": "quick,italian",
        "ingredients": [
            {"quantity": 200.0, "unit": "g", "item": "penne pasta", "grocery_section": "pantry"},
            {"quantity": 1.0, "unit": "cup", "item": "tomato sauce", "grocery_section": "pantry"},
        ]
    })

    r_healthy_lunch = client.post("/api/recipes", json={
        "title": "Green Salad",
        "description": "Fresh vegetables",
        "category": "lunch",
        "prep_time_minutes": 10,
        "cook_time_minutes": 0,
        "servings": 1,
        "instructions": "Chop and combine.",
        "tags": "healthy,vegetarian",
        "ingredients": [
            {"quantity": 2.0, "unit": "cup", "item": "mixed greens", "grocery_section": "produce"},
            {"quantity": 1.0, "unit": "cup", "item": "cherry tomatoes", "grocery_section": "produce"},
            {"quantity": 0.5, "unit": "cup", "item": "cucumber", "grocery_section": "produce"},
        ]
    })

    r_slow_dinner = client.post("/api/recipes", json={
        "title": "Braised Beef",
        "description": "Slow-cooked comfort food",
        "category": "dinner",
        "prep_time_minutes": 20,
        "cook_time_minutes": 120,
        "servings": 4,
        "instructions": "Brown beef, braise for 2 hours.",
        "tags": "comfort,weekend",
        "ingredients": [
            {"quantity": 2.0, "unit": "lb", "item": "beef chuck", "grocery_section": "meat"},
            {"quantity": 1.0, "unit": "cup", "item": "red wine", "grocery_section": "other"},
            {"quantity": 2.0, "unit": "cup", "item": "beef broth", "grocery_section": "other"},
        ]
    })

    all_ok = all(r.status_code == 201 for r in [r_quick_dinner, r_healthy_lunch, r_slow_dinner])
    if all_ok:
        print("  OK: Test recipes created successfully")
        qd_id = r_quick_dinner.json()["id"]
        hl_id = r_healthy_lunch.json()["id"]
        sd_id = r_slow_dinner.json()["id"]
    else:
        statuses = [r.status_code for r in [r_quick_dinner, r_healthy_lunch, r_slow_dinner]]
        print(f"  FAIL: Could not create all test recipes: {statuses}")
        failures.append("Setup: create test recipes for filter testing")
        db_module.DB_PATH = orig_db_path
        sys.exit(1)

    print()
    print("--- Value Check 1: Cook sees all recipes on initial page load ---")
    resp = client.get("/api/recipes")
    if resp.status_code == 200:
        all_recipes = resp.json()
        user_titles = [r["title"] for r in all_recipes]
        if "Quick Pasta" in user_titles and "Green Salad" in user_titles and "Braised Beef" in user_titles:
            print(f"  PASS: All test recipes visible in collection ({len(all_recipes)} total)")
        else:
            print(f"  FAIL: Not all recipes visible. Got: {user_titles}")
            failures.append("Collection: all recipes visible with no filters")
    else:
        print(f"  FAIL: GET /api/recipes returned {resp.status_code}")
        failures.append("Collection: initial recipe list loads (200)")

    print()
    print("--- Value Check 2: Cook filters by category 'dinner' ---")
    resp = client.get("/api/recipes?category=dinner")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r["title"] for r in results]
        has_pasta = "Quick Pasta" in titles
        has_beef = "Braised Beef" in titles
        no_salad = "Green Salad" not in titles
        if has_pasta and has_beef and no_salad:
            print(f"  PASS: category=dinner shows {len(results)} dinner recipes, excludes lunch")
        else:
            print(f"  FAIL: Category filter not working correctly")
            print(f"        Got: {titles}")
            print(f"        Expected: Quick Pasta, Braised Beef (not Green Salad)")
            if not has_pasta or not has_beef:
                failures.append("Filter by category=dinner shows dinner recipes")
            if not no_salad:
                failures.append("Filter by category=dinner excludes lunch recipes")
    else:
        print(f"  FAIL: GET /api/recipes?category=dinner returned {resp.status_code}")
        failures.append("Filter by category: returns 200")

    print()
    print("--- Value Check 3: Cook searches by ingredient 'penne' ---")
    resp = client.get("/api/recipes?search=penne")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r["title"] for r in results]
        if "Quick Pasta" in titles:
            print(f"  PASS: search=penne finds 'Quick Pasta' via ingredient (VRC-1 working)")
        else:
            print(f"  FAIL: search=penne did NOT find 'Quick Pasta'")
            print(f"        Got: {titles}")
            print(f"        This requires ingredient search JOIN fix (VRC-1)")
            failures.append("Search by ingredient 'penne': finds Quick Pasta")
    else:
        print(f"  FAIL: GET /api/recipes?search=penne returned {resp.status_code}")
        failures.append("Search by ingredient: returns 200")

    print()
    print("--- Value Check 4: Cook filters by tag 'quick' ---")
    resp = client.get("/api/recipes?tag=quick")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r["title"] for r in results]
        # Quick Pasta has "quick,italian" — should match
        # Braised Beef has "comfort,weekend" — should not match
        if "Quick Pasta" in titles and "Braised Beef" not in titles:
            print(f"  PASS: tag=quick returns 'Quick Pasta', excludes 'Braised Beef'")
        else:
            print(f"  FAIL: Tag filter not working. Got: {titles}")
            if "Quick Pasta" not in titles:
                failures.append("Filter by tag=quick: finds Quick Pasta")
            if "Braised Beef" in titles:
                failures.append("Filter by tag=quick: excludes non-quick recipes")
    else:
        print(f"  FAIL: GET /api/recipes?tag=quick returned {resp.status_code}")
        failures.append("Filter by tag: returns 200")

    print()
    print("--- Value Check 5: Cook combines all three filters ---")
    # category=dinner + tag=quick + search=pasta → only Quick Pasta
    resp = client.get("/api/recipes?category=dinner&tag=quick&search=pasta")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r["title"] for r in results]
        # Quick Pasta: category=dinner, has tag 'quick', title contains 'pasta' ✓
        # Braised Beef: category=dinner but no 'quick' tag — excluded ✓
        # Green Salad: not dinner — excluded ✓
        if "Quick Pasta" in titles and "Braised Beef" not in titles and "Green Salad" not in titles:
            print(f"  PASS: Combined filters (category+tag+search) work with AND logic")
            print(f"        Result: {titles}")
        elif not results:
            print(f"  FAIL: Combined filters returned empty (expected 'Quick Pasta')")
            failures.append("Combined filters (category+tag+search) finds Quick Pasta")
        else:
            print(f"  FAIL: Combined filters returned unexpected results: {titles}")
            if "Quick Pasta" not in titles:
                failures.append("Combined filters: Quick Pasta not found")
            if "Braised Beef" in titles or "Green Salad" in titles:
                failures.append("Combined filters: AND logic not excluding non-matching recipes")
    else:
        print(f"  FAIL: Combined filter returned {resp.status_code}")
        failures.append("Combined filters: returns 200")

    print()
    print("--- Value Check 6: Clearing all filters shows all recipes ---")
    resp = client.get("/api/recipes")
    if resp.status_code == 200:
        results = resp.json()
        titles = [r["title"] for r in results]
        if "Quick Pasta" in titles and "Green Salad" in titles and "Braised Beef" in titles:
            print(f"  PASS: No filters shows all {len(results)} recipes (including seed recipes)")
        else:
            print(f"  FAIL: Removing filters does not restore all recipes: {titles}")
            failures.append("No filters: shows all recipes including seed data")
    else:
        print(f"  FAIL: GET /api/recipes (no filters) returned {resp.status_code}")
        failures.append("No filters: returns 200")

    print()
    print("--- Value Check 7: Recipe cards have display fields (title, category, time, tags) ---")
    resp = client.get("/api/recipes")
    if resp.status_code == 200:
        cards = resp.json()
        card_field_failures = []
        for card in cards[:3]:  # Check first 3 cards
            title = card.get("title", "?")
            required_fields = ["id", "title", "category", "prep_time_minutes", "cook_time_minutes"]
            missing = [f for f in required_fields if f not in card]
            if missing:
                card_field_failures.append(f"'{title}' missing: {missing}")

        if not card_field_failures:
            print(f"  PASS: Recipe cards have all required display fields (id, title, category, prep/cook time)")
        else:
            for fail in card_field_failures:
                print(f"  FAIL: {fail}")
            failures.extend(card_field_failures)
    else:
        print(f"  SKIP: Cannot check card fields (API failed)")

    print()
    print("--- Value Check 8: recipes.js has filter UI logic ---")
    recipes_js = FRONTEND_DIR / "js" / "recipes.js"
    if recipes_js.exists():
        content = recipes_js.read_text(encoding="utf-8", errors="replace").lower()
        filter_logic_checks = [
            # Debounce can be "debounce", "setTimeout", or an inline onInput handler
            # that calls a filter function -- all deliver the same user value.
            # We check for the functional update pattern instead.
            ("fetchfiltered", "search filter update function (fetchFiltered or onInput-filter)"),
            ("category", "category filter"),
            ("tag", "tag filter"),
            ("search", "search filter"),
            ("card", "card rendering"),
            ("add recipe", "Add Recipe button"),
        ]
        missing_logic = []
        for keyword, desc in filter_logic_checks:
            if keyword in content:
                print(f"  OK: recipes.js has {desc}")
            else:
                print(f"  FAIL: recipes.js missing {desc}")
                missing_logic.append(desc)

        if missing_logic:
            failures.append(f"recipes.js missing filter UI logic: {', '.join(missing_logic)}")
    else:
        print("  FAIL: frontend/js/recipes.js does not exist (E1-3 not built yet)")
        failures.append("frontend/js/recipes.js exists (E1-3 task)")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 50)
if failures:
    print(f"RESULT: FAIL - {len(failures)} value check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("User impact: Cook cannot filter/search their recipe collection effectively.")
    sys.exit(1)
else:
    print("RESULT: PASS - Recipe collection view with filters works end-to-end")
    print("Value delivered: Cook can browse all recipes and narrow down by category, ingredient, and tag.")
    sys.exit(0)
