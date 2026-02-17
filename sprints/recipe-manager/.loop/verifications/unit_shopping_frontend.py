#!/usr/bin/env python3
"""
Verification: Shopping list frontend view — API ready, JS implementation status
PRD Reference: Section 4.3 (Shopping List), Section 3.3 (Shopping API)
Vision Goal: "Generate a Shopping List" — generate, check items, add manual, persists
Category: unit

This script has TWO purposes:
1. Confirm the shopping list BACKEND API passes full regression (kill criterion area)
2. Check whether the shopping.js FRONTEND has been implemented beyond stub status

The shopping.js view must implement (per task E1-6+ scope):
- "Generate from This Week" button (with confirmation if list exists)
- Items grouped by grocery section with section headers
- Checkbox per item (checked moves to bottom, strikethrough)
- "Add Item" input for manual additions
- Item count summary ("12 items, 5 checked")

Currently shopping.js is a stub ("Shopping List Coming Soon" placeholder).
This script FAILS on the frontend check until the shopping view is built.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== UNIT: Shopping Frontend — API Integrity + JS Implementation Status ===")
print("PRD: Section 4.3 — Generate list, check items, add manual items, persist state")
print()

failures = []
warnings = []

# ─── PART 1: Shopping API backend regression guard ─────────────────────────

print("=" * 55)
print("PART 1: Shopping List API — Backend Regression Guard")
print("=" * 55)

try:
    from fastapi.testclient import TestClient
    import database as db_module
    from main import app
except ImportError as e:
    print(f"FAIL: Cannot import backend: {e}")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmpdir:
    test_db = Path(tmpdir) / "shopping_check.db"
    orig_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db
    asyncio.run(db_module.init_db())
    client = TestClient(app)

    WEEK = "2026-02-16"

    print()
    print("--- Setup: Create recipe + meal plan for shopping generation ---")
    recipe_resp = client.post("/api/recipes", json={
        "title": "Test Recipe for Shopping",
        "category": "dinner",
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "servings": 4,
        "description": "", "instructions": "", "tags": "",
        "ingredients": [
            {"quantity": 1.0, "unit": "lb", "item": "ground beef", "grocery_section": "meat"},
            {"quantity": 2.0, "unit": "cup", "item": "mixed vegetables", "grocery_section": "produce"},
            {"quantity": 1.0, "unit": "tbsp", "item": "garlic powder", "grocery_section": "pantry"},
        ]
    })
    if recipe_resp.status_code != 201:
        print(f"FAIL: Could not create recipe: {recipe_resp.status_code}")
        sys.exit(1)

    recipe_id = recipe_resp.json()["id"]
    assign_resp = client.put("/api/meals", json={
        "week_start": WEEK, "day_of_week": 0, "meal_slot": "dinner", "recipe_id": recipe_id
    })
    if assign_resp.status_code not in (200, 201):
        print(f"FAIL: Could not assign recipe: {assign_resp.status_code}")
        sys.exit(1)
    print(f"  OK: Recipe assigned to Mon dinner (week {WEEK})")

    print()
    print("--- API Check 1: GET /api/shopping/current returns 404 when no list exists ---")
    resp = client.get("/api/shopping/current")
    if resp.status_code == 404:
        print(f"  PASS: GET /api/shopping/current returns 404 when no list")
    else:
        print(f"  FAIL: Expected 404, got {resp.status_code}")
        failures.append("GET /api/shopping/current returns 404 when no list")

    print()
    print("--- API Check 2: POST /api/shopping/generate creates list from meal plan ---")
    gen_resp = client.post("/api/shopping/generate", json={"week_start": WEEK})
    if gen_resp.status_code in (200, 201):
        print(f"  PASS: POST /api/shopping/generate returns {gen_resp.status_code}")
    else:
        print(f"  FAIL: Generate returned {gen_resp.status_code}: {gen_resp.text[:200]}")
        failures.append("POST /api/shopping/generate returns 200 or 201")

    print()
    print("--- API Check 3: GET /api/shopping/current returns items after generate ---")
    list_resp = client.get("/api/shopping/current")
    if list_resp.status_code == 200:
        data = list_resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if items:
            print(f"  PASS: Shopping list has {len(items)} item(s)")
            # Verify structure
            first = items[0]
            required_fields = ["id", "item", "quantity", "unit", "grocery_section", "checked"]
            missing_fields = [f for f in required_fields if f not in first]
            if not missing_fields:
                print(f"  PASS: Item has all required fields: {required_fields}")
            else:
                print(f"  FAIL: Item missing fields: {missing_fields}")
                failures.append(f"Shopping item has required fields (missing: {missing_fields})")
        else:
            print(f"  FAIL: Shopping list has no items after generate")
            failures.append("Shopping list has items after generate")
    else:
        print(f"  FAIL: GET /api/shopping/current returned {list_resp.status_code}")
        failures.append("GET /api/shopping/current returns 200 after generate")
        items = []

    print()
    print("--- API Check 4: PATCH /api/shopping/items/{id} toggles checked state ---")
    if items:
        item_id = items[0]["id"]
        original_checked = items[0].get("checked", 0)
        patch_resp = client.patch(f"/api/shopping/items/{item_id}", json={"checked": 1 - original_checked})
        if patch_resp.status_code == 200:
            updated = patch_resp.json()
            new_checked = updated.get("checked")
            if new_checked != original_checked:
                print(f"  PASS: Checked toggled {original_checked} -> {new_checked}")
            else:
                print(f"  FAIL: Checked state unchanged after PATCH")
                failures.append("PATCH /api/shopping/items/{id} toggles checked")
        else:
            print(f"  FAIL: PATCH returned {patch_resp.status_code}")
            failures.append("PATCH /api/shopping/items/{id} returns 200")

    print()
    print("--- API Check 5: POST /api/shopping/items adds manual item ---")
    add_resp = client.post("/api/shopping/items", json={
        "item": "dish soap",
        "quantity": 1.0,
        "unit": "bottle",
        "grocery_section": "other",
        "source": "manual"
    })
    if add_resp.status_code in (200, 201):
        manual_item = add_resp.json()
        print(f"  PASS: Manual item added — id={manual_item.get('id')}, section='{manual_item.get('grocery_section')}'")
    else:
        print(f"  FAIL: POST /api/shopping/items returned {add_resp.status_code}")
        failures.append("POST /api/shopping/items adds manual item")

    print()
    print("--- API Check 6: DELETE /api/shopping/items/{id} removes an item ---")
    if items:
        del_id = items[0]["id"]
        del_resp = client.delete(f"/api/shopping/items/{del_id}")
        if del_resp.status_code in (200, 204):
            # Verify gone
            list_resp2 = client.get("/api/shopping/current")
            if list_resp2.status_code == 200:
                data2 = list_resp2.json()
                items2 = data2.get("items", data2) if isinstance(data2, dict) else data2
                still_there = [i for i in items2 if i.get("id") == del_id]
                if not still_there:
                    print(f"  PASS: Deleted item (id={del_id}) no longer in list")
                else:
                    print(f"  FAIL: Deleted item still appears in list")
                    failures.append("DELETE /api/shopping/items/{id} removes item from list")
        else:
            print(f"  FAIL: DELETE returned {del_resp.status_code}")
            failures.append("DELETE /api/shopping/items/{id} returns 200 or 204")

    db_module.DB_PATH = orig_db_path

# ─── PART 2: shopping.js frontend implementation check ────────────────────

print()
print("=" * 55)
print("PART 2: shopping.js — Frontend Implementation Status")
print("=" * 55)

shopping_js = Path(SPRINT_DIR) / "frontend" / "js" / "shopping.js"
print()

if not shopping_js.exists():
    print(f"  FAIL: frontend/js/shopping.js does not exist")
    failures.append("frontend/js/shopping.js exists")
else:
    content = shopping_js.read_text(encoding="utf-8", errors="replace")
    size = shopping_js.stat().st_size
    print(f"  File: frontend/js/shopping.js ({size} bytes)")

    # Detect if it's a stub
    is_stub = "coming soon" in content.lower() or "placeholder" in content.lower() or "stub" in content.lower()

    if is_stub:
        print(f"  STATUS: STUB — shopping.js is a placeholder, full implementation pending")
        print()

        has_render_shopping = "renderShopping" in content
        if has_render_shopping:
            print(f"  OK: renderShopping() function defined (navigation won't break)")
        else:
            print(f"  FAIL: renderShopping() not defined — navigation to #shopping will error")
            failures.append("shopping.js defines renderShopping()")

        required_features = [
            ("Generate button calling POST /api/shopping/generate", "generate" in content.lower()),
            ("GET /api/shopping/current for list fetch", "current" in content and "/api/shopping" in content),
            ("Checkbox per item (PATCH /api/shopping/items/{id})", "patch" in content.lower() or "checked" in content.lower()),
            ("Add manual item (POST /api/shopping/items)", "/api/shopping/items" in content),
            ("Items grouped by grocery_section", "grocery_section" in content or "section" in content.lower()),
            ("Item count summary", "count" in content.lower() or "items" in content.lower()),
            ("DELETE item", "delete" in content.lower() and "item" in content.lower()),
        ]

        missing = [name for name, found in required_features if not found]
        present = [name for name, found in required_features if found]

        if missing:
            print(f"  Missing features ({len(missing)}/{len(required_features)}):")
            for m in missing:
                print(f"    MISSING: {m}")
            failures.append(f"shopping.js implements full shopping list UI (missing: {', '.join(missing)})")
        if present:
            print(f"  Present features:")
            for p in present:
                print(f"    OK: {p}")
    else:
        print(f"  STATUS: Implementation present — checking required features")
        print()

        checks = [
            ("renderShopping() entry point", "renderShopping" in content),
            ("Generate from This Week button", "generate" in content.lower() and ("button" in content.lower() or "generate" in content)),
            ("GET /api/shopping/current", "/api/shopping/current" in content),
            ("POST /api/shopping/generate", "/api/shopping/generate" in content),
            ("PATCH checked state", "PATCH" in content or "'PATCH'" in content or '"PATCH"' in content),
            ("POST manual item", "POST" in content and "/api/shopping/items" in content),
            ("DELETE item", "DELETE" in content and "item" in content.lower()),
            ("Grouped by grocery_section", "grocery_section" in content or "section" in content.lower()),
            ("Item count summary", any(c in content.lower() for c in ["items,", "items ", "checked", "count"])),
        ]

        all_ok = True
        for name, ok in checks:
            if ok:
                print(f"  OK: {name}")
            else:
                print(f"  FAIL: {name}")
                failures.append(f"shopping.js: {name}")
                all_ok = False

        if all_ok:
            print()
            print(f"  PASS: shopping.js has all required shopping list features")

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
    print("User impact: Cook cannot generate or view their shopping list through the UI.")
    print("The shopping.js frontend needs to be implemented (currently a stub).")
    sys.exit(1)
else:
    print()
    print("RESULT: PASS — Shopping API and frontend both operational")
    print("Value delivered: Cook can generate a shopping list, check off items while shopping,")
    print("add manual items, and return to find their checked state preserved.")
    sys.exit(0)
