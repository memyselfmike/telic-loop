#!/usr/bin/env python3
"""
Verification: Pydantic model validation
PRD Reference: Task 1.3 (models.py)
Vision Goal: Prevents malformed data from corrupting the database
Category: unit

Tests that Pydantic models validate inputs correctly.
"""

import sys
import os

SPRINT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SPRINT_DIR, "backend"))

print("=== Pydantic Model Validation ===")

failures = []

try:
    from models import (
        IngredientCreate, RecipeCreate, IngredientResponse,
        RecipeResponse, RecipeListItem
    )
    print("OK: All models imported successfully")
except ImportError as e:
    print(f"FAIL: Cannot import models: {e}")
    sys.exit(1)

print()
print("--- IngredientCreate validation ---")

# Valid ingredient
try:
    ing = IngredientCreate(quantity=2.0, unit="cup", item="flour", grocery_section="pantry")
    assert ing.quantity == 2.0
    assert ing.unit == "cup"
    assert ing.item == "flour"
    assert ing.grocery_section == "pantry"
    print("  PASS: Valid ingredient creates successfully")
except Exception as e:
    print(f"  FAIL: Valid ingredient rejected: {e}")
    failures.append("IngredientCreate valid")

# Default grocery_section = 'other'
try:
    ing = IngredientCreate(quantity=1.0, unit="whole", item="egg")
    assert ing.grocery_section == "other", f"Expected 'other', got '{ing.grocery_section}'"
    print("  PASS: Default grocery_section = 'other'")
except Exception as e:
    print(f"  FAIL: Default grocery_section not 'other': {e}")
    failures.append("IngredientCreate default grocery_section")

# Missing required fields
try:
    ing = IngredientCreate(unit="cup", item="flour")  # missing quantity
    print(f"  FAIL: Missing quantity should be rejected (got quantity={ing.quantity})")
    failures.append("IngredientCreate missing quantity")
except Exception:
    print("  PASS: Missing quantity raises validation error")

print()
print("--- RecipeCreate validation ---")

valid_recipe_data = {
    "title": "Test Recipe",
    "description": "A test",
    "category": "dinner",
    "prep_time_minutes": 15,
    "cook_time_minutes": 30,
    "servings": 4,
    "instructions": "Step 1. Step 2.",
    "tags": "quick,easy",
    "ingredients": [
        {"quantity": 1.0, "unit": "cup", "item": "flour", "grocery_section": "pantry"}
    ]
}

# Valid recipe
try:
    recipe = RecipeCreate(**valid_recipe_data)
    assert recipe.title == "Test Recipe"
    assert recipe.category == "dinner"
    assert len(recipe.ingredients) == 1
    print("  PASS: Valid recipe creates successfully")
except Exception as e:
    print(f"  FAIL: Valid recipe rejected: {e}")
    failures.append("RecipeCreate valid")

# Missing title
try:
    data = valid_recipe_data.copy()
    del data["title"]
    recipe = RecipeCreate(**data)
    print(f"  FAIL: Missing title should be rejected")
    failures.append("RecipeCreate missing title")
except Exception:
    print("  PASS: Missing title raises validation error")

# Missing category
try:
    data = valid_recipe_data.copy()
    del data["category"]
    recipe = RecipeCreate(**data)
    print(f"  FAIL: Missing category should be rejected")
    failures.append("RecipeCreate missing category")
except Exception:
    print("  PASS: Missing category raises validation error")

# Nested ingredients list
try:
    data = valid_recipe_data.copy()
    data["ingredients"] = [
        {"quantity": 2.0, "unit": "lb", "item": "chicken", "grocery_section": "meat"},
        {"quantity": 1.0, "unit": "tbsp", "item": "soy sauce", "grocery_section": "pantry"},
    ]
    recipe = RecipeCreate(**data)
    assert len(recipe.ingredients) == 2
    assert recipe.ingredients[0].item == "chicken"
    print("  PASS: Nested ingredients list works")
except Exception as e:
    print(f"  FAIL: Nested ingredients rejected: {e}")
    failures.append("RecipeCreate nested ingredients")

print()
print("--- RecipeResponse has id and timestamps ---")
try:
    from datetime import datetime
    resp = RecipeResponse(
        id=1,
        title="Test",
        description="",
        category="dinner",
        prep_time_minutes=10,
        cook_time_minutes=20,
        servings=2,
        instructions="",
        tags="",
        created_at="2026-02-17T00:00:00",
        updated_at="2026-02-17T00:00:00",
        ingredients=[]
    )
    assert resp.id == 1
    assert hasattr(resp, 'created_at')
    assert hasattr(resp, 'updated_at')
    assert hasattr(resp, 'ingredients')
    print("  PASS: RecipeResponse includes id, timestamps, and ingredients")
except Exception as e:
    print(f"  FAIL: RecipeResponse validation failed: {e}")
    failures.append("RecipeResponse structure")

print()
print("--- RecipeListItem (card-level, no full ingredients) ---")
try:
    item = RecipeListItem(
        id=1,
        title="Test Recipe",
        description="A test",
        category="dinner",
        prep_time_minutes=10,
        cook_time_minutes=20,
        servings=2,
        tags="quick"
    )
    assert item.id == 1
    assert item.title == "Test Recipe"
    print("  PASS: RecipeListItem creates successfully")
except Exception as e:
    print(f"  FAIL: RecipeListItem failed: {e}")
    failures.append("RecipeListItem")

print()
print("=" * 40)
if failures:
    print(f"RESULT: FAIL - {len(failures)} test(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("RESULT: PASS - All Pydantic model validations correct")
    sys.exit(0)
