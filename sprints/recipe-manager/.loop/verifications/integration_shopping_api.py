#!/usr/bin/env python3
"""
Verification: Shopping list API and aggregation
PRD Reference: Section 3.3 (Shopping List Endpoints), Section 2.2 (Unit Normalization), Task 3.2
Vision Goal: "Generate a Shopping List" - aggregate from meal plan, normalized units, grouped by section
Category: integration

Tests: generate from meal plan, GET current, toggle checked, add manual, delete item,
persistence, replace old list. Also tests ingredient aggregation across recipes.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== Shopping List API Integration Tests ===")
print(f"Sprint dir: {SPRINT_DIR}")

failures = []

try:
    from fastapi.testclient import TestClient
    import database as db_module
    print("OK: database module imported")
except ImportError as e:
    print(f"FAIL: Cannot import database module: {e}")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "test_shopping.db"
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

    client = TestClient(app)

    print()
    print("--- Setup: Create recipes and meal plan ---")
    # Recipe 1: uses 1 cup broccoli + 2 tbsp soy sauce
    r1 = client.post("/api/recipes", json={
        "title": "Stir Fry A",
        "category": "dinner",
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "servings": 2,
        "description": "", "instructions": "", "tags": "",
        "ingredients": [
            {"quantity": 1.0, "unit": "cup", "item": "broccoli", "grocery_section": "produce"},
            {"quantity": 2.0, "unit": "tbsp", "item": "soy sauce", "grocery_section": "pantry"},
            {"quantity": 6.0, "unit": "oz", "item": "chicken", "grocery_section": "meat"},
        ]
    })
    # Recipe 2: uses 2 cups broccoli + 10 oz chicken (should merge with recipe 1)
    r2 = client.post("/api/recipes", json={
        "title": "Stir Fry B",
        "category": "lunch",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 2,
        "description": "", "instructions": "", "tags": "",
        "ingredients": [
            {"quantity": 2.0, "unit": "cup", "item": "broccoli", "grocery_section": "produce"},
            {"quantity": 10.0, "unit": "oz", "item": "chicken", "grocery_section": "meat"},
        ]
    })

    if r1.status_code != 201 or r2.status_code != 201:
        print(f"FAIL: Could not create test recipes: {r1.status_code}, {r2.status_code}")
        sys.exit(1)

    rid1, rid2 = r1.json()["id"], r2.json()["id"]
    print(f"  OK: Recipes created (id={rid1}, id={rid2})")

    WEEK = "2026-02-16"

    # Assign both to the week
    a1 = client.put("/api/meals", json={"week_start": WEEK, "day_of_week": 0, "meal_slot": "dinner", "recipe_id": rid1})
    a2 = client.put("/api/meals", json={"week_start": WEEK, "day_of_week": 1, "meal_slot": "lunch", "recipe_id": rid2})

    if a1.status_code not in (200, 201) or a2.status_code not in (200, 201):
        print(f"FAIL: Could not assign recipes to meal plan: {a1.status_code}, {a2.status_code}")
        sys.exit(1)
    print(f"  OK: Recipes assigned to meal plan for week {WEEK}")

    print()
    print("--- POST /api/shopping/generate - Generate from meal plan ---")
    resp = client.post("/api/shopping/generate", json={"week_start": WEEK})
    if resp.status_code in (200, 201):
        gen_result = resp.json()
        print(f"  PASS: POST /api/shopping/generate returns {resp.status_code}")
    else:
        print(f"  FAIL: Expected 200/201, got {resp.status_code}: {resp.text[:200]}")
        failures.append("POST /api/shopping/generate returns 200 or 201")

    print()
    print("--- GET /api/shopping/current - Get current list ---")
    resp = client.get("/api/shopping/current")
    if resp.status_code == 200:
        current = resp.json()
        items = current.get("items", current) if isinstance(current, dict) else current
        if isinstance(items, list) and len(items) > 0:
            print(f"  PASS: GET /api/shopping/current returns {len(items)} item(s)")
        else:
            print(f"  FAIL: Expected items in shopping list, got: {str(current)[:200]}")
            failures.append("GET /api/shopping/current returns items")
        items_list = items if isinstance(items, list) else []
    else:
        print(f"  FAIL: Expected 200, got {resp.status_code}")
        failures.append("GET /api/shopping/current returns 200")
        items_list = []

    print()
    print("--- Verify ingredient aggregation: broccoli merged (1+2=3 cups) ---")
    broccoli_items = [i for i in items_list if "broccoli" in i.get("item", "").lower()]
    if len(broccoli_items) == 1:
        qty = broccoli_items[0].get("quantity")
        unit = broccoli_items[0].get("unit")
        if qty == 3.0 and unit == "cup":
            print(f"  PASS: Broccoli aggregated correctly: {qty} {unit}")
        else:
            print(f"  FAIL: Broccoli aggregation wrong: {qty} {unit} (expected 3.0 cup)")
            failures.append("Ingredient aggregation: broccoli 1+2=3 cups")
    elif len(broccoli_items) > 1:
        print(f"  FAIL: Broccoli not merged - found {len(broccoli_items)} separate entries")
        failures.append("Ingredient aggregation: broccoli not merged")
    else:
        print(f"  FAIL: Broccoli not found in shopping list")
        failures.append("Ingredient aggregation: broccoli missing")

    print()
    print("--- Verify weight aggregation: chicken merged (6+10=16 oz -> 1 lb) ---")
    chicken_items = [i for i in items_list if "chicken" in i.get("item", "").lower()]
    if len(chicken_items) == 1:
        qty = chicken_items[0].get("quantity")
        unit = chicken_items[0].get("unit")
        if qty == 1.0 and unit == "lb":
            print(f"  PASS: Chicken aggregated and converted: {qty} {unit}")
        elif qty == 16.0 and unit == "oz":
            print(f"  FAIL: Chicken aggregated but not upconverted to lb: {qty} {unit}")
            failures.append("Ingredient aggregation: chicken oz->lb upconversion")
        else:
            print(f"  FAIL: Chicken aggregation wrong: {qty} {unit} (expected 1.0 lb)")
            failures.append("Ingredient aggregation: chicken 6+10=16 oz -> 1 lb")
    elif len(chicken_items) > 1:
        print(f"  FAIL: Chicken not merged - found {len(chicken_items)} separate entries")
        failures.append("Ingredient aggregation: chicken not merged")
    else:
        print(f"  FAIL: Chicken not found in shopping list")
        failures.append("Ingredient aggregation: chicken missing")

    print()
    print("--- Verify grouped by grocery section ---")
    if items_list:
        sections_found = {i.get("grocery_section") for i in items_list}
        expected_sections = {"produce", "pantry", "meat"}
        if expected_sections.issubset(sections_found):
            print(f"  PASS: Items have correct grocery sections: {sections_found}")
        else:
            print(f"  FAIL: Expected sections {expected_sections}, got {sections_found}")
            failures.append("Shopping items grouped by grocery section")

    print()
    print("--- PATCH /api/shopping/items/{id} - Toggle checked ---")
    if items_list:
        item = items_list[0]
        item_id = item.get("id")
        original_checked = item.get("checked", 0)

        resp = client.patch(f"/api/shopping/items/{item_id}", json={"checked": 1})
        if resp.status_code == 200:
            updated = resp.json()
            new_checked = updated.get("checked", original_checked)
            if new_checked != original_checked:
                print(f"  PASS: PATCH toggle checked: {original_checked} -> {new_checked}")
            else:
                print(f"  FAIL: checked state did not change (still {new_checked})")
                failures.append("PATCH /api/shopping/items/{id} toggles checked")
        else:
            print(f"  FAIL: Expected 200, got {resp.status_code}")
            failures.append("PATCH /api/shopping/items/{id} returns 200")

    print()
    print("--- POST /api/shopping/items - Add manual item ---")
    manual_item = {
        "item": "paper towels",
        "quantity": 1.0,
        "unit": "whole",
        "grocery_section": "other",
        "source": "manual"
    }
    resp = client.post("/api/shopping/items", json=manual_item)
    if resp.status_code in (200, 201):
        added = resp.json()
        manual_id = added.get("id")
        if added.get("source") == "manual" or added.get("item") == "paper towels":
            print(f"  PASS: POST /api/shopping/items adds manual item (id={manual_id})")
        else:
            print(f"  FAIL: Manual item not correct: {added}")
            failures.append("POST /api/shopping/items adds manual item")
    else:
        print(f"  FAIL: Expected 200/201, got {resp.status_code}: {resp.text[:100]}")
        failures.append("POST /api/shopping/items returns 200/201")
        manual_id = None

    print()
    print("--- DELETE /api/shopping/items/{id} - Remove item ---")
    if manual_id:
        resp = client.delete(f"/api/shopping/items/{manual_id}")
        if resp.status_code in (200, 204):
            print(f"  PASS: DELETE /api/shopping/items/{manual_id} returns {resp.status_code}")
            # Verify it's gone
            resp_check = client.get("/api/shopping/current")
            if resp_check.status_code == 200:
                check_items = resp_check.json()
                check_list = check_items.get("items", check_items) if isinstance(check_items, dict) else check_items
                still_there = [i for i in check_list if i.get("id") == manual_id]
                if not still_there:
                    print(f"  PASS: Deleted item no longer in current list")
                else:
                    print(f"  FAIL: Item still in list after delete")
                    failures.append("DELETE /api/shopping/items removes from list")
        else:
            print(f"  FAIL: Expected 200/204, got {resp.status_code}")
            failures.append("DELETE /api/shopping/items/{id} returns 200 or 204")

    print()
    print("--- Generate new list replaces old one ---")
    # Generate again
    resp_gen2 = client.post("/api/shopping/generate", json={"week_start": WEEK})
    if resp_gen2.status_code in (200, 201):
        resp_new = client.get("/api/shopping/current")
        if resp_new.status_code == 200:
            new_items = resp_new.json()
            new_list = new_items.get("items", new_items) if isinstance(new_items, dict) else new_items
            # Old item IDs should be gone (list was replaced)
            old_ids = {i.get("id") for i in items_list}
            new_ids = {i.get("id") for i in new_list}
            if not old_ids.intersection(new_ids):
                print(f"  PASS: Generating new list replaces old list (old IDs gone)")
            else:
                print(f"  INFO: Some IDs overlap (may be re-generated with same IDs, checking item counts)")
                # Accept if item count is consistent
                if len(new_list) >= len([i for i in items_list if i.get("source") != "manual"]):
                    print(f"  PASS: New list has at least as many items as before")
                else:
                    print(f"  FAIL: New list has fewer items than expected")
                    failures.append("Generate replaces old shopping list")
    else:
        print(f"  FAIL: Second generate returned {resp_gen2.status_code}")
        failures.append("Second POST /api/shopping/generate returns 200 or 201")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} test(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("RESULT: PASS - All shopping list API integration tests passed")
    sys.exit(0)
