from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from database import get_connection
from models import RecipeCreate, RecipeResponse, IngredientResponse

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("", response_model=list[RecipeResponse])
def get_recipes(
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[str] = Query(None, description="Filter by tag (partial match)"),
    search: Optional[str] = Query(None, description="Search title, description, and ingredients")
):
    """
    Get all recipes with optional filtering.

    Query parameters:
    - category: exact match on category field
    - tag: partial match within comma-separated tags
    - search: case-insensitive search in title, description, and ingredient items
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Build query with filters
    query = "SELECT DISTINCT r.* FROM recipes r"
    params = []
    where_clauses = []

    # If search includes ingredients, join with ingredients table
    if search:
        query += " LEFT JOIN ingredients i ON r.id = i.recipe_id"
        search_pattern = f"%{search}%"
        where_clauses.append(
            "(r.title LIKE ? OR r.description LIKE ? OR i.item LIKE ?)"
        )
        params.extend([search_pattern, search_pattern, search_pattern])

    if category:
        where_clauses.append("r.category = ?")
        params.append(category)

    if tag:
        # Partial match for tags (e.g., "quick" matches "quick,healthy")
        where_clauses.append("r.tags LIKE ?")
        params.append(f"%{tag}%")

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY r.created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    # Get recipe IDs to fetch ingredients
    recipe_ids = [row["id"] for row in rows]

    # Fetch all ingredients for these recipes
    ingredients_map = {}
    if recipe_ids:
        placeholders = ",".join("?" * len(recipe_ids))
        cursor.execute(
            f"SELECT * FROM ingredients WHERE recipe_id IN ({placeholders}) ORDER BY sort_order",
            recipe_ids
        )
        for ing_row in cursor.fetchall():
            recipe_id = ing_row["recipe_id"]
            if recipe_id not in ingredients_map:
                ingredients_map[recipe_id] = []
            ingredients_map[recipe_id].append(IngredientResponse(
                id=ing_row["id"],
                recipe_id=ing_row["recipe_id"],
                quantity=ing_row["quantity"],
                unit=ing_row["unit"],
                item=ing_row["item"],
                grocery_section=ing_row["grocery_section"],
                sort_order=ing_row["sort_order"]
            ))

    conn.close()

    # Build response
    recipes = []
    for row in rows:
        recipe_id = row["id"]
        recipes.append(RecipeResponse(
            id=recipe_id,
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
            ingredients=ingredients_map.get(recipe_id, [])
        ))

    return recipes


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: int):
    """Get a single recipe by ID with all its ingredients."""
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch recipe
    cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")

    # Fetch ingredients
    cursor.execute(
        "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order",
        (recipe_id,)
    )
    ingredient_rows = cursor.fetchall()

    conn.close()

    ingredients = [
        IngredientResponse(
            id=ing["id"],
            recipe_id=ing["recipe_id"],
            quantity=ing["quantity"],
            unit=ing["unit"],
            item=ing["item"],
            grocery_section=ing["grocery_section"],
            sort_order=ing["sort_order"]
        )
        for ing in ingredient_rows
    ]

    return RecipeResponse(
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
        ingredients=ingredients
    )


@router.post("", response_model=RecipeResponse, status_code=201)
def create_recipe(recipe: RecipeCreate):
    """Create a new recipe with ingredients."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Insert recipe
        cursor.execute("""
            INSERT INTO recipes (title, description, category, prep_time_minutes,
                               cook_time_minutes, servings, instructions, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe.title,
            recipe.description,
            recipe.category,
            recipe.prep_time_minutes,
            recipe.cook_time_minutes,
            recipe.servings,
            recipe.instructions,
            recipe.tags
        ))

        recipe_id = cursor.lastrowid

        # Insert ingredients
        for idx, ingredient in enumerate(recipe.ingredients):
            cursor.execute("""
                INSERT INTO ingredients (recipe_id, quantity, unit, item, grocery_section, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                recipe_id,
                ingredient.quantity,
                ingredient.unit,
                ingredient.item,
                ingredient.grocery_section,
                idx
            ))

        conn.commit()

        # Fetch the created recipe to return
        cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        row = cursor.fetchone()

        cursor.execute(
            "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order",
            (recipe_id,)
        )
        ingredient_rows = cursor.fetchall()

        conn.close()

        ingredients = [
            IngredientResponse(
                id=ing["id"],
                recipe_id=ing["recipe_id"],
                quantity=ing["quantity"],
                unit=ing["unit"],
                item=ing["item"],
                grocery_section=ing["grocery_section"],
                sort_order=ing["sort_order"]
            )
            for ing in ingredient_rows
        ]

        return RecipeResponse(
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
            ingredients=ingredients
        )

    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to create recipe: {str(e)}")


@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(recipe_id: int, recipe: RecipeCreate):
    """Update an existing recipe, replacing all fields and ingredients."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if recipe exists
        cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")

        # Update recipe
        cursor.execute("""
            UPDATE recipes
            SET title = ?,
                description = ?,
                category = ?,
                prep_time_minutes = ?,
                cook_time_minutes = ?,
                servings = ?,
                instructions = ?,
                tags = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            recipe.title,
            recipe.description,
            recipe.category,
            recipe.prep_time_minutes,
            recipe.cook_time_minutes,
            recipe.servings,
            recipe.instructions,
            recipe.tags,
            recipe_id
        ))

        # Delete existing ingredients
        cursor.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))

        # Insert new ingredients
        for idx, ingredient in enumerate(recipe.ingredients):
            cursor.execute("""
                INSERT INTO ingredients (recipe_id, quantity, unit, item, grocery_section, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                recipe_id,
                ingredient.quantity,
                ingredient.unit,
                ingredient.item,
                ingredient.grocery_section,
                idx
            ))

        conn.commit()

        # Fetch the updated recipe to return
        cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        row = cursor.fetchone()

        cursor.execute(
            "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order",
            (recipe_id,)
        )
        ingredient_rows = cursor.fetchall()

        conn.close()

        ingredients = [
            IngredientResponse(
                id=ing["id"],
                recipe_id=ing["recipe_id"],
                quantity=ing["quantity"],
                unit=ing["unit"],
                item=ing["item"],
                grocery_section=ing["grocery_section"],
                sort_order=ing["sort_order"]
            )
            for ing in ingredient_rows
        ]

        return RecipeResponse(
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
            ingredients=ingredients
        )

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to update recipe: {str(e)}")


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int):
    """Delete a recipe. Cascades to ingredients and meal plans."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if recipe exists
        cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")

        # Delete recipe (cascades via foreign keys)
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()
        conn.close()

        return None  # 204 No Content

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete recipe: {str(e)}")
