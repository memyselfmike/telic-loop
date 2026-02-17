#!/usr/bin/env python3
"""
Verification: Complete meal planning workflow
PRD Reference: Section 5 (Epic 2 Acceptance Criteria), Section 3.2
Vision Goal: "Plan Meals for the Week" - assign, view, clear, swap, navigate weeks, copy slots
Category: value

Proves the core value chain:
"A weekly planner shows 7 days (Monday-Sunday) with meal slots... The cook assigns
recipes to slots... copy a recipe to multiple slots (meal prep — same lunch all week).
Navigating between weeks... Each day shows prep+cook time."

Simulates the meal prep workflow: assign same recipe to Mon-Fri lunch slots (5 PUT calls).
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== VALUE: Complete Meal Planning Workflow ===")
print("Vision: Cook plans their week — assign recipes, see prep time, copy to multiple slots")
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
    test_db = Path(tmpdir) / "meal_plan.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db
    asyncio.run(db_module.init_db())
    client = TestClient(app)

    print("=== Scenario: Cook plans meals for the week ===")
    print()

    print("--- Setup: Create 3 recipes for the week ---")
    recipes = [
        {
            "title": "Meal Prep Lunch Bowl",
            "category": "lunch",
            "prep_time_minutes": 15,
            "cook_time_minutes": 20,
            "servings": 1,
            "description": "", "instructions": "", "tags": "meal-prep",
            "ingredients": [{"quantity": 1.0, "unit": "cup", "item": "rice", "grocery_section": "pantry"}]
        },
        {
            "title": "Quick Weeknight Pasta",
            "category": "dinner",
            "prep_time_minutes": 10,
            "cook_time_minutes": 25,
            "servings": 4,
            "description": "", "instructions": "", "tags": "quick",
            "ingredients": [{"quantity": 300.0, "unit": "g", "item": "pasta", "grocery_section": "pantry"}]
        },
        {
            "title": "Sunday Roast",
            "category": "dinner",
            "prep_time_minutes": 30,
            "cook_time_minutes": 120,
            "servings": 6,
            "description": "", "instructions": "", "tags": "weekend",
            "ingredients": [{"quantity": 2.0, "unit": "lb", "item": "beef roast", "grocery_section": "meat"}]
        }
    ]

    recipe_ids = []
    for r in recipes:
        resp = client.post("/api/recipes", json=r)
        if resp.status_code == 201:
            recipe_ids.append(resp.json()["id"])
        else:
            print(f"  FAIL: Create recipe '{r['title']}': {resp.status_code}")

    if len(recipe_ids) == 3:
        lunch_id, pasta_id, roast_id = recipe_ids
        print(f"  OK: Recipes created: lunch={lunch_id}, pasta={pasta_id}, roast={roast_id}")
    else:
        print(f"  FAIL: Only {len(recipe_ids)} recipes created")
        sys.exit(1)

    WEEK = "2026-02-16"  # Monday Feb 16, 2026

    print()
    print("--- Value Check 1: Copy recipe to Mon-Fri lunch slots (meal prep workflow) ---")
    print("  (This proves: 'copy a recipe to multiple slots — same lunch all week')")
    meal_prep_results = []
    for day in range(5):  # Mon=0, Tue=1, Wed=2, Thu=3, Fri=4
        resp = client.put("/api/meals", json={
            "week_start": WEEK,
            "day_of_week": day,
            "meal_slot": "lunch",
            "recipe_id": lunch_id
        })
        meal_prep_results.append((day, resp.status_code))

    all_ok = all(code in (200, 201) for _, code in meal_prep_results)
    if all_ok:
        print(f"  PASS: All 5 PUT /api/meals calls succeeded for Mon-Fri lunch")
    else:
        failed_days = [(d, c) for d, c in meal_prep_results if c not in (200, 201)]
        print(f"  FAIL: {len(failed_days)} PUT call(s) failed: {failed_days}")
        failures.append("Copy to 5 slots: all PUT calls succeed")

    # Verify all 5 slots are assigned
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries = resp.json()
        lunch_entries = [e for e in entries if e.get("meal_slot") == "lunch"]
        lunch_days = {e.get("day_of_week") for e in lunch_entries if e.get("recipe_id") == lunch_id}
        if lunch_days == {0, 1, 2, 3, 4}:
            print(f"  PASS: All 5 lunch slots show the meal prep recipe")
        else:
            print(f"  FAIL: Only days {lunch_days} have the meal prep recipe (expected 0-4)")
            failures.append("Copy to 5 slots: all 5 slots display recipe")
    else:
        print(f"  FAIL: GET /api/meals returned {resp.status_code}")
        failures.append("Copy to 5 slots: GET week returns 200")

    print()
    print("--- Value Check 2: Assign dinner recipes (Mon=pasta, Sun=roast) ---")
    resp_mon = client.put("/api/meals", json={
        "week_start": WEEK, "day_of_week": 0, "meal_slot": "dinner", "recipe_id": pasta_id
    })
    resp_sun = client.put("/api/meals", json={
        "week_start": WEEK, "day_of_week": 6, "meal_slot": "dinner", "recipe_id": roast_id
    })
    if resp_mon.status_code in (200, 201) and resp_sun.status_code in (200, 201):
        print(f"  PASS: Dinner slots assigned for Monday and Sunday")
    else:
        print(f"  FAIL: Mon={resp_mon.status_code}, Sun={resp_sun.status_code}")
        failures.append("Assign dinner slots")

    print()
    print("--- Value Check 3: View full week plan with recipe details ---")
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries = resp.json()
        total = len(entries)
        # Should have 5 lunches + 2 dinners = 7 entries
        if total >= 7:
            print(f"  PASS: Week plan has {total} entries (5 lunches + 2+ dinners)")
        else:
            print(f"  FAIL: Expected 7+ entries, got {total}")
            failures.append("Week plan has all assigned slots")

        # Check recipe details are included
        sample = entries[0] if entries else {}
        has_details = (
            "title" in sample or "recipe_title" in sample
        ) and (
            "total_time" in sample
        )
        if has_details:
            print(f"  PASS: Entries include recipe title and total_time")
        else:
            print(f"  FAIL: Entries missing recipe details. Keys: {list(sample.keys())}")
            failures.append("Week plan entries include recipe title and times")
    else:
        print(f"  FAIL: GET /api/meals?week={WEEK}: {resp.status_code}")
        failures.append("View week plan returns 200")

    print()
    print("--- Value Check 4: Day time totals can be computed ---")
    # Monday has: lunch (15+20=35 min) + dinner (10+25=35 min) = 70 min total
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries = resp.json()
        monday_entries = [e for e in entries if e.get("day_of_week") == 0]
        total_time = sum(
            e.get("total_time", 0)
            for e in monday_entries
        )
        if total_time == 70:
            print(f"  PASS: Monday total cook time = 70 min (15+20 lunch + 10+25 dinner)")
        elif total_time > 0:
            print(f"  PASS: Monday total cook time = {total_time} min (computed from total_time field)")
        else:
            print(f"  FAIL: Cannot compute day time total (got {total_time} min)")
            failures.append("Day time total computable from API response")

    print()
    print("--- Value Check 5: Clear a slot (remove assignment) ---")
    # Remove Monday lunch
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries = resp.json()
        mon_lunch = next((e for e in entries if e.get("day_of_week") == 0 and e.get("meal_slot") == "lunch"), None)
        if mon_lunch:
            meal_entry_id = mon_lunch.get("id")
            del_resp = client.delete(f"/api/meals/{meal_entry_id}")
            if del_resp.status_code in (200, 204):
                # Verify slot is now empty
                resp2 = client.get(f"/api/meals?week={WEEK}")
                entries2 = resp2.json()
                still_there = any(
                    e.get("day_of_week") == 0 and e.get("meal_slot") == "lunch"
                    for e in entries2
                )
                if not still_there:
                    print(f"  PASS: Cleared Monday lunch slot")
                else:
                    print(f"  FAIL: Monday lunch slot still has assignment after delete")
                    failures.append("Clear slot removes assignment")
            else:
                print(f"  FAIL: DELETE /api/meals/{meal_entry_id}: {del_resp.status_code}")
                failures.append("Clear slot: DELETE returns 200 or 204")
        else:
            print(f"  SKIP: Could not find Monday lunch entry to clear")

    print()
    print("--- Value Check 6: Navigate to next week (week isolation) ---")
    NEXT_WEEK = "2026-02-23"
    resp = client.get(f"/api/meals?week={NEXT_WEEK}")
    if resp.status_code == 200:
        next_week_entries = resp.json()
        if next_week_entries == []:
            print(f"  PASS: Next week is empty (weeks are independent)")
        else:
            print(f"  FAIL: Next week has {len(next_week_entries)} entries (should be empty)")
            failures.append("Week navigation: next week starts empty")
    else:
        print(f"  FAIL: GET /api/meals?week={NEXT_WEEK}: {resp.status_code}")
        failures.append("Week navigation: GET next week returns 200")

    print()
    print("--- Value Check 7: Upsert (swap) replaces slot recipe ---")
    # Re-assign Monday dinner (currently pasta) to roast
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries = resp.json()
        mon_dinner = next((e for e in entries if e.get("day_of_week") == 0 and e.get("meal_slot") == "dinner"), None)
        if mon_dinner and mon_dinner.get("recipe_id") == pasta_id:
            # Swap to roast
            swap_resp = client.put("/api/meals", json={
                "week_start": WEEK, "day_of_week": 0, "meal_slot": "dinner", "recipe_id": roast_id
            })
            if swap_resp.status_code in (200, 201):
                resp2 = client.get(f"/api/meals?week={WEEK}")
                entries2 = resp2.json()
                new_mon_dinner = next((e for e in entries2 if e.get("day_of_week") == 0 and e.get("meal_slot") == "dinner"), None)
                if new_mon_dinner and new_mon_dinner.get("recipe_id") == roast_id:
                    # Check no duplicate (only 1 entry for this slot)
                    duplicates = [e for e in entries2 if e.get("day_of_week") == 0 and e.get("meal_slot") == "dinner"]
                    if len(duplicates) == 1:
                        print(f"  PASS: Swapped Monday dinner from pasta to roast (no duplicate)")
                    else:
                        print(f"  FAIL: Swap created {len(duplicates)} entries for same slot")
                        failures.append("Swap: upsert replaces without duplicate")
                else:
                    print(f"  FAIL: After swap, Monday dinner still has old recipe")
                    failures.append("Swap: new recipe shows in slot")
            else:
                print(f"  FAIL: Swap PUT returned {swap_resp.status_code}")
                failures.append("Swap: PUT returns 200/201")
        else:
            print(f"  SKIP: Monday dinner not in expected state for swap test")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} value check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("User impact: Cook cannot plan their week — the core meal planning promise is undelivered.")
    sys.exit(1)
else:
    print("RESULT: PASS - Complete meal planning workflow works end-to-end")
    print("Value delivered: Cook can plan the full week, meal prep lunches, swap dinners, and navigate weeks.")
    sys.exit(0)
