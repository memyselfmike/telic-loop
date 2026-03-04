"""API integration tests for Recipe Manager"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sqlite3
import os

from backend.main import app
from backend.database import DB_PATH, init_db


@pytest.fixture(scope="function")
def client():
    """Create a test client with a fresh database"""
    # Use a test database
    test_db_path = Path(__file__).parent.parent / "data" / "test_recipes.db"

    # Backup original DB_PATH
    import backend.database
    original_db_path = backend.database.DB_PATH
    backend.database.DB_PATH = test_db_path

    # Remove test database if it exists
    if test_db_path.exists():
        test_db_path.unlink()

    # Initialize fresh database
    init_db()

    # Create client
    with TestClient(app) as test_client:
        yield test_client

    # Cleanup
    if test_db_path.exists():
        test_db_path.unlink()

    # Restore original DB_PATH
    backend.database.DB_PATH = original_db_path


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_seed_data_loads(client):
    """Test that seed data is loaded on first run"""
    response = client.get("/api/recipes")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 5

    # Verify all categories are represented
    categories = {r["category"] for r in recipes}
    assert categories == {"breakfast", "lunch", "dinner", "snack", "dessert"}


def test_create_recipe(client):
    """Test creating a recipe with ingredients"""
    recipe_data = {
        "title": "Test Recipe",
        "description": "A test recipe",
        "category": "dinner",
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "servings": 4,
        "instructions": "1. Test step 1\n2. Test step 2",
        "tags": "test,quick",
        "ingredients": [
            {"quantity": 2, "unit": "cup", "item": "flour", "grocery_section": "pantry"},
            {"quantity": 1, "unit": "whole", "item": "egg", "grocery_section": "dairy"}
        ]
    }

    response = client.post("/api/recipes", json=recipe_data)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Test Recipe"
    assert data["category"] == "dinner"
    assert len(data["ingredients"]) == 2
    assert data["meal_plan_count"] == 0


def test_get_recipe_by_id(client):
    """Test retrieving a recipe by ID with ingredients"""
    response = client.get("/api/recipes/1")
    assert response.status_code == 200

    recipe = response.json()
    assert recipe["id"] == 1
    assert "ingredients" in recipe
    assert len(recipe["ingredients"]) > 0
    assert "meal_plan_count" in recipe


def test_get_recipe_not_found(client):
    """Test getting non-existent recipe returns 404"""
    response = client.get("/api/recipes/9999")
    assert response.status_code == 404


def test_filter_recipes_by_category(client):
    """Test filtering recipes by category"""
    response = client.get("/api/recipes?category=breakfast")
    assert response.status_code == 200

    recipes = response.json()
    assert len(recipes) >= 1
    for recipe in recipes:
        assert recipe["category"] == "breakfast"


def test_filter_recipes_by_tag(client):
    """Test filtering recipes by tag"""
    response = client.get("/api/recipes?tag=quick")
    assert response.status_code == 200

    recipes = response.json()
    assert len(recipes) >= 1
    for recipe in recipes:
        assert "quick" in recipe["tags"]


def test_search_recipes(client):
    """Test searching recipes by title and ingredients"""
    # Search by title
    response = client.get("/api/recipes?search=Oatmeal")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) >= 1

    # Search by ingredient
    response = client.get("/api/recipes?search=chicken")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) >= 1


def test_combined_filters(client):
    """Test combining multiple filters"""
    response = client.get("/api/recipes?category=snack&tag=quick")
    assert response.status_code == 200

    recipes = response.json()
    for recipe in recipes:
        assert recipe["category"] == "snack"
        assert "quick" in recipe["tags"]


def test_search_no_results(client):
    """Test search with no matches returns empty list"""
    response = client.get("/api/recipes?search=nonexistentitem12345")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 0


def test_update_recipe(client):
    """Test updating a recipe and replacing ingredients"""
    # Get existing recipe
    recipe_response = client.get("/api/recipes/1")
    recipe = recipe_response.json()

    # Update it
    updated_data = {
        "title": "Updated Title",
        "description": recipe["description"],
        "category": recipe["category"],
        "prep_time_minutes": 99,
        "cook_time_minutes": recipe["cook_time_minutes"],
        "servings": recipe["servings"],
        "instructions": recipe["instructions"],
        "tags": recipe["tags"],
        "ingredients": [
            {"quantity": 5, "unit": "cup", "item": "new ingredient", "grocery_section": "other"}
        ]
    }

    response = client.put(f"/api/recipes/{recipe['id']}", json=updated_data)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["prep_time_minutes"] == 99
    assert len(data["ingredients"]) == 1
    assert data["ingredients"][0]["item"] == "new ingredient"


def test_delete_recipe(client):
    """Test deleting a recipe"""
    response = client.delete("/api/recipes/1")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get("/api/recipes/1")
    assert response.status_code == 404


def test_assign_meal_to_slot(client):
    """Test assigning a recipe to a meal slot"""
    meal_data = {
        "week_start": "2026-03-03",  # A Monday
        "day_of_week": 0,
        "meal_slot": "dinner",
        "recipe_id": 1
    }

    response = client.put("/api/meals", json=meal_data)
    assert response.status_code == 200

    data = response.json()
    assert data["week_start"] == "2026-03-03"
    assert data["day_of_week"] == 0
    assert data["meal_slot"] == "dinner"
    assert data["recipe_id"] == 1
    assert "recipe_title" in data
    assert "prep_time_minutes" in data


def test_get_meal_plan_for_week(client):
    """Test retrieving meal plan for a week"""
    # Assign a few meals
    client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })
    client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 1,
        "meal_slot": "lunch",
        "recipe_id": 2
    })

    response = client.get("/api/meals?week=2026-03-03")
    assert response.status_code == 200

    meals = response.json()
    assert len(meals) == 2
    assert all("recipe_title" in m for m in meals)


def test_upsert_meal_slot(client):
    """Test that assigning to same slot replaces previous assignment"""
    meal_data = {
        "week_start": "2026-03-03",
        "day_of_week": 0,
        "meal_slot": "dinner",
        "recipe_id": 1
    }

    # First assignment
    response = client.put("/api/meals", json=meal_data)
    assert response.status_code == 200

    # Replace with different recipe
    meal_data["recipe_id"] = 2
    response = client.put("/api/meals", json=meal_data)
    assert response.status_code == 200

    # Verify only one entry for this slot
    response = client.get("/api/meals?week=2026-03-03")
    meals = response.json()
    dinner_meals = [m for m in meals if m["day_of_week"] == 0 and m["meal_slot"] == "dinner"]
    assert len(dinner_meals) == 1
    assert dinner_meals[0]["recipe_id"] == 2


def test_delete_meal_slot(client):
    """Test clearing a meal slot"""
    # Assign meal
    response = client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 0,
        "meal_slot": "dinner",
        "recipe_id": 1
    })
    meal_id = response.json()["id"]

    # Delete it
    response = client.delete(f"/api/meals/{meal_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get("/api/meals?week=2026-03-03")
    meals = response.json()
    assert len(meals) == 0


def test_cascade_delete_recipe_removes_meal_plans(client):
    """Test that deleting a recipe removes its meal plan entries"""
    # Assign recipe to meal slot
    client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 0,
        "meal_slot": "dinner",
        "recipe_id": 1
    })

    # Verify meal plan exists
    response = client.get("/api/meals?week=2026-03-03")
    assert len(response.json()) == 1

    # Delete recipe
    client.delete("/api/recipes/1")

    # Verify meal plan is gone
    response = client.get("/api/meals?week=2026-03-03")
    assert len(response.json()) == 0


def test_generate_shopping_list(client):
    """Test generating shopping list from meal plan"""
    # Assign some meals
    client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1  # Classic Oatmeal
    })
    client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 1,
        "meal_slot": "lunch",
        "recipe_id": 2  # Grilled Chicken Salad
    })

    # Generate shopping list
    response = client.post("/api/shopping/generate", json={"week_start": "2026-03-03"})
    assert response.status_code == 201

    data = response.json()
    assert data["week_start"] == "2026-03-03"
    assert len(data["items"]) > 0

    # Verify items are from recipes
    items = {item["item"] for item in data["items"]}
    assert "rolled oats" in items or "milk" in items or "chicken breast" in items


def test_shopping_list_unit_normalization(client):
    """Test that shopping list normalizes units correctly"""
    # Create recipes with ingredients that need normalization
    # Recipe 1: 2 tsp sugar
    client.post("/api/recipes", json={
        "title": "Recipe 1",
        "category": "dessert",
        "ingredients": [
            {"quantity": 2, "unit": "tsp", "item": "sugar", "grocery_section": "pantry"}
        ]
    })

    # Recipe 2: 2 tsp sugar
    client.post("/api/recipes", json={
        "title": "Recipe 2",
        "category": "dessert",
        "ingredients": [
            {"quantity": 2, "unit": "tsp", "item": "sugar", "grocery_section": "pantry"}
        ]
    })

    # Get recipe IDs
    recipes = client.get("/api/recipes?search=Recipe").json()
    recipe1_id = recipes[0]["id"]
    recipe2_id = recipes[1]["id"]

    # Assign both to meal plan
    client.put("/api/meals", json={
        "week_start": "2026-03-10",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": recipe1_id
    })
    client.put("/api/meals", json={
        "week_start": "2026-03-10",
        "day_of_week": 1,
        "meal_slot": "breakfast",
        "recipe_id": recipe2_id
    })

    # Generate shopping list
    response = client.post("/api/shopping/generate", json={"week_start": "2026-03-10"})
    assert response.status_code == 201

    data = response.json()

    # Find sugar item
    sugar_items = [item for item in data["items"] if "sugar" in item["item"]]
    assert len(sugar_items) == 1

    # 2 tsp + 2 tsp = 4 tsp = 1.3 tbsp (decimal format)
    sugar = sugar_items[0]
    assert sugar["unit"] == "tbsp"
    assert sugar["quantity"] == 1.3


def test_shopping_list_grouping_by_section(client):
    """Test that shopping list items are grouped by grocery section"""
    # Assign meals
    client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })

    # Generate list
    response = client.post("/api/shopping/generate", json={"week_start": "2026-03-03"})
    data = response.json()

    # Verify items have sections
    for item in data["items"]:
        assert "grocery_section" in item
        assert item["grocery_section"] in ["produce", "meat", "dairy", "pantry", "frozen", "other"]


def test_generate_empty_week_fails(client):
    """Test that generating list for empty week returns error"""
    response = client.post("/api/shopping/generate", json={"week_start": "2026-12-01"})
    assert response.status_code == 400
    assert "No meals planned" in response.json()["detail"]


def test_get_current_shopping_list(client):
    """Test getting the current shopping list"""
    # Create a list first
    client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })
    client.post("/api/shopping/generate", json={"week_start": "2026-03-03"})

    # Get current list
    response = client.get("/api/shopping/current")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "week_start" in data


def test_toggle_shopping_item_checked(client):
    """Test toggling checked status of shopping item"""
    # Create list
    client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })
    response = client.post("/api/shopping/generate", json={"week_start": "2026-03-03"})
    items = response.json()["items"]
    item_id = items[0]["id"]

    # Toggle checked
    response = client.patch(f"/api/shopping/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["checked"] is True

    # Toggle again
    response = client.patch(f"/api/shopping/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["checked"] is False


def test_add_manual_shopping_item(client):
    """Test adding a manual item to shopping list"""
    # Create list first
    client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })
    client.post("/api/shopping/generate", json={"week_start": "2026-03-03"})

    # Add manual item
    manual_item = {
        "item": "paper towels",
        "quantity": 1,
        "unit": "pack",
        "grocery_section": "other",
        "checked": False,
        "source": "manual"
    }

    response = client.post("/api/shopping/items", json=manual_item)
    assert response.status_code == 201

    data = response.json()
    assert data["item"] == "paper towels"
    assert data["source"] == "manual"


def test_delete_shopping_item(client):
    """Test removing an item from shopping list"""
    # Create list
    client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })
    response = client.post("/api/shopping/generate", json={"week_start": "2026-03-03"})
    items = response.json()["items"]
    item_id = items[0]["id"]

    # Delete item
    response = client.delete(f"/api/shopping/items/{item_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get("/api/shopping/current")
    remaining_items = response.json()["items"]
    assert item_id not in [item["id"] for item in remaining_items]


def test_regenerate_shopping_list_replaces_old(client):
    """Test that generating new list replaces old one"""
    # Create first list
    client.put("/api/meals", json={
        "week_start": "2026-03-03",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })
    response1 = client.post("/api/shopping/generate", json={"week_start": "2026-03-03"})
    list1_id = response1.json()["id"]

    # Generate again for same week
    response2 = client.post("/api/shopping/generate", json={"week_start": "2026-03-03"})
    list2_id = response2.json()["id"]

    # IDs should be different (new list created)
    assert list2_id != list1_id

    # Current should return the new one
    response = client.get("/api/shopping/current")
    assert response.json()["id"] == list2_id
