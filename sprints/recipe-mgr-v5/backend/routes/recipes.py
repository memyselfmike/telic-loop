"""
Recipe CRUD API routes
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.database import get_connection
from backend.models import (
    Recipe, RecipeWithIngredients, RecipeCreate, RecipeUpdate,
    Ingredient, IngredientCreate
)

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("/", response_model=List[RecipeWithIngredients])
async def list_recipes(
    category: Optional[str] = Query(None, pattern="^(breakfast|lunch|dinner|snack|dessert)$"),
    tag: Optional[str] = None,
    search: Optional[str] = None
):
    """
    List all recipes with optional filtering
    - category: exact category match
    - tag: partial match within comma-separated tags
    - search: search title, description, and ingredient items
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Base query
    query = """
        SELECT DISTINCT r.*
        FROM recipes r
        LEFT JOIN ingredients i ON r.id = i.recipe_id
        WHERE 1=1
    """
    params = []

    # Apply filters
    if category:
        query += " AND r.category = ?"
        params.append(category)

    if tag:
        query += " AND r.tags LIKE ?"
        params.append(f"%{tag}%")

    if search:
        query += """ AND (
            r.title LIKE ? OR
            r.description LIKE ? OR
            i.item LIKE ?
        )"""
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern])

    query += " ORDER BY r.created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    # Convert to dict and group by recipe
    recipes_dict = {}
    for row in rows:
        recipe_id = row["id"]
        if recipe_id not in recipes_dict:
            recipes_dict[recipe_id] = {
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "category": row["category"],
                "prep_time_minutes": row["prep_time_minutes"],
                "cook_time_minutes": row["cook_time_minutes"],
                "servings": row["servings"],
                "instructions": row["instructions"],
                "tags": row["tags"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "ingredients": []
            }

    # Fetch ingredients for all recipes
    if recipes_dict:
        recipe_ids = list(recipes_dict.keys())
        placeholders = ",".join("?" * len(recipe_ids))
        cursor.execute(f"""
            SELECT * FROM ingredients
            WHERE recipe_id IN ({placeholders})
            ORDER BY recipe_id, sort_order
        """, recipe_ids)

        for ing_row in cursor.fetchall():
            recipe_id = ing_row["recipe_id"]
            if recipe_id in recipes_dict:
                recipes_dict[recipe_id]["ingredients"].append({
                    "id": ing_row["id"],
                    "recipe_id": ing_row["recipe_id"],
                    "quantity": ing_row["quantity"],
                    "unit": ing_row["unit"],
                    "item": ing_row["item"],
                    "grocery_section": ing_row["grocery_section"],
                    "sort_order": ing_row["sort_order"]
                })

    cursor.close()
    conn.close()

    return list(recipes_dict.values())


@router.get("/{recipe_id}", response_model=RecipeWithIngredients)
async def get_recipe(recipe_id: int):
    """Get a single recipe with ingredients"""
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch recipe
    cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Recipe not found")

    recipe_data = {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "prep_time_minutes": row["prep_time_minutes"],
        "cook_time_minutes": row["cook_time_minutes"],
        "servings": row["servings"],
        "instructions": row["instructions"],
        "tags": row["tags"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "ingredients": []
    }

    # Fetch ingredients
    cursor.execute("""
        SELECT * FROM ingredients
        WHERE recipe_id = ?
        ORDER BY sort_order
    """, (recipe_id,))

    for ing_row in cursor.fetchall():
        recipe_data["ingredients"].append({
            "id": ing_row["id"],
            "recipe_id": ing_row["recipe_id"],
            "quantity": ing_row["quantity"],
            "unit": ing_row["unit"],
            "item": ing_row["item"],
            "grocery_section": ing_row["grocery_section"],
            "sort_order": ing_row["sort_order"]
        })

    cursor.close()
    conn.close()

    return recipe_data


@router.post("/", response_model=RecipeWithIngredients, status_code=201)
async def create_recipe(recipe: RecipeCreate):
    """Create a new recipe with ingredients"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Insert recipe
        cursor.execute("""
            INSERT INTO recipes (
                title, description, category, prep_time_minutes,
                cook_time_minutes, servings, instructions, tags
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe.title, recipe.description, recipe.category,
            recipe.prep_time_minutes, recipe.cook_time_minutes,
            recipe.servings, recipe.instructions, recipe.tags
        ))

        recipe_id = cursor.lastrowid

        # Insert ingredients
        for ingredient in recipe.ingredients:
            cursor.execute("""
                INSERT INTO ingredients (
                    recipe_id, quantity, unit, item, grocery_section, sort_order
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                recipe_id, ingredient.quantity, ingredient.unit,
                ingredient.item, ingredient.grocery_section, ingredient.sort_order
            ))

        conn.commit()

        # Fetch and return the created recipe
        cursor.close()
        conn.close()

        return await get_recipe(recipe_id)

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to create recipe: {str(e)}")


@router.put("/{recipe_id}", response_model=RecipeWithIngredients)
async def update_recipe(recipe_id: int, recipe: RecipeUpdate):
    """Update recipe and replace all ingredients"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if recipe exists
        cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Recipe not found")

        # Update recipe
        cursor.execute("""
            UPDATE recipes
            SET title = ?, description = ?, category = ?,
                prep_time_minutes = ?, cook_time_minutes = ?,
                servings = ?, instructions = ?, tags = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            recipe.title, recipe.description, recipe.category,
            recipe.prep_time_minutes, recipe.cook_time_minutes,
            recipe.servings, recipe.instructions, recipe.tags,
            recipe_id
        ))

        # Delete old ingredients
        cursor.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))

        # Insert new ingredients
        for ingredient in recipe.ingredients:
            cursor.execute("""
                INSERT INTO ingredients (
                    recipe_id, quantity, unit, item, grocery_section, sort_order
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                recipe_id, ingredient.quantity, ingredient.unit,
                ingredient.item, ingredient.grocery_section, ingredient.sort_order
            ))

        conn.commit()
        cursor.close()
        conn.close()

        return await get_recipe(recipe_id)

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to update recipe: {str(e)}")


@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: int):
    """
    Delete recipe (cascades to ingredients and meal_plans)
    Returns warning if recipe is in active meal plans
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if recipe exists
        cursor.execute("SELECT title FROM recipes WHERE id = ?", (recipe_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Recipe not found")

        recipe_title = row["title"]

        # Check if recipe is in any meal plans
        cursor.execute("""
            SELECT COUNT(*) as count FROM meal_plans WHERE recipe_id = ?
        """, (recipe_id,))
        meal_plan_count = cursor.fetchone()["count"]

        # Delete recipe (cascades to ingredients and meal_plans due to FK constraints)
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return {
            "message": "Recipe deleted successfully",
            "title": recipe_title,
            "warning": f"This recipe was removed from {meal_plan_count} meal plan slot(s)" if meal_plan_count > 0 else None
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete recipe: {str(e)}")
