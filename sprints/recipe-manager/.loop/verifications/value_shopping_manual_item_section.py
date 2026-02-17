#!/usr/bin/env python3
"""
Verification: Manual shopping list item appears in 'other' section
PRD Reference: Section 4.3 (Shopping List), Section 3.3 (POST /api/shopping/items)
Vision Goal: "User adds a manual item to the shopping list and it appears in the other section"
Category: value

Proves the value proof:
"User adds a manual item to the shopping list and it appears in the other section"

The 'other' grocery section is the default for manually added items (paper towels, coffee, etc.)
that don't fit standard produce/meat/dairy/pantry/frozen categories.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== VALUE: Manual Shopping Item Appears in 'Other' Section ===")
print("Vision: Cook adds non-recipe items (paper towels, coffee) to shopping list")
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
    test_db = Path(tmpdir) / "manual_item.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db
    asyncio.run(db_module.init_db())
    client = TestClient(app)

    print("=== Scenario: Cook adds manual items to their shopping list ===")
    print()

    # Setup: need an existing list to add items to
    print("--- Setup: Create recipe, assign to plan, generate shopping list ---")
    recipe_resp = client.post("/api/recipes", json={
        "title": "Simple Pasta",
        "category": "dinner",
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "servings": 2,
        "description": "", "instructions": "", "tags": "",
        "ingredients": [
            {"quantity": 2.0, "unit": "cup", "item": "pasta", "grocery_section": "pantry"},
            {"quantity": 1.0, "unit": "cup", "item": "tomato sauce", "grocery_section": "pantry"},
        ]
    })
    if recipe_resp.status_code != 201:
        print(f"FAIL: Could not create recipe: {recipe_resp.status_code}")
        sys.exit(1)

    recipe_id = recipe_resp.json()["id"]
    WEEK = "2026-02-16"

    assign_resp = client.put("/api/meals", json={
        "week_start": WEEK,
        "day_of_week": 0,
        "meal_slot": "dinner",
        "recipe_id": recipe_id
    })
    if assign_resp.status_code not in (200, 201):
        print(f"FAIL: Could not assign recipe to meal plan: {assign_resp.status_code}")
        sys.exit(1)

    gen_resp = client.post("/api/shopping/generate", json={"week_start": WEEK})
    if gen_resp.status_code not in (200, 201):
        print(f"FAIL: Could not generate shopping list: {gen_resp.status_code}")
        sys.exit(1)
    print(f"  OK: Shopping list generated from meal plan")

    print()
    print("--- Value Check 1: Add manual item (paper towels) with no explicit section ---")
    # When no grocery_section is provided, default should be 'other'
    resp = client.post("/api/shopping/items", json={
        "item": "paper towels",
        "quantity": 1.0,
        "unit": "whole",
        "source": "manual"
    })
    if resp.status_code in (200, 201):
        item = resp.json()
        item_id = item.get("id")
        section = item.get("grocery_section", "")
        if section == "other":
            print(f"  PASS: Manual item 'paper towels' created in 'other' section (id={item_id})")
        else:
            print(f"  FAIL: Manual item grocery_section='{section}' (expected 'other')")
            failures.append(f"Manual item with no section defaults to 'other' (got '{section}')")
    else:
        print(f"  FAIL: POST /api/shopping/items returned {resp.status_code}: {resp.text[:200]}")
        failures.append("POST /api/shopping/items returns 200 or 201")
        item_id = None

    print()
    print("--- Value Check 2: Add manual item (coffee) explicitly in 'other' section ---")
    resp2 = client.post("/api/shopping/items", json={
        "item": "coffee beans",
        "quantity": 1.0,
        "unit": "lb",
        "grocery_section": "other",
        "source": "manual"
    })
    if resp2.status_code in (200, 201):
        item2 = resp2.json()
        item2_id = item2.get("id")
        print(f"  PASS: Manual item 'coffee beans' added (id={item2_id})")
    else:
        print(f"  FAIL: POST /api/shopping/items returned {resp2.status_code}")
        failures.append("Add manual item with explicit 'other' section")
        item2_id = None

    print()
    print("--- Value Check 3: Current list contains manual items in 'other' section ---")
    list_resp = client.get("/api/shopping/current")
    if list_resp.status_code == 200:
        data = list_resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        other_items = [i for i in items if i.get("grocery_section") == "other"]
        manual_items = [i for i in items if i.get("source") == "manual"]

        print(f"  Total items in list: {len(items)}")
        print(f"  Items in 'other' section: {len(other_items)}")
        print(f"  Items with source='manual': {len(manual_items)}")

        if len(other_items) >= 1:
            other_names = [i.get("item") for i in other_items]
            print(f"  Items in 'other': {other_names}")
            has_paper_towels = any("paper towels" in i.get("item", "").lower() for i in other_items)
            if has_paper_towels:
                print(f"  PASS: 'paper towels' visible in 'other' grocery section")
            else:
                print(f"  FAIL: 'paper towels' not found in 'other' section — found: {other_names}")
                failures.append("Manual item 'paper towels' appears in 'other' section")
        else:
            print(f"  FAIL: No items in 'other' section (expected at least paper towels)")
            failures.append("Manual items appear in 'other' grocery section")
    else:
        print(f"  FAIL: GET /api/shopping/current returned {list_resp.status_code}")
        failures.append("GET current list returns 200")

    print()
    print("--- Value Check 4: Manual items persist across re-fetch (simulated browser reopen) ---")
    # Re-fetch to simulate browser closing and reopening
    list_resp2 = client.get("/api/shopping/current")
    if list_resp2.status_code == 200:
        data2 = list_resp2.json()
        items2 = data2.get("items", data2) if isinstance(data2, dict) else data2
        other_items2 = [i for i in items2 if i.get("grocery_section") == "other"]
        if len(other_items2) >= 1:
            print(f"  PASS: Manual items persist across re-fetch ({len(other_items2)} in 'other' section)")
        else:
            print(f"  FAIL: Manual items not found on re-fetch")
            failures.append("Manual items persist across re-fetch")
    else:
        print(f"  FAIL: Second GET /api/shopping/current returned {list_resp2.status_code}")
        failures.append("Second GET current list returns 200")

    print()
    print("--- Value Check 5: Manual item can be deleted ---")
    if item_id:
        del_resp = client.delete(f"/api/shopping/items/{item_id}")
        if del_resp.status_code in (200, 204):
            # Verify it's gone from the list
            list_resp3 = client.get("/api/shopping/current")
            if list_resp3.status_code == 200:
                data3 = list_resp3.json()
                items3 = data3.get("items", data3) if isinstance(data3, dict) else data3
                remaining_paper = [i for i in items3 if i.get("id") == item_id]
                if not remaining_paper:
                    print(f"  PASS: Deleted manual item (id={item_id}) no longer in list")
                else:
                    print(f"  FAIL: Deleted item still appears in list")
                    failures.append("Deleted manual item removed from list")
            else:
                print(f"  WARN: Could not re-fetch after delete")
        else:
            print(f"  FAIL: DELETE /api/shopping/items/{item_id} returned {del_resp.status_code}")
            failures.append("DELETE manual item returns 200 or 204")
    else:
        print(f"  SKIP: No item_id to delete (add manual item failed)")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 50)
if failures:
    print(f"RESULT: FAIL — {len(failures)} value check(s) failed:")
    for f in failures:
        print(f"  FAIL: {f}")
    print()
    print("User impact: Cook cannot track non-recipe items they need to buy.")
    print("'Other' section is how non-category items like paper towels and coffee appear in the list.")
    sys.exit(1)
else:
    print("RESULT: PASS — Manual items appear correctly in 'other' grocery section")
    print("Value delivered: Cook can add paper towels, coffee, and other non-recipe items to their")
    print("shopping list. They appear in the 'other' section and persist across browser reopens.")
    sys.exit(0)
