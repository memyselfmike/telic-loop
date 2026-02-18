#!/usr/bin/env python3
"""
Verification: Planner frontend view — API ready, JS implementation status
PRD Reference: Section 4.2 (Weekly Meal Planner), Section 3.2 (Meal Plan API)
Vision Goal: "Plan Meals for the Week" — 7-day grid, meal slots, week navigation, day totals
Category: unit

This script has TWO purposes:
1. Confirm the meal plan BACKEND API is fully functional (regression guard)
2. Check whether the planner.js FRONTEND has been implemented beyond stub status

The planner.js view must implement (per task E1-6+ scope):
- A 7-column grid (Mon-Sun) with 4 meal slot rows
- Recipe picker (searchable list from collection)
- Week navigation (prev/next arrows, "This Week" button)
- Day summary row (total prep+cook time)
- Slot assignment, clearing, swapping

Currently planner.js is a stub ("Meal Planner Coming Soon" placeholder).
This script FAILS on the frontend check until the planner view is built.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== UNIT: Planner Frontend — API Integrity + JS Implementation Status ===")
print("PRD: Section 4.2 — 7-day grid, slot assignment, week navigation")
print()

failures = []
warnings = []

# ─── PART 1: Planner API backend regression guard ──────────────────────────

print("=" * 55)
print("PART 1: Meal Plan API — Backend Regression Guard")
print("=" * 55)

try:
    from fastapi.testclient import TestClient
    import database as db_module
    from main import app
except ImportError as e:
    print(f"FAIL: Cannot import backend: {e}")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "planner_check.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db
    asyncio.run(db_module.init_db())
    client = TestClient(app)

    WEEK = "2026-02-16"  # A Monday

    # Check 1: GET /api/meals?week= returns list
    print()
    print("--- API Check 1: GET /api/meals?week= returns 200 with list ---")
    resp = client.get(f"/api/meals?week={WEEK}")
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list):
            print(f"  PASS: GET /api/meals?week={WEEK} returns list ({len(data)} entries for empty week)")
        else:
            print(f"  FAIL: Response is not a list: {type(data)}")
            failures.append("GET /api/meals returns JSON list")
    else:
        print(f"  FAIL: GET /api/meals returned {resp.status_code}")
        failures.append(f"GET /api/meals?week= returns 200 (got {resp.status_code})")

    # Check 2: PUT /api/meals assigns recipe to slot
    print()
    print("--- API Check 2: PUT /api/meals assigns recipe to slot ---")
    # Use a seed recipe (id=1 should exist after init_db)
    seeds_resp = client.get("/api/recipes")
    seeds = seeds_resp.json() if seeds_resp.status_code == 200 else []
    if seeds:
        seed_id = seeds[0]["id"]
        assign_resp = client.put("/api/meals", json={
            "week_start": WEEK,
            "day_of_week": 0,  # Monday
            "meal_slot": "dinner",
            "recipe_id": seed_id
        })
        if assign_resp.status_code in (200, 201):
            entry = assign_resp.json()
            has_title = bool(entry.get("recipe_title"))
            has_time = "total_time" in entry or "prep_time_minutes" in entry
            if has_title:
                print(f"  PASS: PUT /api/meals returns entry with recipe_title='{entry.get('recipe_title')}'")
            else:
                print(f"  FAIL: Entry missing recipe_title field: {entry}")
                failures.append("PUT /api/meals response includes recipe_title")
        else:
            print(f"  FAIL: PUT /api/meals returned {assign_resp.status_code}: {assign_resp.text[:200]}")
            failures.append("PUT /api/meals returns 200 or 201")
    else:
        print(f"  WARN: No seed recipes found — skipping PUT check")
        warnings.append("No seed recipes to assign for PUT check")

    # Check 3: GET /api/meals returns assigned entry with total_time
    print()
    print("--- API Check 3: GET /api/meals returns entries with recipe_title and total_time ---")
    week_resp = client.get(f"/api/meals?week={WEEK}")
    if week_resp.status_code == 200:
        entries = week_resp.json()
        if entries:
            entry = entries[0]
            has_recipe_title = bool(entry.get("recipe_title"))
            has_total_time = "total_time" in entry
            if has_recipe_title and has_total_time:
                print(f"  PASS: Entry has recipe_title='{entry['recipe_title']}', total_time={entry.get('total_time')}")
            else:
                missing = []
                if not has_recipe_title:
                    missing.append("recipe_title")
                if not has_total_time:
                    missing.append("total_time")
                print(f"  FAIL: Entry missing fields: {missing}")
                failures.append(f"Meal plan entry includes fields: {missing}")
        else:
            print(f"  FAIL: Week is empty after assignment")
            failures.append("GET /api/meals returns assigned entry")
    else:
        print(f"  FAIL: GET /api/meals returned {week_resp.status_code}")
        failures.append("GET /api/meals after assignment returns 200")

    # Check 4: Different week is independent
    print()
    print("--- API Check 4: Different weeks are independent ---")
    other_week = "2026-02-23"
    other_resp = client.get(f"/api/meals?week={other_week}")
    if other_resp.status_code == 200:
        other_entries = other_resp.json()
        if not other_entries:
            print(f"  PASS: Week {other_week} is independent (empty)")
        else:
            print(f"  FAIL: Week {other_week} has {len(other_entries)} entries (should be empty)")
            failures.append("Different weeks are independent")
    else:
        print(f"  FAIL: GET /api/meals for other week returned {other_resp.status_code}")
        failures.append("GET /api/meals for different week returns 200")

    # Check 5: DELETE /api/meals/{id} clears slot
    print()
    print("--- API Check 5: DELETE /api/meals/{id} clears a slot ---")
    week_resp2 = client.get(f"/api/meals?week={WEEK}")
    if week_resp2.status_code == 200 and week_resp2.json():
        entry_id = week_resp2.json()[0]["id"]
        del_resp = client.delete(f"/api/meals/{entry_id}")
        if del_resp.status_code in (200, 204):
            # Verify slot is cleared
            verify_resp = client.get(f"/api/meals?week={WEEK}")
            remaining = verify_resp.json() if verify_resp.status_code == 200 else []
            if not remaining:
                print(f"  PASS: DELETE cleared slot — week now empty")
            else:
                print(f"  FAIL: Slot still has entries after DELETE")
                failures.append("DELETE /api/meals/{id} clears slot")
        else:
            print(f"  FAIL: DELETE /api/meals/{entry_id} returned {del_resp.status_code}")
            failures.append("DELETE /api/meals/{id} returns 200 or 204")
    else:
        print(f"  WARN: No entry to delete (week empty or GET failed)")

    db_module.DB_PATH = orig_db_path

# ─── PART 2: planner.js frontend implementation check ─────────────────────

print()
print("=" * 55)
print("PART 2: planner.js — Frontend Implementation Status")
print("=" * 55)

planner_js = Path(SPRINT_DIR) / "frontend" / "js" / "planner.js"
print()

if not planner_js.exists():
    print(f"  FAIL: frontend/js/planner.js does not exist")
    failures.append("frontend/js/planner.js exists")
else:
    content = planner_js.read_text(encoding="utf-8", errors="replace")
    size = planner_js.stat().st_size
    print(f"  File: frontend/js/planner.js ({size} bytes)")

    # Stub detection: use unambiguous phrases only. "placeholder" is a valid HTML attribute
    # in real implementations (e.g., placeholder: 'Search recipes...'), so exclude it.
    # Also treat files < 3000 bytes as stubs (true implementations are much larger).
    is_stub = (
        "coming soon" in content.lower()
        or "not yet implemented" in content.lower()
        or size < 3000
    )

    if is_stub:
        print(f"  STATUS: STUB — planner.js is a placeholder, full implementation pending")
        print()
        # Check for minimum stub requirements (navigation works)
        has_render_planner = "renderPlanner" in content
        if has_render_planner:
            print(f"  OK: renderPlanner() function defined (navigation won't break)")
        else:
            print(f"  FAIL: renderPlanner() not defined — navigation to #planner will error")
            failures.append("planner.js defines renderPlanner()")

        # List what's missing from the full implementation
        required_features = [
            ("7-day grid", "mon" in content.lower() or "sun" in content.lower() or "day_of_week" in content),
            ("meal slots", "meal_slot" in content or "breakfast" in content.lower()),
            ("week navigation", "prev" in content.lower() or "week_start" in content or "navigation" in content.lower()),
            ("day time totals", "total_time" in content or "prep_time" in content),
            ("recipe picker", "recipe_id" in content or "picker" in content.lower()),
            ("PUT /api/meals call", "/api/meals" in content and "put" in content.lower()),
            ("DELETE meal slot", "delete" in content.lower() and "meal" in content.lower()),
        ]

        missing = [name for name, found in required_features if not found]
        present = [name for name, found in required_features if found]

        if missing:
            print()
            print(f"  Missing features ({len(missing)}/{len(required_features)}):")
            for m in missing:
                print(f"    MISSING: {m}")
            failures.append(f"planner.js implements full weekly planner UI (missing: {', '.join(missing)})")
        if present:
            print()
            print(f"  Present features:")
            for p in present:
                print(f"    OK: {p}")
    else:
        # Full implementation — check all required features
        print(f"  STATUS: Implementation present — checking required features")
        print()

        checks = [
            ("renderPlanner() entry point", "renderPlanner" in content),
            ("7-day grid (Mon-Sun)", any(d in content.lower() for d in ["monday", "sunday", "mon-sun", "day_of_week", "days of"])),
            ("meal slots (breakfast/lunch/dinner/snack)", any(s in content for s in ["breakfast", "lunch", "dinner", "snack"])),
            ("week navigation (prev/next/this week)", any(w in content.lower() for w in ["prev", "next week", "this week", "week_start"])),
            ("day time totals", any(t in content for t in ["total_time", "prep_time", "cook_time"])),
            ("GET /api/meals", "GET" in content and "/api/meals" in content or "apiFetch('/api/meals" in content or 'apiFetch("/api/meals' in content),
            ("PUT /api/meals (assign recipe)", "PUT" in content and "/api/meals" in content or "'PUT'" in content or '"PUT"' in content),
            ("DELETE /api/meals (clear slot)", "DELETE" in content and "/api/meals" in content),
            ("Recipe picker / searchable list", any(p in content.lower() for p in ["picker", "recipe_id", "search", "pick recipe"])),
        ]

        all_ok = True
        for name, ok in checks:
            if ok:
                print(f"  OK: {name}")
            else:
                print(f"  FAIL: {name}")
                failures.append(f"planner.js: {name}")
                all_ok = False

        if all_ok:
            print()
            print(f"  PASS: planner.js has all required weekly planner features")

print()
print("=" * 55)
print("SUMMARY")
print("=" * 55)

if failures:
    print(f"\nFailed ({len(failures)}):")
    for f in failures:
        print(f"  FAIL: {f}")
    print()
    print("RESULT: FAIL")
    print()
    print("User impact: Cook cannot open the Weekly Meal Planner view and plan their week.")
    print("The planner.js frontend needs to be implemented (currently a stub).")
    sys.exit(1)
else:
    print()
    print("RESULT: PASS — Planner API and frontend both operational")
    print("Value delivered: Cook can plan meals across 7 days through the weekly planner view.")
    sys.exit(0)
