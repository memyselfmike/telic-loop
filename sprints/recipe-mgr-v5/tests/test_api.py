"""
API Integration Tests for Recipe Manager
Tests all endpoints using FastAPI TestClient
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app
from backend.database import get_connection, init_database, DB_PATH


@pytest.fixture(scope="function")
def client():
    """
    Create a test client with fresh database for each test
    """
    # Remove existing test database
    if DB_PATH.exists():
        DB_PATH.unlink()

    # Initialize fresh database with seed data
    init_database()

    # Create test client
    with TestClient(app) as test_client:
        yield test_client

    # Cleanup after test
    if DB_PATH.exists():
        DB_PATH.unlink()


# ========== Recipe CRUD Tests ==========

def test_create_recipe(client):
    """Test POST /api/recipes creates a recipe with ingredients"""
    recipe_data = {
        "title": "Test Recipe",
        "description": "A test recipe",
        "category": "lunch",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 2,
        "instructions": "1. Mix\n2. Cook",
        "tags": "test,quick",
        "ingredients": [
            {"quantity": 1.0, "unit": "cup", "item": "flour", "grocery_section": "pantry", "sort_order": 0},
            {"quantity": 2.0, "unit": "whole", "item": "eggs", "grocery_section": "dairy", "sort_order": 1}
        ]
    }

    response = client.post("/api/recipes/", json=recipe_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Recipe"
    assert data["category"] == "lunch"
    assert "id" in data


def test_get_recipe_by_id(client):
    """Test GET /api/recipes/{id} returns recipe with ingredients"""
    # Use seed data - recipe ID 1 should exist
    response = client.get("/api/recipes/1")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "title" in data
    assert "ingredients" in data
    assert len(data["ingredients"]) > 0


def test_get_all_recipes(client):
    """Test GET /api/recipes returns all recipes"""
    response = client.get("/api/recipes/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5  # Should have 5 seed recipes


def test_filter_recipes_by_category(client):
    """Test GET /api/recipes?category= filters by category"""
    response = client.get("/api/recipes/?category=breakfast")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for recipe in data:
        assert recipe["category"] == "breakfast"


def test_search_recipes(client):
    """Test GET /api/recipes?search= searches across title, description, ingredients"""
    response = client.get("/api/recipes/?search=oat")
    assert response.status_code == 200
    data = response.json()
    # Should find "Classic Oatmeal" from seed data
    assert len(data) >= 1


def test_filter_recipes_by_tag(client):
    """Test GET /api/recipes?tag= filters by tag"""
    # First create a recipe with a specific tag
    recipe_data = {
        "title": "Quick Soup",
        "category": "dinner",
        "tags": "quick,easy",
        "ingredients": [{"quantity": 1.0, "unit": "cup", "item": "water", "grocery_section": "other"}]
    }
    create_response = client.post("/api/recipes/", json=recipe_data)
    assert create_response.status_code == 201

    # Now search by tag
    response = client.get("/api/recipes/?tag=quick")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("quick" in recipe["tags"] for recipe in data)


def test_update_recipe(client):
    """Test PUT /api/recipes/{id} updates recipe and replaces ingredients"""
    # Get existing recipe
    get_response = client.get("/api/recipes/1")
    assert get_response.status_code == 200
    recipe = get_response.json()

    # Update it
    recipe["title"] = "Updated Title"
    recipe["ingredients"] = [
        {"quantity": 3.0, "unit": "cup", "item": "new ingredient", "grocery_section": "pantry", "sort_order": 0}
    ]

    update_response = client.put("/api/recipes/1", json=recipe)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Updated Title"

    # Verify ingredients were replaced
    get_response = client.get("/api/recipes/1")
    recipe_data = get_response.json()
    assert len(recipe_data["ingredients"]) == 1
    assert recipe_data["ingredients"][0]["item"] == "new ingredient"


def test_delete_recipe(client):
    """Test DELETE /api/recipes/{id} removes recipe"""
    response = client.delete("/api/recipes/1")
    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get("/api/recipes/1")
    assert get_response.status_code == 404


def test_delete_recipe_cascades_to_meal_plans(client):
    """Test DELETE /api/recipes removes associated meal plans"""
    # Assign recipe to meal plan
    meal_data = {
        "week_start": "2026-03-02",  # A Monday
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    }
    assign_response = client.put("/api/meals/", json=meal_data)
    assert assign_response.status_code == 200

    # Delete the recipe
    delete_response = client.delete("/api/recipes/1")
    assert delete_response.status_code == 200

    # Check meal plan is empty
    meals_response = client.get("/api/meals/?week=2026-03-02")
    assert meals_response.status_code == 200
    meals = meals_response.json()
    assert len(meals) == 0


# ========== Meal Plan Tests ==========

def test_assign_meal_to_slot(client):
    """Test PUT /api/meals assigns recipe to meal slot"""
    meal_data = {
        "week_start": "2026-03-02",  # Monday
        "day_of_week": 1,  # Tuesday
        "meal_slot": "lunch",
        "recipe_id": 2
    }

    response = client.put("/api/meals/", json=meal_data)
    assert response.status_code == 200
    data = response.json()
    assert data["recipe_id"] == 2
    assert data["day_of_week"] == 1
    assert "recipe_title" in data


def test_get_week_meals(client):
    """Test GET /api/meals?week= returns all meals for week"""
    # Assign a meal
    meal_data = {
        "week_start": "2026-03-02",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    }
    client.put("/api/meals/", json=meal_data)

    # Get week
    response = client.get("/api/meals/?week=2026-03-02")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["week_start"] == "2026-03-02"


def test_replace_meal_in_slot(client):
    """Test PUT /api/meals replaces existing meal in same slot"""
    meal_data = {
        "week_start": "2026-03-02",
        "day_of_week": 0,
        "meal_slot": "dinner",
        "recipe_id": 1
    }

    # First assignment
    response1 = client.put("/api/meals/", json=meal_data)
    assert response1.status_code == 200
    meal_id_1 = response1.json()["id"]

    # Replace with different recipe
    meal_data["recipe_id"] = 2
    response2 = client.put("/api/meals/", json=meal_data)
    assert response2.status_code == 200
    meal_id_2 = response2.json()["id"]

    # Should reuse same ID (update, not insert)
    assert meal_id_1 == meal_id_2
    assert response2.json()["recipe_id"] == 2


def test_clear_meal_slot(client):
    """Test DELETE /api/meals/{id} removes meal assignment"""
    # Assign meal
    meal_data = {
        "week_start": "2026-03-02",
        "day_of_week": 0,
        "meal_slot": "snack",
        "recipe_id": 1
    }
    assign_response = client.put("/api/meals/", json=meal_data)
    meal_id = assign_response.json()["id"]

    # Delete it
    delete_response = client.delete(f"/api/meals/{meal_id}")
    assert delete_response.status_code == 200

    # Verify it's gone
    meals_response = client.get("/api/meals/?week=2026-03-02")
    meals = meals_response.json()
    assert not any(m["id"] == meal_id for m in meals)


def test_week_start_must_be_monday(client):
    """Test PUT /api/meals validates week_start is a Monday"""
    meal_data = {
        "week_start": "2026-03-03",  # Tuesday, not Monday
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    }

    response = client.put("/api/meals/", json=meal_data)
    assert response.status_code == 400
    assert "Monday" in response.json()["detail"]


# ========== Shopping List Tests ==========

def test_generate_shopping_list(client):
    """Test POST /api/shopping/generate creates list from meal plan"""
    # Assign meals
    client.put("/api/meals/", json={
        "week_start": "2026-03-02",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })
    client.put("/api/meals/", json={
        "week_start": "2026-03-02",
        "day_of_week": 1,
        "meal_slot": "lunch",
        "recipe_id": 2
    })

    # Generate shopping list
    response = client.post("/api/shopping/generate", json={"week_start": "2026-03-02"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert data["week_start"] == "2026-03-02"


def test_shopping_list_unit_normalization(client):
    """Test shopping list normalizes units correctly"""
    # Create recipe with tsp measurements
    recipe_data = {
        "title": "Unit Test Recipe",
        "category": "snack",
        "ingredients": [
            {"quantity": 4.0, "unit": "tsp", "item": "sugar", "grocery_section": "pantry"}
        ]
    }
    create_response = client.post("/api/recipes/", json=recipe_data)
    recipe_id = create_response.json()["id"]

    # Assign to meal plan
    client.put("/api/meals/", json={
        "week_start": "2026-03-02",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": recipe_id
    })

    # Generate shopping list
    response = client.post("/api/shopping/generate", json={"week_start": "2026-03-02"})
    data = response.json()

    # Find sugar item
    sugar_items = [item for item in data["items"] if item["item"] == "sugar"]
    assert len(sugar_items) > 0
    sugar = sugar_items[0]

    # 4 tsp should normalize to 1.3 tbsp
    assert sugar["unit"] == "tbsp"
    assert sugar["quantity"] == 1.3


def test_shopping_list_aggregation(client):
    """Test shopping list aggregates same ingredients"""
    # Create two recipes with same ingredient
    for i in range(2):
        recipe_data = {
            "title": f"Agg Test {i}",
            "category": "lunch",
            "ingredients": [
                {"quantity": 1.0, "unit": "cup", "item": "flour", "grocery_section": "pantry"}
            ]
        }
        create_response = client.post("/api/recipes/", json=recipe_data)
        recipe_id = create_response.json()["id"]

        # Assign to meal plan
        client.put("/api/meals/", json={
            "week_start": "2026-03-02",
            "day_of_week": i,
            "meal_slot": "lunch",
            "recipe_id": recipe_id
        })

    # Generate shopping list
    response = client.post("/api/shopping/generate", json={"week_start": "2026-03-02"})
    data = response.json()

    # Should have one flour item with quantity 2.0
    flour_items = [item for item in data["items"] if item["item"] == "flour"]
    assert len(flour_items) == 1
    assert flour_items[0]["quantity"] == 2.0


def test_shopping_list_groups_by_section(client):
    """Test shopping list items are grouped by grocery_section"""
    # Assign meal
    client.put("/api/meals/", json={
        "week_start": "2026-03-02",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })

    # Generate list
    response = client.post("/api/shopping/generate", json={"week_start": "2026-03-02"})
    data = response.json()

    # Verify all items have grocery_section
    for item in data["items"]:
        assert "grocery_section" in item
        assert item["grocery_section"] in ["produce", "meat", "dairy", "pantry", "frozen", "other"]


def test_get_current_shopping_list(client):
    """Test GET /api/shopping/current returns most recent list"""
    # Generate a list
    client.put("/api/meals/", json={
        "week_start": "2026-03-02",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })
    client.post("/api/shopping/generate", json={"week_start": "2026-03-03"})

    # Get current
    response = client.get("/api/shopping/current")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "week_start" in data


def test_add_manual_shopping_item(client):
    """Test POST /api/shopping/items adds manual item"""
    # Generate initial list
    client.put("/api/meals/", json={
        "week_start": "2026-03-02",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })
    client.post("/api/shopping/generate", json={"week_start": "2026-03-03"})

    # Add manual item
    manual_item = {
        "item": "toilet paper",
        "quantity": 1.0,
        "unit": "whole",
        "grocery_section": "other",
        "source": "manual"
    }
    response = client.post("/api/shopping/items", json=manual_item)
    assert response.status_code == 201
    data = response.json()
    assert data["item"] == "toilet paper"
    assert data["source"] == "manual"


def test_toggle_shopping_item_checked(client):
    """Test PATCH /api/shopping/items/{id} toggles checked status"""
    # Generate list
    client.put("/api/meals/", json={
        "week_start": "2026-03-02",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })
    gen_response = client.post("/api/shopping/generate", json={"week_start": "2026-03-02"})
    items = gen_response.json()["items"]
    item_id = items[0]["id"]
    initial_checked = items[0]["checked"]

    # Toggle checked
    response = client.patch(f"/api/shopping/items/{item_id}")
    assert response.status_code == 200

    # Verify it toggled
    current_response = client.get("/api/shopping/current")
    current_items = current_response.json()["items"]
    updated_item = next(item for item in current_items if item["id"] == item_id)
    assert updated_item["checked"] != initial_checked


def test_delete_shopping_item(client):
    """Test DELETE /api/shopping/items/{id} removes item"""
    # Generate list
    client.put("/api/meals/", json={
        "week_start": "2026-03-02",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 1
    })
    gen_response = client.post("/api/shopping/generate", json={"week_start": "2026-03-02"})
    items = gen_response.json()["items"]
    item_id = items[0]["id"]

    # Delete item
    response = client.delete(f"/api/shopping/items/{item_id}")
    assert response.status_code == 200

    # Verify it's gone
    current_response = client.get("/api/shopping/current")
    current_items = current_response.json()["items"]
    assert not any(item["id"] == item_id for item in current_items)


# ========== Error Handling Tests ==========

def test_get_nonexistent_recipe(client):
    """Test GET /api/recipes/{id} returns 404 for nonexistent recipe"""
    response = client.get("/api/recipes/9999")
    assert response.status_code == 404


def test_assign_nonexistent_recipe_to_meal(client):
    """Test PUT /api/meals returns 404 for nonexistent recipe"""
    meal_data = {
        "week_start": "2026-03-02",
        "day_of_week": 0,
        "meal_slot": "breakfast",
        "recipe_id": 9999
    }
    response = client.put("/api/meals/", json=meal_data)
    assert response.status_code == 404
