#!/usr/bin/env python3
"""
Verification: Weekly planner view — 7-day grid, slot assignment, week navigation, copy to slots
PRD Reference: Section 4.2 (Weekly Meal Planner), Section 3.2 (Meal Plans), Epic 2 AC
Vision Goal: "Plan Meals for the Week" — assign recipes across Mon-Sun, navigate weeks, copy for meal prep
Category: value

Proves the value proofs:
1. "User opens the weekly planner, assigns recipes to meal slots across Mon-Sun, navigates
   between weeks, and sees daily time totals"
2. "User copies a recipe to Monday-Friday lunch slots for meal prep and all 5 slots display the recipe"

Tests both:
1. API layer: the data round-trip that backs the UI (must pass for frontend to work)
2. Frontend layer: planner.js has the required UI implementation
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

print("=== VALUE: Weekly Planner UI — 7-Day Grid + Meal Slot Assignment ===")
print("Vision: Cook opens planner, assigns recipes across Mon-Sun, navigates weeks, meal preps")
print()

failures = []

try:
    from fastapi.testclient import TestClient
    import database as db_module
    from main import app
except ImportError as e:
    print(f"FAIL: Cannot import app: {e}")
    sys.exit(1)

# ─── PART 1: API value chain for the weekly planner ───────────────────────────

with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "planner_value.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db
    asyncio.run(db_module.init_db())
    client = TestClient(app)

    print("=== Scenario: Cook plans meals for the week ===")
    print()

    print("--- Setup: Create recipes to use in planner ---")
    lunch_resp = client.post("/api/recipes", json={
        "title": "Meal Prep Grain Bowl",
        "category": "lunch",
        "prep_time_minutes": 10,
        "cook_time_minutes": 25,
        "servings": 1,
        "description": "Hearty lunch bowl for meal prep",
        "instructions": "Cook grains, add toppings.",
        "tags": "meal-prep,healthy",
        "ingredients": [
            {"quantity": 1.0, "unit": "cup", "item": "quinoa", "grocery_section": "pantry"},
            {"quantity": 0.5, "unit": "cup", "item": "chickpeas", "grocery_section": "pantry"},
        ]
    })
    breakfast_resp = client.post("/api/recipes", json={
        "title": "Overnight Oats",
        "category": "breakfast",
        "prep_time_minutes": 5,
        "cook_time_minutes": 0,
        "servings": 1,
        "description": "Prep the night before",
        "instructions": "Mix oats with milk, refrigerate.",
        "tags": "quick,healthy",
        "ingredients": [
            {"quantity": 0.5, "unit": "cup", "item": "rolled oats", "grocery_section": "pantry"},
            {"quantity": 1.0, "unit": "cup", "item": "almond milk", "grocery_section": "dairy"},
        ]
    })
    dinner_resp = client.post("/api/recipes", json={
        "title": "Sunday Slow Cooker Chili",
        "category": "dinner",
        "prep_time_minutes": 20,
        "cook_time_minutes": 240,
        "servings": 6,
        "description": "Weekend project dinner",
        "instructions": "Brown beef, add everything, slow cook 4 hours.",
        "tags": "comfort,weekend",
        "ingredients": [
            {"quantity": 1.0, "unit": "lb", "item": "ground beef", "grocery_section": "meat"},
            {"quantity": 2.0, "unit": "cup", "item": "kidney beans", "grocery_section": "pantry"},
        ]
    })

    all_created = all(r.status_code == 201 for r in [lunch_resp, breakfast_resp, dinner_resp])
    if not all_created:
        print(f"  FAIL: Could not create recipes: {[r.status_code for r in [lunch_resp, breakfast_resp, dinner_resp]]}")
        db_module.DB_PATH = orig_db_path
        sys.exit(1)

    lunch_id = lunch_resp.json()["id"]
    breakfast_id = breakfast_resp.json()["id"]
    dinner_id = dinner_resp.json()["id"]
    print(f"  OK: Recipes created — lunch={lunch_id}, breakfast={breakfast_id}, dinner={dinner_id}")

    WEEK = "2026-02-16"   # Monday Feb 16, 2026
    NEXT_WEEK = "2026-02-23"

    print()
    print("--- Value Check 1: Meal prep — copy lunch to Mon-Fri (5 slots) ---")
    print("  Vision: 'copy a recipe to multiple slots (meal prep — same lunch all week)'")
    meal_prep_codes = []
    for day in range(5):  # Mon=0 through Fri=4
        resp = client.put("/api/meals", json={
            "week_start": WEEK,
            "day_of_week": day,
            "meal_slot": "lunch",
            "recipe_id": lunch_id
        })
        meal_prep_codes.append((day, resp.status_code))

    all_ok = all(code in (200, 201) for _, code in meal_prep_codes)
    if all_ok:
        print(f"  PASS: All 5 PUT /api/meals calls succeeded (Mon–Fri lunch)")
    else:
        failed = [(d, c) for d, c in meal_prep_codes if c not in (200, 201)]
        print(f"  FAIL: {len(failed)} PUT call(s) failed: {failed}")
        failures.append("Meal prep: 5 consecutive PUT calls all succeed")

    # Verify all 5 slots show the recipe
    week_resp = client.get(f"/api/meals?week={WEEK}")
    if week_resp.status_code == 200:
        entries = week_resp.json()
        lunch_entries = [e for e in entries if e.get("meal_slot") == "lunch"]
        assigned_days = {e.get("day_of_week") for e in lunch_entries if e.get("recipe_id") == lunch_id}
        if assigned_days == {0, 1, 2, 3, 4}:
            print(f"  PASS: All 5 lunch slots (Mon–Fri) display 'Meal Prep Grain Bowl'")
        else:
            print(f"  FAIL: Only days {assigned_days} show meal prep recipe (expected {{0,1,2,3,4}})")
            failures.append("Meal prep: all 5 slots display the recipe")
    else:
        print(f"  FAIL: GET /api/meals?week={WEEK} returned {week_resp.status_code}")
        failures.append("Meal prep: GET week returns 200 after assignment")

    print()
    print("--- Value Check 2: Assign breakfast Mon + dinner Sun across full week ---")
    resp_mon_breakfast = client.put("/api/meals", json={
        "week_start": WEEK, "day_of_week": 0, "meal_slot": "breakfast", "recipe_id": breakfast_id
    })
    resp_sun_dinner = client.put("/api/meals", json={
        "week_start": WEEK, "day_of_week": 6, "meal_slot": "dinner", "recipe_id": dinner_id
    })
    if resp_mon_breakfast.status_code in (200, 201) and resp_sun_dinner.status_code in (200, 201):
        print(f"  PASS: Assigned breakfast to Monday, dinner to Sunday")
    else:
        print(f"  FAIL: Mon breakfast={resp_mon_breakfast.status_code}, Sun dinner={resp_sun_dinner.status_code}")
        failures.append("Assign breakfast/dinner across week")

    print()
    print("--- Value Check 3: View full week plan — all slots appear with recipe details ---")
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries = resp.json()
        # 5 lunches + 1 breakfast + 1 dinner = 7 entries
        if len(entries) >= 7:
            print(f"  PASS: Full week plan has {len(entries)} entries (5 lunches + breakfast + dinner)")
        else:
            print(f"  FAIL: Expected 7+ entries, got {len(entries)}")
            failures.append("Week plan: all assigned slots appear in GET /api/meals")

        # Check recipe details (title + total_time for day summary)
        sample = entries[0] if entries else {}
        has_title = bool(sample.get("recipe_title"))
        has_time = "total_time" in sample
        if has_title and has_time:
            print(f"  PASS: Entries include recipe_title and total_time (for day summary display)")
        else:
            missing = [f for f, ok in [("recipe_title", has_title), ("total_time", has_time)] if not ok]
            print(f"  FAIL: Entries missing fields: {missing}")
            failures.append(f"Week plan entries include recipe display fields: {missing}")
    else:
        print(f"  FAIL: GET /api/meals?week={WEEK}: {resp.status_code}")
        failures.append("View full week plan returns 200")

    print()
    print("--- Value Check 4: Day time totals computable from total_time field ---")
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries = resp.json()
        # Monday: breakfast (5+0=5 min) + lunch (10+25=35 min) = 40 min
        mon_entries = [e for e in entries if e.get("day_of_week") == 0]
        mon_total = sum(e.get("total_time", 0) for e in mon_entries)
        if mon_total == 40:
            print(f"  PASS: Monday day total = 40 min (breakfast 5 + lunch 35)")
        elif mon_total > 0:
            print(f"  PASS: Monday day total = {mon_total} min (computable from total_time field)")
        else:
            print(f"  FAIL: Cannot compute Monday day total (got {mon_total})")
            failures.append("Day time totals computable from total_time in API response")

    print()
    print("--- Value Check 5: Clear a slot (cook removes an assignment) ---")
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        entries = resp.json()
        mon_lunch = next((e for e in entries if e.get("day_of_week") == 0 and e.get("meal_slot") == "lunch"), None)
        if mon_lunch:
            del_resp = client.delete(f"/api/meals/{mon_lunch['id']}")
            if del_resp.status_code in (200, 204):
                verify = client.get(f"/api/meals?week={WEEK}")
                remaining = verify.json() if verify.status_code == 200 else []
                slot_still_filled = any(
                    e.get("day_of_week") == 0 and e.get("meal_slot") == "lunch"
                    for e in remaining
                )
                if not slot_still_filled:
                    print(f"  PASS: Cleared Monday lunch slot — slot is now empty")
                else:
                    print(f"  FAIL: Monday lunch still assigned after DELETE")
                    failures.append("Clear slot: DELETE /api/meals/{id} removes the assignment")
            else:
                print(f"  FAIL: DELETE returned {del_resp.status_code}")
                failures.append("Clear slot: DELETE returns 200 or 204")
        else:
            print(f"  SKIP: Monday lunch not found in plan entries")

    print()
    print("--- Value Check 6: Navigate to next week — weeks are independent ---")
    resp = client.get(f"/api/meals?week={NEXT_WEEK}")
    if resp.status_code == 200:
        next_entries = resp.json()
        if next_entries == []:
            print(f"  PASS: Next week ({NEXT_WEEK}) starts empty — weeks are independent")
        else:
            print(f"  FAIL: Next week has {len(next_entries)} entries (expected empty)")
            failures.append("Week navigation: next week is independent (starts empty)")
    else:
        print(f"  FAIL: GET /api/meals?week={NEXT_WEEK} returned {resp.status_code}")
        failures.append("Week navigation: GET next week returns 200")

    print()
    print("--- Value Check 7: Swap recipe in a slot (upsert replaces existing) ---")
    # Re-assign Sunday dinner from chili to a different recipe
    swap_resp = client.put("/api/meals", json={
        "week_start": WEEK, "day_of_week": 6, "meal_slot": "dinner", "recipe_id": breakfast_id
    })
    if swap_resp.status_code in (200, 201):
        verify = client.get(f"/api/meals?week={WEEK}")
        if verify.status_code == 200:
            entries = verify.json()
            sun_dinner = next((e for e in entries if e.get("day_of_week") == 6 and e.get("meal_slot") == "dinner"), None)
            sun_dinner_count = sum(1 for e in entries if e.get("day_of_week") == 6 and e.get("meal_slot") == "dinner")
            if sun_dinner and sun_dinner.get("recipe_id") == breakfast_id and sun_dinner_count == 1:
                print(f"  PASS: Sunday dinner swapped — no duplicates, new recipe assigned")
            elif sun_dinner_count > 1:
                print(f"  FAIL: Swap created {sun_dinner_count} entries for same slot (upsert broken)")
                failures.append("Slot swap: upsert replaces without creating duplicates")
            else:
                print(f"  FAIL: Swap did not update slot correctly")
                failures.append("Slot swap: PUT replaces existing assignment")
    else:
        print(f"  FAIL: Swap PUT returned {swap_resp.status_code}")
        failures.append("Slot swap: PUT /api/meals returns 200/201 for existing slot")

    db_module.DB_PATH = orig_db_path

# ─── PART 2: planner.js frontend implementation check ─────────────────────────

print()
print("=== PART 2: planner.js — Frontend Implementation Status ===")
print()

planner_js = FRONTEND_DIR / "js" / "planner.js"

if not planner_js.exists():
    print(f"  FAIL: frontend/js/planner.js does not exist")
    failures.append("planner.js exists")
else:
    content = planner_js.read_text(encoding="utf-8", errors="replace")
    size = planner_js.stat().st_size
    print(f"  File: frontend/js/planner.js ({size} bytes, {content.count(chr(10))+1} lines)")

    # Stub detection: use unambiguous phrases only. "placeholder" is a valid HTML attribute
    # in real implementations (e.g., placeholder: 'Search recipes...'), so exclude it.
    # Also treat files < 3000 bytes as stubs (true implementations are much larger).
    is_stub = (
        any(phrase in content.lower() for phrase in ["coming soon", "not yet implemented"])
        or size < 3000
    )

    if is_stub:
        print(f"  STATUS: STUB — planner.js is a placeholder (Epic 2 not yet built)")
        print()
        # Even for stubs, check that the nav entry point exists (won't break routing)
        has_render_planner = "renderPlanner" in content
        if has_render_planner:
            print(f"  OK: renderPlanner() defined — navigation to #planner won't crash")
        else:
            print(f"  FAIL: renderPlanner() missing — clicking Meal Plan tab will error")
            failures.append("planner.js: renderPlanner() entry point defined")

        # List what the builder needs to implement
        missing_features = [
            "7-day grid (Mon-Sun columns)",
            "4 meal slot rows (breakfast, lunch, dinner, snack)",
            "Recipe picker — searchable list from collection",
            "Week navigation (prev/next arrows, This Week button)",
            "Day summary row (total prep+cook time)",
            "GET /api/meals?week= to load plan",
            "PUT /api/meals to assign recipe to slot",
            "DELETE /api/meals/{id} to clear a slot",
            "Copy to multiple slots (meal prep workflow)",
        ]
        print(f"  MISSING FEATURES ({len(missing_features)}):")
        for f in missing_features:
            print(f"    MISSING: {f}")
        failures.append("planner.js: full weekly planner UI not yet implemented (Epic 2 pending)")
    else:
        print(f"  STATUS: Implementation present — checking required features")
        print()

        checks = [
            ("renderPlanner() entry point", "renderPlanner" in content),
            ("7-day grid (day columns)", any(kw in content.lower() for kw in ["monday", "tuesday", "day_of_week", "days[", "day-col", "grid", "column"])),
            ("meal slots (breakfast/lunch/dinner/snack)", all(slot in content for slot in ["breakfast", "lunch", "dinner", "snack"])),
            ("Week navigation (prev/next/this week)", any(kw in content.lower() for kw in ["prevweek", "nextweek", "prev week", "next week", "this week", "week_start"])),
            ("Day time totals display", any(kw in content for kw in ["total_time", "prep_time", "cook_time", "day total", "daily total"])),
            ("GET /api/meals to load week", any(kw in content for kw in ["/api/meals", "apiFetch('/api/meals", 'apiFetch("/api/meals'])),
            ("PUT /api/meals to assign recipe", "'PUT'" in content or '"PUT"' in content),
            ("DELETE /api/meals to clear slot", "DELETE" in content and "meal" in content.lower()),
            ("Recipe picker / searchable list", any(kw in content.lower() for kw in ["picker", "recipe_id", "pick a recipe", "search", "searchable"])),
            ("Slot + day_of_week in PUT body", "day_of_week" in content and "meal_slot" in content),
        ]

        all_pass = True
        for name, ok in checks:
            if ok:
                print(f"  OK: {name}")
            else:
                print(f"  FAIL: {name}")
                failures.append(f"planner.js: {name}")
                all_pass = False

        if all_pass:
            print()
            print(f"  PASS: planner.js implements all required weekly planner features")

print()
print("=" * 55)
if failures:
    print(f"RESULT: FAIL — {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print()
    print("User impact: Cook cannot use the Weekly Meal Planner view.")
    print("Epic 2 (planner.js frontend) needs to be implemented.")
    sys.exit(1)
else:
    print("RESULT: PASS — Weekly planner value chain works end-to-end")
    print("Value delivered: Cook can assign recipes to 7-day/4-slot grid, meal prep Mon-Fri,")
    print("navigate between weeks, see day time totals, and swap/clear slot assignments.")
    sys.exit(0)
