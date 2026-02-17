#!/usr/bin/env python3
"""
Verification: Meal plan API endpoints
PRD Reference: Section 3.2 (Meal Plan Endpoints), Task 2.3
Vision Goal: "Plan Meals for the Week" - assign recipes, navigate weeks, see weekly plan
Category: integration

Tests meal plan CRUD: assign, retrieve with recipe details, upsert, delete,
cascade delete, week isolation, invalid recipe_id.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== Meal Plan API Integration Tests ===")
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
    test_db = Path(tmpdir) / "test_meals.db"
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

    # Create a test recipe to assign to meal plan slots
    RECIPE = {
        "title": "Meal Plan Test Recipe",
        "description": "Test",
        "category": "dinner",
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "servings": 2,
        "instructions": "Cook it.",
        "tags": "test",
        "ingredients": [
            {"quantity": 1.0, "unit": "cup", "item": "rice", "grocery_section": "pantry"}
        ]
    }

    print()
    print("--- Setup: Create test recipe ---")
    resp = client.post("/api/recipes", json=RECIPE)
    if resp.status_code == 201:
        recipe_id = resp.json()["id"]
        print(f"  OK: Test recipe created (id={recipe_id})")
    else:
        print(f"  FAIL: Could not create test recipe: {resp.status_code} {resp.text[:100]}")
        sys.exit(1)

    WEEK = "2026-02-16"  # Monday

    print()
    print("--- PUT /api/meals - Assign recipe to slot ---")
    meal_body = {
        "week_start": WEEK,
        "day_of_week": 0,  # Monday
        "meal_slot": "dinner",
        "recipe_id": recipe_id
    }
    resp = client.put("/api/meals", json=meal_body)
    if resp.status_code in (200, 201):
        meal_entry = resp.json()
        meal_id = meal_entry.get("id")
        print(f"  PASS: PUT /api/meals returns {resp.status_code}, entry id={meal_id}")
    else:
        print(f"  FAIL: Expected 200 or 201, got {resp.status_code}: {resp.text[:200]}")
        failures.append("PUT /api/meals assign recipe")
        meal_id = None

    print()
    print("--- GET /api/meals?week= - Retrieve week plan with recipe details ---")
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries = resp.json()
        if entries:
            entry = entries[0]
            has_title = "title" in entry or "recipe_title" in entry
            has_total_time = "total_time" in entry
            if has_title and has_total_time:
                print(f"  PASS: GET /api/meals returns entries with recipe title and total_time")
            else:
                print(f"  FAIL: Entry missing recipe details. Keys: {list(entry.keys())}")
                failures.append("GET /api/meals includes recipe title and total_time")
        else:
            print(f"  FAIL: No entries returned for week {WEEK}")
            failures.append("GET /api/meals returns entries")
    else:
        print(f"  FAIL: Expected 200, got {resp.status_code}")
        failures.append("GET /api/meals returns 200")

    print()
    print("--- PUT /api/meals (upsert) - Replace existing slot assignment ---")
    # Create second recipe
    resp2 = client.post("/api/recipes", json={**RECIPE, "title": "Second Recipe", "category": "dinner"})
    if resp2.status_code == 201:
        recipe2_id = resp2.json()["id"]
        # Upsert same slot with different recipe
        upsert_body = {
            "week_start": WEEK,
            "day_of_week": 0,
            "meal_slot": "dinner",
            "recipe_id": recipe2_id
        }
        resp_u = client.put("/api/meals", json=upsert_body)
        if resp_u.status_code in (200, 201):
            # Verify the slot now has recipe2
            resp_check = client.get(f"/api/meals?week={WEEK}")
            if resp_check.status_code == 200:
                entries = resp_check.json()
                monday_dinner = [e for e in entries if e.get("day_of_week") == 0 and e.get("meal_slot") == "dinner"]
                if len(monday_dinner) == 1:
                    rec_id = monday_dinner[0].get("recipe_id")
                    if rec_id == recipe2_id:
                        print(f"  PASS: Upsert replaced recipe in slot (now recipe_id={recipe2_id})")
                    else:
                        print(f"  FAIL: Expected recipe_id={recipe2_id}, got {rec_id}")
                        failures.append("PUT /api/meals upsert replaces recipe")
                else:
                    print(f"  FAIL: Upsert created duplicate slot (found {len(monday_dinner)} entries)")
                    failures.append("PUT /api/meals upsert no duplicates")
        else:
            print(f"  FAIL: Upsert returned {resp_u.status_code}")
            failures.append("PUT /api/meals upsert returns 200/201")
    else:
        print(f"  SKIP: Could not create second recipe for upsert test")

    print()
    print("--- DELETE /api/meals/{id} - Remove meal plan entry ---")
    # Get the current fresh meal_id (after upsert the original was replaced)
    current_entries = client.get(f"/api/meals?week={WEEK}").json()
    monday_dinner_entries = [e for e in current_entries if e.get("day_of_week") == 0 and e.get("meal_slot") == "dinner"]
    delete_meal_id = monday_dinner_entries[0]["id"] if monday_dinner_entries else None
    if delete_meal_id:
        resp = client.delete(f"/api/meals/{delete_meal_id}")
        if resp.status_code in (200, 204):
            print(f"  PASS: DELETE /api/meals/{delete_meal_id} returns {resp.status_code}")
        else:
            print(f"  FAIL: Expected 200/204, got {resp.status_code}")
            failures.append("DELETE /api/meals/{id} returns 200 or 204")
    else:
        print("  SKIP: No current meal_id found for delete test")

    print()
    print("--- DELETE recipe cascades to meal plan entries ---")
    # Assign a recipe then delete it
    assign_resp = client.put("/api/meals", json={
        "week_start": WEEK,
        "day_of_week": 2,  # Wednesday
        "meal_slot": "lunch",
        "recipe_id": recipe_id
    })
    if assign_resp.status_code in (200, 201):
        # Delete the recipe
        client.delete(f"/api/recipes/{recipe_id}")
        # Check meal plan no longer has entry for this recipe
        resp = client.get(f"/api/meals?week={WEEK}")
        if resp.status_code == 200:
            entries = resp.json()
            orphaned = [e for e in entries if e.get("recipe_id") == recipe_id]
            if not orphaned:
                print(f"  PASS: Deleting recipe removes its meal plan entries")
            else:
                print(f"  FAIL: {len(orphaned)} meal plan entries remain after recipe delete")
                failures.append("Cascade: recipe delete removes meal plan entries")
        else:
            print(f"  SKIP: Could not verify cascade")
    else:
        print(f"  SKIP: Could not assign recipe for cascade test")

    print()
    print("--- PUT /api/meals with invalid recipe_id returns error ---")
    bad_body = {
        "week_start": WEEK,
        "day_of_week": 3,
        "meal_slot": "breakfast",
        "recipe_id": 999999  # Non-existent
    }
    resp = client.put("/api/meals", json=bad_body)
    if resp.status_code in (400, 404, 422):
        print(f"  PASS: Invalid recipe_id returns {resp.status_code} error")
    else:
        print(f"  FAIL: Expected 4xx for invalid recipe_id, got {resp.status_code}")
        failures.append("PUT /api/meals invalid recipe_id returns error")

    print()
    print("--- Week isolation: different weeks return different data ---")
    # Assign to a second week
    other_week = "2026-02-23"  # Next week
    client.put("/api/meals", json={
        "week_start": other_week,
        "day_of_week": 0,
        "meal_slot": "dinner",
        "recipe_id": recipe2_id
    })
    resp1 = client.get(f"/api/meals?week={WEEK}")
    resp2_week = client.get(f"/api/meals?week={other_week}")
    if resp1.status_code == 200 and resp2_week.status_code == 200:
        # The two weeks should be independent
        week1_ids = {e.get("id") for e in resp1.json()}
        week2_ids = {e.get("id") for e in resp2_week.json()}
        if not week1_ids.intersection(week2_ids):
            print(f"  PASS: Different weeks return independent data")
        else:
            print(f"  FAIL: Week data overlaps: {week1_ids} ∩ {week2_ids}")
            failures.append("Week isolation: different weeks return separate data")
    else:
        print(f"  FAIL: Week isolation check failed ({resp1.status_code}, {resp2_week.status_code})")
        failures.append("Week isolation: API returns 200 for both weeks")

    print()
    print("--- GET /api/meals empty week returns [] ---")
    empty_week = "2025-01-01"
    resp = client.get(f"/api/meals?week={empty_week}")
    if resp.status_code == 200 and resp.json() == []:
        print(f"  PASS: Empty week returns []")
    else:
        print(f"  FAIL: Expected [], got status={resp.status_code} body={resp.text[:100]}")
        failures.append("GET /api/meals empty week returns []")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} test(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("RESULT: PASS - All meal plan API integration tests passed")
    sys.exit(0)
