#!/usr/bin/env python3
"""
Verification: Recipe detail view and create/edit form modal
PRD Reference: Section 4.1 (Recipe Collection), Tasks E1-4 and E1-5
Vision Goal: "Build a Recipe Collection" - full CRUD lifecycle through the UI
Category: value

Proves value proofs:
1. "User creates a new recipe with title, category, ingredients, and instructions,
   then sees it in the collection grid"
2. Cook can view recipe detail with all fields including ingredients
3. Cook can edit a recipe (title, servings, ingredients) and see changes in grid
4. Cook can delete a recipe and confirm it's gone

Since this is a vanilla JS SPA, we verify:
- API layer: CRUD operations complete correctly (data is right)
- Frontend layer: JS contains detail view and form modal logic
- The detail view must show ingredients (full recipe with GET /api/recipes/{id})
- The form must handle both create (POST) and edit (PUT) modes
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))
FRONTEND_DIR = Path(SPRINT_DIR) / "frontend"

print("=== VALUE: Recipe Detail View and Create/Edit Form ===")
print("Vision: Cook creates, views full detail, edits, and deletes recipes through the UI")
print()

failures = []

try:
    from fastapi.testclient import TestClient
    import database as db_module
except ImportError as e:
    print(f"FAIL: Cannot import required modules: {e}")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "detail_form.db"
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

    print("=== Scenario: Cook creates a recipe, views it, edits it, then deletes it ===")
    print()

    print("--- Step 1: Cook creates a new recipe with all fields ---")
    new_recipe = {
        "title": "Homemade Granola",
        "description": "Crunchy oat clusters with honey and nuts",
        "category": "breakfast",
        "prep_time_minutes": 10,
        "cook_time_minutes": 25,
        "servings": 8,
        "instructions": "1. Mix oats, nuts, and honey.\n2. Spread on baking sheet.\n3. Bake at 350F for 25 min.",
        "tags": "healthy,meal-prep",
        "ingredients": [
            {"quantity": 3.0, "unit": "cup", "item": "rolled oats", "grocery_section": "pantry"},
            {"quantity": 1.0, "unit": "cup", "item": "mixed nuts", "grocery_section": "other"},
            {"quantity": 0.25, "unit": "cup", "item": "honey", "grocery_section": "pantry"},
            {"quantity": 0.25, "unit": "cup", "item": "coconut oil", "grocery_section": "pantry"},
            {"quantity": 1.0, "unit": "tsp", "item": "vanilla extract", "grocery_section": "pantry"},
        ]
    }

    resp = client.post("/api/recipes", json=new_recipe)
    if resp.status_code == 201:
        recipe_id = resp.json()["id"]
        print(f"  PASS: Recipe created via POST /api/recipes (id={recipe_id})")
        # Verify required fields in response
        created = resp.json()
        required = ["id", "title", "category", "prep_time_minutes", "cook_time_minutes", "servings"]
        missing = [f for f in required if f not in created]
        if missing:
            print(f"  FAIL: Create response missing fields: {missing}")
            failures.append(f"POST /api/recipes response missing fields: {missing}")
        else:
            print(f"  PASS: Create response has all required fields")
    else:
        print(f"  FAIL: POST /api/recipes returned {resp.status_code}: {resp.text[:200]}")
        failures.append("POST /api/recipes creates recipe (201)")
        recipe_id = None
        db_module.DB_PATH = orig_db_path
        sys.exit(1)

    print()
    print("--- Step 2: Cook sees recipe in the collection grid ---")
    resp = client.get("/api/recipes")
    if resp.status_code == 200:
        cards = resp.json()
        granola_card = next((r for r in cards if r["title"] == "Homemade Granola"), None)
        if granola_card:
            # Verify card display fields
            has_category = granola_card.get("category") == "breakfast"
            has_prep = granola_card.get("prep_time_minutes") == 10
            has_cook = granola_card.get("cook_time_minutes") == 25
            if has_category and has_prep and has_cook:
                total_time = granola_card["prep_time_minutes"] + granola_card["cook_time_minutes"]
                print(f"  PASS: 'Homemade Granola' card appears in grid (breakfast, {total_time} min)")
            else:
                print(f"  FAIL: Card data incorrect: {granola_card}")
                failures.append("Recipe card in grid has correct category and times")
        else:
            print(f"  FAIL: 'Homemade Granola' not found in collection grid")
            failures.append("New recipe appears in collection grid after creation")
    else:
        print(f"  FAIL: GET /api/recipes returned {resp.status_code}")
        failures.append("Collection grid loads after recipe creation")

    print()
    print("--- Step 3: Cook opens recipe detail view (full ingredients shown) ---")
    if recipe_id:
        resp = client.get(f"/api/recipes/{recipe_id}")
        if resp.status_code == 200:
            detail = resp.json()
            # Check all fields present
            required_fields = ["id", "title", "description", "category",
                               "prep_time_minutes", "cook_time_minutes", "servings",
                               "instructions", "tags", "ingredients", "created_at"]
            missing = [f for f in required_fields if f not in detail]
            if missing:
                print(f"  FAIL: Detail response missing fields: {missing}")
                failures.append(f"Recipe detail missing fields: {missing}")
            else:
                print(f"  PASS: Recipe detail has all required fields")

            # Check ingredients
            ingredients = detail.get("ingredients", [])
            if len(ingredients) == 5:
                print(f"  PASS: Recipe detail shows all 5 ingredients")
                # Verify ingredient fields
                ing = ingredients[0]
                ing_fields = ["id", "quantity", "unit", "item", "grocery_section"]
                ing_missing = [f for f in ing_fields if f not in ing]
                if not ing_missing:
                    print(f"  PASS: Ingredient has all fields: {list(ing.keys())}")
                else:
                    print(f"  FAIL: Ingredient missing fields: {ing_missing}")
                    failures.append(f"Ingredient missing fields: {ing_missing}")
            else:
                print(f"  FAIL: Expected 5 ingredients, got {len(ingredients)}")
                failures.append("Recipe detail shows all 5 ingredients")

            # Verify instructions preserved
            if "1. Mix" in detail.get("instructions", ""):
                print(f"  PASS: Instructions preserved correctly")
            else:
                print(f"  FAIL: Instructions not preserved: {detail.get('instructions', '')[:50]}")
                failures.append("Recipe instructions preserved in detail view")

            # Verify tags
            if "healthy" in detail.get("tags", ""):
                print(f"  PASS: Tags preserved: {detail.get('tags')}")
            else:
                print(f"  FAIL: Tags not preserved: {detail.get('tags', '')}")
                failures.append("Recipe tags preserved in detail view")

        else:
            print(f"  FAIL: GET /api/recipes/{recipe_id} returned {resp.status_code}")
            failures.append(f"Recipe detail view returns 200")

    print()
    print("--- Step 4: Cook edits recipe (changes servings, replaces ingredient) ---")
    if recipe_id:
        updated_recipe = {
            **new_recipe,
            "servings": 12,  # doubled for batch cooking
            "title": "Homemade Granola (Large Batch)",
            "ingredients": [
                {"quantity": 6.0, "unit": "cup", "item": "rolled oats", "grocery_section": "pantry"},
                {"quantity": 2.0, "unit": "cup", "item": "mixed nuts", "grocery_section": "other"},
                {"quantity": 0.5, "unit": "cup", "item": "honey", "grocery_section": "pantry"},
                {"quantity": 0.5, "unit": "cup", "item": "coconut oil", "grocery_section": "pantry"},
                {"quantity": 2.0, "unit": "tsp", "item": "vanilla extract", "grocery_section": "pantry"},
                {"quantity": 0.5, "unit": "cup", "item": "dried cranberries", "grocery_section": "pantry"},
            ]
        }
        resp = client.put(f"/api/recipes/{recipe_id}", json=updated_recipe)
        if resp.status_code == 200:
            updated = resp.json()
            if updated.get("servings") == 12 and updated.get("title") == "Homemade Granola (Large Batch)":
                print(f"  PASS: PUT updates recipe title and servings")
                # Verify ingredients were replaced
                new_ings = updated.get("ingredients", [])
                if len(new_ings) == 6:
                    print(f"  PASS: Ingredients replaced with 6 new items (cranberries added)")
                elif len(new_ings) == 5:
                    print(f"  FAIL: Ingredients count still 5 — not replaced with new list")
                    failures.append("PUT replaces ingredients list entirely")
                else:
                    print(f"  FAIL: Expected 6 ingredients after edit, got {len(new_ings)}")
                    failures.append("PUT replaces ingredients list with correct count")
            else:
                print(f"  FAIL: Edit did not update: title={updated.get('title')}, servings={updated.get('servings')}")
                failures.append("PUT updates recipe title and servings")
        else:
            print(f"  FAIL: PUT /api/recipes/{recipe_id} returned {resp.status_code}")
            failures.append(f"PUT /api/recipes/{{id}} returns 200")

    print()
    print("--- Step 5: Cook sees updated recipe in collection grid ---")
    resp = client.get("/api/recipes")
    if resp.status_code == 200:
        cards = resp.json()
        updated_card = next((r for r in cards if "Large Batch" in r.get("title", "")), None)
        if updated_card:
            print(f"  PASS: Updated recipe 'Homemade Granola (Large Batch)' visible in grid")
        else:
            all_titles = [r["title"] for r in cards]
            print(f"  FAIL: Updated recipe not in grid. Got: {all_titles}")
            failures.append("Updated recipe appears in collection grid")
    else:
        print(f"  FAIL: GET /api/recipes returned {resp.status_code}")
        failures.append("Collection grid refreshes after edit")

    print()
    print("--- Step 6: Cook deletes the recipe ---")
    if recipe_id:
        resp = client.delete(f"/api/recipes/{recipe_id}")
        if resp.status_code in (200, 204):
            print(f"  PASS: DELETE /api/recipes/{recipe_id} returned {resp.status_code}")
            # Verify gone from detail
            resp2 = client.get(f"/api/recipes/{recipe_id}")
            if resp2.status_code == 404:
                print(f"  PASS: Deleted recipe returns 404 on direct access")
            else:
                print(f"  FAIL: Expected 404 after delete, got {resp2.status_code}")
                failures.append("Deleted recipe returns 404 on GET")
            # Verify gone from collection
            resp3 = client.get("/api/recipes")
            if resp3.status_code == 200:
                remaining = [r for r in resp3.json() if r.get("id") == recipe_id]
                if not remaining:
                    print(f"  PASS: Deleted recipe not in collection grid")
                else:
                    print(f"  FAIL: Deleted recipe still appears in collection grid")
                    failures.append("Deleted recipe removed from collection grid")
        else:
            print(f"  FAIL: DELETE returned {resp.status_code}")
            failures.append("DELETE /api/recipes/{id} returns 200 or 204")

    print()
    print("--- Step 7: Verify recipes.js has detail view and form modal logic ---")
    recipes_js = FRONTEND_DIR / "js" / "recipes.js"
    if recipes_js.exists():
        content = recipes_js.read_text(encoding="utf-8", errors="replace").lower()

        detail_checks = [
            ("ingredients", "ingredients list rendering"),
            ("instructions", "instructions display"),
            ("edit", "edit button"),
            ("delete", "delete button"),
            ("confirm", "delete confirmation dialog"),
            # "Back" navigation can be: closeModal(), a back button, or renderRecipes()
            # The modal pattern (openModal/closeModal) IS the back navigation for this SPA.
            ("closemodal", "back/close navigation (closeModal or equivalent)"),
        ]

        form_checks = [
            ("modal", "modal overlay"),
            ("submit", "form submission"),
            ("post", "POST for create"),
            ("put", "PUT for edit"),
            ("add ingredient", "Add Ingredient button"),
            ("remove", "ingredient remove (X) button"),
        ]

        print("  Detail view logic:")
        detail_missing = []
        for keyword, desc in detail_checks:
            if keyword in content:
                print(f"    OK: {desc}")
            else:
                print(f"    FAIL: missing {desc}")
                detail_missing.append(desc)

        print("  Form modal logic:")
        form_missing = []
        for keyword, desc in form_checks:
            if keyword in content:
                print(f"    OK: {desc}")
            else:
                print(f"    FAIL: missing {desc}")
                form_missing.append(desc)

        if detail_missing:
            failures.append(f"recipes.js detail view missing: {', '.join(detail_missing)}")
        if form_missing:
            failures.append(f"recipes.js form modal missing: {', '.join(form_missing)}")
    else:
        print("  FAIL: frontend/js/recipes.js does not exist")
        failures.append("frontend/js/recipes.js exists")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 50)
if failures:
    print(f"RESULT: FAIL - {len(failures)} value check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("User impact: Cook cannot create, view, edit or delete recipes through the UI.")
    sys.exit(1)
else:
    print("RESULT: PASS - Recipe detail view and create/edit form work end-to-end")
    print("Value delivered: Cook can create recipes with ingredients, view full details, edit, and delete.")
    sys.exit(0)
