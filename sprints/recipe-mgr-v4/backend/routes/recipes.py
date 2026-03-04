"""Recipe CRUD API routes"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import sqlite3
from backend.database import get_db
from backend.models import Recipe, RecipeCreate, RecipeUpdate, RecipeListItem, Ingredient


router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("", response_model=List[RecipeListItem])
async def list_recipes(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None
):
    """List all recipes with optional filters"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Build query with filters
        query = "SELECT * FROM recipes WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if tag:
            query += " AND tags LIKE ?"
            params.append(f"%{tag}%")

        if search:
            # Search in title, description, and ingredients
            query += """ AND (
                title LIKE ? OR
                description LIKE ? OR
                id IN (
                    SELECT recipe_id FROM ingredients
                    WHERE item LIKE ?
                )
            )"""
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        recipes = []
        for row in rows:
            recipes.append(RecipeListItem(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                category=row["category"],
                prep_time_minutes=row["prep_time_minutes"],
                cook_time_minutes=row["cook_time_minutes"],
                servings=row["servings"],
                instructions=row["instructions"],
                tags=row["tags"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            ))

        return recipes


@router.get("/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: int):
    """Get recipe by ID with ingredients and meal plan count"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get recipe
        cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Recipe not found")

        # Get ingredients
        cursor.execute(
            "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order",
            (recipe_id,)
        )
        ingredient_rows = cursor.fetchall()

        ingredients = []
        for ing_row in ingredient_rows:
            ingredients.append(Ingredient(
                id=ing_row["id"],
                recipe_id=ing_row["recipe_id"],
                quantity=ing_row["quantity"],
                unit=ing_row["unit"],
                item=ing_row["item"],
                grocery_section=ing_row["grocery_section"],
                sort_order=ing_row["sort_order"]
            ))

        # Get meal plan count
        cursor.execute(
            "SELECT COUNT(*) as count FROM meal_plans WHERE recipe_id = ?",
            (recipe_id,)
        )
        meal_plan_count = cursor.fetchone()["count"]

        recipe = Recipe(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            category=row["category"],
            prep_time_minutes=row["prep_time_minutes"],
            cook_time_minutes=row["cook_time_minutes"],
            servings=row["servings"],
            instructions=row["instructions"],
            tags=row["tags"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            ingredients=ingredients,
            meal_plan_count=meal_plan_count
        )

        return recipe


@router.post("", response_model=Recipe, status_code=201)
async def create_recipe(recipe: RecipeCreate):
    """Create a new recipe with ingredients"""
    with get_db() as conn:
        cursor = conn.cursor()

        try:
            # Insert recipe
            cursor.execute(
                """INSERT INTO recipes
                   (title, description, category, prep_time_minutes, cook_time_minutes,
                    servings, instructions, tags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    recipe.title,
                    recipe.description,
                    recipe.category,
                    recipe.prep_time_minutes,
                    recipe.cook_time_minutes,
                    recipe.servings,
                    recipe.instructions,
                    recipe.tags
                )
            )
            recipe_id = cursor.lastrowid

            # Insert ingredients
            for i, ingredient in enumerate(recipe.ingredients):
                cursor.execute(
                    """INSERT INTO ingredients
                       (recipe_id, quantity, unit, item, grocery_section, sort_order)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        recipe_id,
                        ingredient.quantity,
                        ingredient.unit,
                        ingredient.item,
                        ingredient.grocery_section,
                        i
                    )
                )

            conn.commit()

            # Return the created recipe
            cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
            row = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order",
                (recipe_id,)
            )
            ingredient_rows = cursor.fetchall()

            ingredients = []
            for ing_row in ingredient_rows:
                ingredients.append(Ingredient(
                    id=ing_row["id"],
                    recipe_id=ing_row["recipe_id"],
                    quantity=ing_row["quantity"],
                    unit=ing_row["unit"],
                    item=ing_row["item"],
                    grocery_section=ing_row["grocery_section"],
                    sort_order=ing_row["sort_order"]
                ))

            return Recipe(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                category=row["category"],
                prep_time_minutes=row["prep_time_minutes"],
                cook_time_minutes=row["cook_time_minutes"],
                servings=row["servings"],
                instructions=row["instructions"],
                tags=row["tags"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                ingredients=ingredients,
                meal_plan_count=0
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.put("/{recipe_id}", response_model=Recipe)
async def update_recipe(recipe_id: int, recipe: RecipeUpdate):
    """Update an existing recipe and replace ingredients"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if recipe exists
        cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Recipe not found")

        try:
            # Update recipe
            cursor.execute(
                """UPDATE recipes SET
                   title = ?, description = ?, category = ?,
                   prep_time_minutes = ?, cook_time_minutes = ?,
                   servings = ?, instructions = ?, tags = ?,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (
                    recipe.title,
                    recipe.description,
                    recipe.category,
                    recipe.prep_time_minutes,
                    recipe.cook_time_minutes,
                    recipe.servings,
                    recipe.instructions,
                    recipe.tags,
                    recipe_id
                )
            )

            # Delete existing ingredients
            cursor.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))

            # Insert new ingredients
            for i, ingredient in enumerate(recipe.ingredients):
                cursor.execute(
                    """INSERT INTO ingredients
                       (recipe_id, quantity, unit, item, grocery_section, sort_order)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        recipe_id,
                        ingredient.quantity,
                        ingredient.unit,
                        ingredient.item,
                        ingredient.grocery_section,
                        i
                    )
                )

            conn.commit()

            # Return the updated recipe
            return await get_recipe(recipe_id)

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: int):
    """Delete a recipe (cascades to ingredients and meal plans)"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if recipe exists
        cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Recipe not found")

        # Delete recipe (cascade handles ingredients and meal_plans)
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()

        return None
