#!/usr/bin/env python3
"""
Verification: Deleting a recipe assigned to a meal plan slot clears the slot
PRD Reference: Section 2.1 (meal_plans FK CASCADE), Section 5 (Epic 2 criteria)
Vision Goal: "Trust the Data" - deleting a recipe removes it from meal plan slots
Category: value

Value Proof #9 from sprint context:
"User deletes a recipe assigned to a meal plan slot and the slot is cleared with a warning"

This verifies:
1. When a recipe is deleted, all meal plan slots using that recipe are automatically cleared
2. The API does not return orphaned meal plan entries after recipe deletion
3. The weekly plan for the affected week no longer shows the deleted recipe
4. Other slots in the same week that use different recipes are NOT affected

Note: The "with a warning" part is a UI concern handled by the frontend (confirmation dialog).
The backend must guarantee that the slot IS cleared via CASCADE delete.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== VALUE: Delete Recipe Clears Assigned Meal Slots ===")
print("Vision: 'Trust the Data' — deleting a recipe removes it from the plan with proper cascade")
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
    test_db = Path(tmpdir) / "cascade.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db
    asyncio.run(db_module.init_db())
    client = TestClient(app, raise_server_exceptions=True)

    print("=== Scenario: Cook plans the week, then removes a recipe ===")
    print()

    WEEK = "2026-02-16"  # Monday

    print("--- Setup: Create two recipes ---")
    # Recipe that will be deleted
    doomed_resp = client.post("/api/recipes", json={
        "title": "Doomed Recipe",
        "description": "This recipe will be deleted",
        "category": "dinner",
        "prep_time_minutes": 20,
        "cook_time_minutes": 30,
        "servings": 4,
        "instructions": "1. Cook. 2. Serve.",
        "tags": "test",
        "ingredients": [
            {"quantity": 1.0, "unit": "lb", "item": "chicken", "grocery_section": "meat"},
            {"quantity": 2.0, "unit": "cup", "item": "rice", "grocery_section": "pantry"},
        ]
    })
    assert doomed_resp.status_code == 201, f"Could not create doomed recipe: {doomed_resp.text[:100]}"
    doomed_id = doomed_resp.json()["id"]
    print(f"  OK: Created 'Doomed Recipe' (id={doomed_id})")

    # Recipe that will survive
    survivor_resp = client.post("/api/recipes", json={
        "title": "Survivor Recipe",
        "description": "This recipe stays in the plan",
        "category": "lunch",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 2,
        "instructions": "1. Prep. 2. Eat.",
        "tags": "test",
        "ingredients": [
            {"quantity": 200.0, "unit": "g", "item": "pasta", "grocery_section": "pantry"},
        ]
    })
    assert survivor_resp.status_code == 201
    survivor_id = survivor_resp.json()["id"]
    print(f"  OK: Created 'Survivor Recipe' (id={survivor_id})")

    print()
    print("--- Step 1: Assign doomed recipe to multiple slots ---")
    slots_for_doomed = [
        (0, "dinner"),  # Monday dinner
        (2, "dinner"),  # Wednesday dinner
        (4, "dinner"),  # Friday dinner
    ]
    doomed_meal_ids = []
    for day, slot in slots_for_doomed:
        resp = client.put("/api/meals", json={
            "week_start": WEEK,
            "day_of_week": day,
            "meal_slot": slot,
            "recipe_id": doomed_id
        })
        assert resp.status_code in (200, 201), f"Failed to assign slot day={day}: {resp.status_code}"
        doomed_meal_ids.append(resp.json()["id"])
    print(f"  OK: Doomed recipe assigned to 3 slots: Monday, Wednesday, Friday dinner")

    print()
    print("--- Step 2: Assign survivor recipe to another slot ---")
    survivor_resp2 = client.put("/api/meals", json={
        "week_start": WEEK,
        "day_of_week": 0,  # Monday lunch
        "meal_slot": "lunch",
        "recipe_id": survivor_id
    })
    assert survivor_resp2.status_code in (200, 201)
    survivor_meal_id = survivor_resp2.json()["id"]
    print(f"  OK: Survivor recipe assigned to Monday lunch (id={survivor_meal_id})")

    print()
    print("--- Step 3: Verify week plan before deletion ---")
    resp = client.get(f"/api/meals?week={WEEK}")
    assert resp.status_code == 200
    entries_before = resp.json()
    doomed_entries_before = [e for e in entries_before if e.get("recipe_id") == doomed_id]
    survivor_entries_before = [e for e in entries_before if e.get("recipe_id") == survivor_id]
    total_before = len(entries_before)

    if len(doomed_entries_before) == 3:
        print(f"  OK: Week plan has {total_before} total entries, 3 using 'Doomed Recipe'")
    else:
        print(f"  WARN: Expected 3 doomed entries, found {len(doomed_entries_before)}")

    print()
    print("--- Value Check 1: Delete the doomed recipe ---")
    del_resp = client.delete(f"/api/recipes/{doomed_id}")
    if del_resp.status_code in (200, 204):
        print(f"  PASS: DELETE /api/recipes/{doomed_id} returns {del_resp.status_code}")
    else:
        print(f"  FAIL: DELETE /api/recipes/{doomed_id} returned {del_resp.status_code}")
        failures.append("DELETE /api/recipes returns 200/204")

    print()
    print("--- Value Check 2: Deleted recipe no longer accessible ---")
    get_deleted = client.get(f"/api/recipes/{doomed_id}")
    if get_deleted.status_code == 404:
        print(f"  PASS: GET /api/recipes/{doomed_id} returns 404 (recipe gone)")
    else:
        print(f"  FAIL: Expected 404 for deleted recipe, got {get_deleted.status_code}")
        failures.append("Deleted recipe returns 404")

    print()
    print("--- Value Check 3: Meal plan slots for deleted recipe are CLEARED ---")
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries_after = resp.json()
        orphaned_entries = [e for e in entries_after if e.get("recipe_id") == doomed_id]
        if not orphaned_entries:
            print(f"  PASS: All {len(doomed_entries_before)} meal plan slots using 'Doomed Recipe' are cleared")
        else:
            print(f"  FAIL: {len(orphaned_entries)} orphaned meal plan entries remain!")
            for e in orphaned_entries:
                print(f"        Orphan: day={e.get('day_of_week')}, slot={e.get('meal_slot')}, recipe_id={e.get('recipe_id')}")
            print(f"        CASCADE DELETE not working for meal_plans table")
            failures.append("CASCADE: meal plan entries cleared when recipe deleted")
    else:
        print(f"  FAIL: GET /api/meals returned {resp.status_code}")
        failures.append("GET /api/meals after recipe delete returns 200")

    print()
    print("--- Value Check 4: Survivor recipe slot is NOT affected ---")
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries_after = resp.json()
        survivor_entries_after = [e for e in entries_after if e.get("recipe_id") == survivor_id]
        if len(survivor_entries_after) == len(survivor_entries_before):
            print(f"  PASS: Survivor recipe still assigned to {len(survivor_entries_after)} slot(s)")
        else:
            print(f"  FAIL: Survivor recipe lost entries: had {len(survivor_entries_before)}, now {len(survivor_entries_after)}")
            failures.append("Cascade: survivor recipe slots not affected by delete")

    print()
    print("--- Value Check 5: Week plan total entries reduced by exact amount ---")
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries_after = resp.json()
        total_after = len(entries_after)
        expected_after = total_before - len(doomed_entries_before)
        if total_after == expected_after:
            print(f"  PASS: Week plan reduced from {total_before} to {total_after} entries (removed {len(doomed_entries_before)} doomed)")
        else:
            print(f"  FAIL: Expected {expected_after} entries after delete, got {total_after}")
            failures.append("Week plan count correct after cascade delete")

    print()
    print("--- Value Check 6: Doomed recipe ingredients also CASCADE deleted ---")
    # Verify the ingredients table doesn't have orphaned rows
    import sqlite3
    conn = sqlite3.connect(str(db_module.DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    orphaned_ings = conn.execute(
        "SELECT id FROM ingredients WHERE recipe_id = ?", (doomed_id,)
    ).fetchall()
    conn.close()
    if not orphaned_ings:
        print(f"  PASS: Ingredients for deleted recipe also cascade-deleted from DB")
    else:
        print(f"  FAIL: {len(orphaned_ings)} orphaned ingredient rows remain in DB")
        failures.append("CASCADE: ingredients removed when recipe deleted")

    print()
    print("--- Value Check 7: Can still use survivor recipe (not corrupted) ---")
    # Verify survivor recipe is fully accessible with ingredients
    get_survivor = client.get(f"/api/recipes/{survivor_id}")
    if get_survivor.status_code == 200:
        data = get_survivor.json()
        if data.get("title") == "Survivor Recipe" and len(data.get("ingredients", [])) > 0:
            print(f"  PASS: Survivor recipe still fully accessible with ingredients")
        else:
            print(f"  FAIL: Survivor recipe data incomplete: {data}")
            failures.append("Survivor recipe still accessible after other recipe deleted")
    else:
        print(f"  FAIL: GET survivor recipe returned {get_survivor.status_code}")
        failures.append("Survivor recipe accessible after delete")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} value check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("User impact: Cook deletes a recipe but it lingers in their meal plan — ")
    print("showing phantom recipes for meals that no longer exist. Data is corrupted.")
    print()
    print("Fix: Ensure meal_plans table has:")
    print("  FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE")
    print("  AND PRAGMA foreign_keys = ON in get_db()")
    sys.exit(1)
else:
    print("RESULT: PASS - Deleting a recipe correctly clears all assigned meal plan slots")
    print("Value delivered: Cook trusts the data — recipe gone means it's gone everywhere.")
    sys.exit(0)
