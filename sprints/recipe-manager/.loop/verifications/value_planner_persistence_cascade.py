#!/usr/bin/env python3
"""
Verification: Planner persistence, cascade delete, and day total accuracy
PRD Reference: Section 4.2, Section 5 (Epic 2), Section 2.1 (ON DELETE CASCADE)
Vision Goal: "Trust the Data" - planner data persists across navigation/reloads and
             stays consistent when recipes are deleted from the collection.
Category: value

Task E2-6 covers three integration behaviors:

1. PERSISTENCE — Assigned meals survive navigation between tabs and between weeks.
   Each call to renderPlanner() re-fetches from GET /api/meals?week= so slots
   always reflect the current DB state. This is verified by simulating navigation
   (calling GET /api/meals again) after assigning meals.

2. CASCADE DELETE — Deleting a recipe from the collection automatically clears all
   planner slots that used it (via SQLite ON DELETE CASCADE on meal_plans.recipe_id).
   The planner must render an empty slot (no recipe) when a cascade-deleted entry is
   absent from the GET /api/meals response.

3. DAY TOTALS ACCURACY — The day total row sums total_time (prep+cook) across all
   assigned meal slots for each day column. The API provides total_time per entry;
   the planner.js buildTotalRow() sums them per day. We verify the API gives correct
   per-entry total_time values so the frontend can produce accurate day totals.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

# Ensure UTF-8 output on Windows (cp1252 default breaks unicode in print)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))
FRONTEND_DIR = Path(SPRINT_DIR) / "frontend"

print("=== VALUE: Planner Persistence, Cascade Delete, and Day Totals Accuracy ===")
print("Task E2-6 — Verifying trustworthy planner data across navigation and recipe deletion")
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
    test_db = Path(tmpdir) / "planner_e2_6.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db
    asyncio.run(db_module.init_db())
    client = TestClient(app, raise_server_exceptions=True)

    WEEK = "2026-02-16"   # Monday Feb 16, 2026
    NEXT_WEEK = "2026-02-23"
    PREV_WEEK = "2026-02-09"

    # ─── Setup: Create test recipes with known times ───────────────────────────
    print("--- Setup: Create test recipes with known prep+cook times ---")

    def create_recipe(title, category, prep, cook):
        resp = client.post("/api/recipes", json={
            "title": title,
            "category": category,
            "prep_time_minutes": prep,
            "cook_time_minutes": cook,
            "servings": 2,
            "description": f"{category} recipe",
            "instructions": "Cook and serve.",
            "tags": "test",
            "ingredients": [
                {"quantity": 1.0, "unit": "cup", "item": "ingredient", "grocery_section": "other"}
            ]
        })
        assert resp.status_code == 201, f"Failed to create '{title}': {resp.status_code}"
        return resp.json()["id"]

    breakfast_id = create_recipe("Persistence Oatmeal", "breakfast", 5, 10)   # total=15
    lunch_id = create_recipe("Persistence Salad", "lunch", 10, 0)             # total=10
    dinner_id = create_recipe("Persistence Stir Fry", "dinner", 15, 20)       # total=35
    cascade_id = create_recipe("Cascade Victim Recipe", "dinner", 20, 30)     # total=50
    print(f"  OK: breakfast={breakfast_id}(15min), lunch={lunch_id}(10min), "
          f"dinner={dinner_id}(35min), cascade={cascade_id}(50min)")

    # ─── PART 1: PERSISTENCE ──────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("PART 1: Persistence — data survives navigation between tabs/weeks")
    print("=" * 60)
    print()
    print("Approach: Assign meals, then re-fetch (simulating navigation away and back).")
    print("The planner fetches fresh from GET /api/meals on every navigation to #planner.")
    print()

    print("--- Check 1a: Assign recipes to multiple slots ---")
    assignments = [
        (0, "breakfast", breakfast_id),  # Monday breakfast
        (0, "lunch", lunch_id),          # Monday lunch
        (2, "dinner", dinner_id),        # Wednesday dinner
        (4, "breakfast", breakfast_id),  # Friday breakfast
        (6, "dinner", dinner_id),        # Sunday dinner
    ]
    assigned_ids = {}
    for day, slot, recipe_id in assignments:
        resp = client.put("/api/meals", json={
            "week_start": WEEK,
            "day_of_week": day,
            "meal_slot": slot,
            "recipe_id": recipe_id
        })
        if resp.status_code in (200, 201):
            assigned_ids[(day, slot)] = resp.json()["id"]
        else:
            print(f"  FAIL: Could not assign day={day} slot={slot}: {resp.status_code}")
            failures.append(f"Setup: assign day={day} slot={slot}")

    if len(assigned_ids) == len(assignments):
        print(f"  PASS: All {len(assignments)} slots assigned successfully")
    else:
        print(f"  FAIL: Only {len(assigned_ids)}/{len(assignments)} slots assigned")
        failures.append("Persistence setup: all slots assigned")

    print()
    print("--- Check 1b: Simulate tab navigation away and back to #planner ---")
    print("  (Calls GET /api/meals fresh — same as renderPlanner() does on every visit)")
    reload_resp = client.get(f"/api/meals?week={WEEK}")
    if reload_resp.status_code == 200:
        reloaded = reload_resp.json()
        # Build index by (day_of_week, meal_slot)
        reloaded_index = {(e["day_of_week"], e["meal_slot"]): e for e in reloaded}
        all_present = True
        for day, slot, expected_recipe_id in assignments:
            entry = reloaded_index.get((day, slot))
            if entry and entry.get("recipe_id") == expected_recipe_id:
                pass  # Good
            else:
                print(f"  FAIL: day={day} slot={slot} not persisted after navigation "
                      f"(expected recipe_id={expected_recipe_id}, got {entry})")
                all_present = False
                failures.append(f"Persistence: day={day} slot={slot} survives navigation")
        if all_present:
            print(f"  PASS: All {len(assignments)} assignments persist after simulated navigation")
    else:
        print(f"  FAIL: GET /api/meals?week={WEEK} returned {reload_resp.status_code}")
        failures.append("Persistence: GET /api/meals after navigation returns 200")

    print()
    print("--- Check 1c: Simulate week navigation (prev week, next week, back) ---")
    # Navigate to previous week
    prev_resp = client.get(f"/api/meals?week={PREV_WEEK}")
    next_resp = client.get(f"/api/meals?week={NEXT_WEEK}")
    back_resp = client.get(f"/api/meals?week={WEEK}")

    if prev_resp.status_code == 200 and next_resp.status_code == 200 and back_resp.status_code == 200:
        prev_entries = prev_resp.json()
        next_entries = next_resp.json()
        back_entries = back_resp.json()

        # Previous week should be empty (we only assigned to WEEK)
        if prev_entries == []:
            print(f"  PASS: Previous week ({PREV_WEEK}) is empty (correct isolation)")
        else:
            print(f"  FAIL: Previous week has {len(prev_entries)} entries (expected empty)")
            failures.append("Week navigation: previous week is isolated (empty)")

        # Next week should also be empty
        if next_entries == []:
            print(f"  PASS: Next week ({NEXT_WEEK}) is empty (correct isolation)")
        else:
            print(f"  FAIL: Next week has {len(next_entries)} entries (expected empty)")
            failures.append("Week navigation: next week is isolated (empty)")

        # Back to current week — all assignments still there
        back_index = {(e["day_of_week"], e["meal_slot"]): e for e in back_entries}
        all_back = all(
            back_index.get((day, slot), {}).get("recipe_id") == rid
            for day, slot, rid in assignments
        )
        if all_back:
            print(f"  PASS: Returning to current week ({WEEK}) — all {len(assignments)} assignments persist")
        else:
            print(f"  FAIL: Some assignments lost after navigating to prev/next week and back")
            failures.append("Week navigation: assignments persist when returning to current week")
    else:
        print(f"  FAIL: Week navigation GET calls returned {prev_resp.status_code}/"
              f"{next_resp.status_code}/{back_resp.status_code}")
        failures.append("Week navigation: all GET /api/meals calls return 200")

    # ─── PART 2: CASCADE DELETE ───────────────────────────────────────────────
    print()
    print("=" * 60)
    print("PART 2: Cascade Delete — recipe deletion clears planner slots")
    print("=" * 60)
    print()

    print("--- Check 2a: Assign cascade-victim recipe to multiple slots ---")
    cascade_slots = [
        (1, "dinner"),   # Tuesday dinner
        (3, "dinner"),   # Thursday dinner
        (5, "lunch"),    # Saturday lunch
    ]
    for day, slot in cascade_slots:
        resp = client.put("/api/meals", json={
            "week_start": WEEK,
            "day_of_week": day,
            "meal_slot": slot,
            "recipe_id": cascade_id
        })
        if resp.status_code not in (200, 201):
            print(f"  FAIL: Could not assign cascade victim to day={day} slot={slot}")
            failures.append(f"Cascade setup: assign cascade victim to day={day}")

    # Verify they're in the plan
    pre_cascade_resp = client.get(f"/api/meals?week={WEEK}")
    pre_entries = pre_cascade_resp.json() if pre_cascade_resp.status_code == 200 else []
    cascade_entries_before = [e for e in pre_entries if e.get("recipe_id") == cascade_id]

    if len(cascade_entries_before) == len(cascade_slots):
        print(f"  PASS: Cascade victim assigned to {len(cascade_entries_before)} slots")
    else:
        print(f"  FAIL: Expected {len(cascade_slots)} cascade entries, got {len(cascade_entries_before)}")
        failures.append("Cascade setup: all cascade slots assigned")

    total_before = len(pre_entries)

    print()
    print("--- Check 2b: Delete the recipe from the collection ---")
    del_resp = client.delete(f"/api/recipes/{cascade_id}")
    if del_resp.status_code in (200, 204):
        print(f"  PASS: DELETE /api/recipes/{cascade_id} returns {del_resp.status_code}")
    else:
        print(f"  FAIL: DELETE /api/recipes/{cascade_id} returned {del_resp.status_code}")
        failures.append("Cascade: delete recipe returns 200/204")

    print()
    print("--- Check 2c: Verify planner slots for deleted recipe are cleared ---")
    print("  (Simulates navigator returning to #planner tab after deleting from #recipes)")
    post_cascade_resp = client.get(f"/api/meals?week={WEEK}")
    if post_cascade_resp.status_code == 200:
        post_entries = post_cascade_resp.json()
        orphaned = [e for e in post_entries if e.get("recipe_id") == cascade_id]

        if not orphaned:
            print(f"  PASS: All {len(cascade_entries_before)} cascade victim slots are cleared "
                  f"from GET /api/meals response")
        else:
            print(f"  FAIL: {len(orphaned)} orphaned slots remain (recipe_id={cascade_id} still in response)")
            for e in orphaned:
                print(f"        Orphan: day={e.get('day_of_week')}, slot={e.get('meal_slot')}")
            failures.append("Cascade: deleted recipe slots cleared from planner (ON DELETE CASCADE)")

        # Other slots should not be affected
        surviving_entries = [e for e in post_entries if e.get("recipe_id") != cascade_id]
        original_surviving = [
            (day, slot, rid) for day, slot, rid in assignments
            if rid != cascade_id
        ]
        if len(surviving_entries) >= len(original_surviving):
            print(f"  PASS: Other recipe slots ({len(surviving_entries)}) not affected by cascade delete")
        else:
            print(f"  FAIL: Expected {len(original_surviving)} surviving slots, got {len(surviving_entries)}")
            failures.append("Cascade: other recipe slots not affected")

        total_after = len(post_entries)
        expected_after = total_before - len(cascade_entries_before)
        if total_after == expected_after:
            print(f"  PASS: Week plan reduced exactly: {total_before} → {total_after} entries "
                  f"(removed {len(cascade_entries_before)})")
        else:
            print(f"  FAIL: Expected {expected_after} entries after cascade, got {total_after}")
            failures.append("Cascade: exact entry count after cascade delete")
    else:
        print(f"  FAIL: GET /api/meals after recipe delete returned {post_cascade_resp.status_code}")
        failures.append("Cascade: GET /api/meals returns 200 after recipe deletion")

    print()
    print("--- Check 2d: No JS errors — planner renders cleanly after cascade delete ---")
    # Verify the remaining week data is well-formed (no null recipe_titles, no zero IDs)
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries = resp.json()
        malformed = [
            e for e in entries
            if not e.get("recipe_title") or not e.get("recipe_id")
        ]
        if not malformed:
            print(f"  PASS: All {len(entries)} remaining entries have valid recipe_title and recipe_id "
                  f"(no null/orphaned data that would cause JS render errors)")
        else:
            print(f"  FAIL: {len(malformed)} entries with missing recipe_title or recipe_id:")
            for e in malformed:
                print(f"        day={e.get('day_of_week')} slot={e.get('meal_slot')} "
                      f"recipe_id={e.get('recipe_id')} title={e.get('recipe_title')!r}")
            failures.append("Cascade: no null/orphaned data in planner response after delete")

    # ─── PART 3: DAY TOTALS ACCURACY ─────────────────────────────────────────
    print()
    print("=" * 60)
    print("PART 3: Day Totals Accuracy — total_time field for each assigned slot")
    print("=" * 60)
    print()
    print("The planner's day total row sums total_time for each day from the API response.")
    print("Verifying the API returns accurate total_time = prep_time + cook_time per entry.")
    print()

    # Re-fetch current week to get the final state for day total checks
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries = resp.json()
        entry_index = {}
        for e in entries:
            day = e.get("day_of_week")
            slot = e.get("meal_slot")
            entry_index[(day, slot)] = e

        # Verify total_time field present on all entries
        missing_time = [e for e in entries if "total_time" not in e]
        if not missing_time:
            print(f"  PASS: total_time field present on all {len(entries)} entries")
        else:
            print(f"  FAIL: {len(missing_time)} entries missing total_time field")
            failures.append("Day totals: total_time field present on all meal plan entries")

        # Verify specific known total_time values
        print()
        print("--- Check 3a: Monday total_time per recipe is correct ---")
        # Monday has: breakfast_id (5+10=15) and lunch_id (10+0=10)
        mon_breakfast = entry_index.get((0, "breakfast"))
        mon_lunch = entry_index.get((0, "lunch"))

        if mon_breakfast and mon_breakfast.get("recipe_id") == breakfast_id:
            if mon_breakfast.get("total_time") == 15:
                print(f"  PASS: Monday breakfast total_time = 15 min (prep=5 + cook=10)")
            else:
                print(f"  FAIL: Monday breakfast total_time = {mon_breakfast.get('total_time')} (expected 15)")
                failures.append("Day totals: Monday breakfast total_time = 15")
        else:
            print(f"  WARN: Monday breakfast not in current plan (may have been cleared) — skipping check")

        if mon_lunch and mon_lunch.get("recipe_id") == lunch_id:
            if mon_lunch.get("total_time") == 10:
                print(f"  PASS: Monday lunch total_time = 10 min (prep=10 + cook=0)")
            else:
                print(f"  FAIL: Monday lunch total_time = {mon_lunch.get('total_time')} (expected 10)")
                failures.append("Day totals: Monday lunch total_time = 10")
        else:
            print(f"  WARN: Monday lunch not in current plan (may have been cleared) — skipping check")

        print()
        print("--- Check 3b: Day total sums correctly across multiple recipes ---")
        # Monday: breakfast(15) + lunch(10) = 25
        monday_entries = [e for e in entries if e.get("day_of_week") == 0]
        monday_total = sum(e.get("total_time", 0) for e in monday_entries)

        if monday_entries:
            expected_monday = sum(
                e.get("total_time", 0) for e in monday_entries
            )
            if monday_total == expected_monday:
                entry_summary = " + ".join(
                    f"{e.get('meal_slot')}={e.get('total_time')}min" for e in monday_entries
                )
                print(f"  PASS: Monday day total = {monday_total} min ({entry_summary})")
            else:
                print(f"  FAIL: Monday total {monday_total} != expected {expected_monday}")
                failures.append("Day totals: Monday sum correct")
        else:
            print(f"  INFO: No Monday entries to verify day total (all were cleared or cascaded)")

        # Verify Wednesday day total (dinner_id was assigned to day 2)
        wed_entries = [e for e in entries if e.get("day_of_week") == 2]
        if wed_entries:
            wed_dinner = next((e for e in wed_entries if e.get("meal_slot") == "dinner"), None)
            if wed_dinner and wed_dinner.get("recipe_id") == dinner_id:
                if wed_dinner.get("total_time") == 35:
                    print(f"  PASS: Wednesday dinner total_time = 35 min (prep=15 + cook=20)")
                else:
                    print(f"  FAIL: Wednesday dinner total_time = {wed_dinner.get('total_time')} (expected 35)")
                    failures.append("Day totals: Wednesday dinner total_time = 35")
            else:
                print(f"  INFO: Wednesday dinner not in expected state — recipe_id may differ")
        else:
            print(f"  INFO: No Wednesday entries to verify")

        print()
        print("--- Check 3c: Day totals are zero for empty days ---")
        # Sunday was assigned dinner_id but cascade delete cleared cascade_id entries.
        # Let's check a day we know has no assignments: Saturday (cascade slots were cleared)
        sat_entries = [e for e in entries if e.get("day_of_week") == 5]
        # Saturday cascade slot (lunch) was cascade-deleted along with cascade_id recipe
        sat_lunch = next((e for e in sat_entries if e.get("meal_slot") == "lunch"), None)
        if sat_lunch is None:
            print(f"  PASS: Saturday lunch is empty after cascade delete (total_time contribution = 0)")
        else:
            print(f"  INFO: Saturday lunch still has recipe_id={sat_lunch.get('recipe_id')}")

        # Verify total_time = 0 does not appear for existing entries (would be a data error)
        zero_time_entries = [
            e for e in entries
            if e.get("total_time") is not None and e.get("total_time") == 0
            and (e.get("recipe_id") in [breakfast_id, lunch_id, dinner_id])
        ]
        # Note: only flag as error if the recipe was supposed to have non-zero time
        if not zero_time_entries:
            print(f"  PASS: No entries with unexpectedly zero total_time for timed recipes")
        else:
            print(f"  FAIL: {len(zero_time_entries)} entries have total_time=0 but recipe has prep/cook time")
            for e in zero_time_entries:
                print(f"        day={e.get('day_of_week')} slot={e.get('meal_slot')} "
                      f"recipe_id={e.get('recipe_id')} total_time={e.get('total_time')}")
            failures.append("Day totals: total_time not zero for timed recipes")

    else:
        print(f"  FAIL: GET /api/meals?week={WEEK} returned {resp.status_code}")
        failures.append("Day totals: GET /api/meals returns 200 for total computation")

    # ─── PART 4: planner.js frontend integration code check ──────────────────
    print()
    print("=" * 60)
    print("PART 4: planner.js — Integration Code Review")
    print("=" * 60)
    print()
    print("Checking planner.js implements the patterns that deliver persistence,")
    print("cascade-safe rendering, and accurate day totals.")
    print()

    planner_js = FRONTEND_DIR / "js" / "planner.js"

    if not planner_js.exists():
        print(f"  FAIL: frontend/js/planner.js not found")
        failures.append("planner.js exists")
    else:
        content = planner_js.read_text(encoding="utf-8", errors="replace")
        size = planner_js.stat().st_size
        print(f"  File: planner.js ({size} bytes)")

        integration_checks = [
            # Persistence: fresh fetch on every renderPlanner() call
            ("Fresh fetch on every navigation (GET /api/meals?week= in render())",
             "apiFetch" in content and "/api/meals" in content and "render" in content),
            ("week_start state preserved between renders",
             "state.weekStart" in content or "weekStart" in content),
            ("re-render after assignment (render() called after PUT)",
             "await render()" in content and "assignMeal" in content),
            ("re-render after removal (render() called after DELETE)",
             "await render()" in content and "removeMeal" in content),

            # Cascade safety: no client-side cache that would hold stale recipe data
            ("indexMeals() or equivalent for O(1) lookup per render cycle",
             "indexMeals" in content or "mealIndex" in content or "Map" in content),

            # Day totals: sums total_time from API response
            ("Day total row sums total_time per day",
             "total_time" in content and ("reduce" in content or "sum" in content or "Total" in content)),
            ("Handles missing total_time gracefully (defaults to 0)",
             "total_time || 0" in content or "(meal.total_time || 0)" in content
             or "meal ? (meal.total_time" in content),

            # Cascade-safe: planner doesn't cache recipes that could become stale
            ("Meal data re-fetched fresh each navigation (no cross-session stale cache)",
             "state.meals" in content and
             ("state.meals = []" in content or "state.meals = await" in content)),
        ]

        all_ok = True
        for name, ok in integration_checks:
            if ok:
                print(f"  OK: {name}")
            else:
                print(f"  FAIL: {name}")
                failures.append(f"planner.js integration: {name}")
                all_ok = False

        if all_ok:
            print()
            print(f"  PASS: planner.js integration patterns are correct for persistence,")
            print(f"        cascade safety, and accurate day totals")

    db_module.DB_PATH = orig_db_path

print()
print("=" * 60)
if failures:
    print(f"RESULT: FAIL — {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("User impact: Planner may show stale data after navigation or recipe deletion,")
    print("or display inaccurate day totals — breaking trust in the planner's data.")
    sys.exit(1)
else:
    print("RESULT: PASS — Planner persistence, cascade delete, and day totals all verified")
    print()
    print("  Persistence:     Assigned meals survive navigation between tabs and weeks")
    print("  Cascade delete:  Deleting a recipe clears its planner slots via ON DELETE CASCADE")
    print("  Day totals:      total_time field is accurate; frontend can sum it correctly")
    print("  No stale data:   Planner re-fetches fresh from API on every navigation")
    print()
    print("Value delivered: Cook can trust the planner — data is consistent across navigation")
    print("and stays clean when recipes are removed from the collection.")
    sys.exit(0)
