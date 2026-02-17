from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models import (
    RecipeCreate,
    RecipeResponse,
    RecipeListItem,
    IngredientResponse,
)

router = APIRouter()


async def _fetch_recipe(db, recipe_id: int) -> RecipeResponse:
    cursor = await db.execute(
        "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    cursor = await db.execute(
        "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order",
        (recipe_id,),
    )
    ing_rows = await cursor.fetchall()
    ingredients = [
        IngredientResponse(
            id=r["id"],
            recipe_id=r["recipe_id"],
            quantity=r["quantity"],
            unit=r["unit"],
            item=r["item"],
            grocery_section=r["grocery_section"],
            sort_order=r["sort_order"],
        )
        for r in ing_rows
    ]

    return RecipeResponse(
        id=row["id"],
        title=row["title"],
        description=row["description"] or "",
        category=row["category"],
        prep_time_minutes=row["prep_time_minutes"] or 0,
        cook_time_minutes=row["cook_time_minutes"] or 0,
        servings=row["servings"] or 1,
        instructions=row["instructions"] or "",
        tags=row["tags"] or "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        ingredients=ingredients,
    )


@router.get("/recipes", response_model=list[RecipeListItem])
async def list_recipes(
    category: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
):
    async with get_db() as db:
        query = (
            "SELECT DISTINCT r.id, r.title, r.description, r.category, "
            "r.prep_time_minutes, r.cook_time_minutes, r.tags "
            "FROM recipes r LEFT JOIN ingredients i ON i.recipe_id = r.id "
            "WHERE 1=1"
        )
        params: list = []

        if category:
            query += " AND r.category = ?"
            params.append(category)

        if tag:
            query += " AND (r.tags = ? OR r.tags LIKE ? OR r.tags LIKE ? OR r.tags LIKE ?)"
            params.extend([tag, f"{tag},%", f"%,{tag}", f"%,{tag},%"])

        if search:
            query += " AND (r.title LIKE ? OR r.description LIKE ? OR i.item LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY r.title"
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        return [
            RecipeListItem(
                id=r["id"],
                title=r["title"],
                description=r["description"] or "",
                category=r["category"],
                prep_time_minutes=r["prep_time_minutes"] or 0,
                cook_time_minutes=r["cook_time_minutes"] or 0,
                tags=r["tags"] or "",
            )
            for r in rows
        ]


@router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(recipe_id: int):
    async with get_db() as db:
        return await _fetch_recipe(db, recipe_id)


@router.post("/recipes", response_model=RecipeResponse, status_code=201)
async def create_recipe(recipe: RecipeCreate):
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO recipes
                (title, description, category, prep_time_minutes,
                 cook_time_minutes, servings, instructions, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recipe.title,
                recipe.description,
                recipe.category,
                recipe.prep_time_minutes,
                recipe.cook_time_minutes,
                recipe.servings,
                recipe.instructions,
                recipe.tags,
            ),
        )
        recipe_id = cursor.lastrowid

        for sort_order, ingredient in enumerate(recipe.ingredients):
            await db.execute(
                """
                INSERT INTO ingredients
                    (recipe_id, quantity, unit, item, grocery_section, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    recipe_id,
                    ingredient.quantity,
                    ingredient.unit,
                    ingredient.item,
                    ingredient.grocery_section,
                    sort_order,
                ),
            )

        await db.commit()
        return await _fetch_recipe(db, recipe_id)


@router.put("/recipes/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(recipe_id: int, recipe: RecipeCreate):
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Recipe not found")

        await db.execute(
            """
            UPDATE recipes SET
                title = ?,
                description = ?,
                category = ?,
                prep_time_minutes = ?,
                cook_time_minutes = ?,
                servings = ?,
                instructions = ?,
                tags = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                recipe.title,
                recipe.description,
                recipe.category,
                recipe.prep_time_minutes,
                recipe.cook_time_minutes,
                recipe.servings,
                recipe.instructions,
                recipe.tags,
                recipe_id,
            ),
        )

        await db.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))

        for sort_order, ingredient in enumerate(recipe.ingredients):
            await db.execute(
                """
                INSERT INTO ingredients
                    (recipe_id, quantity, unit, item, grocery_section, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    recipe_id,
                    ingredient.quantity,
                    ingredient.unit,
                    ingredient.item,
                    ingredient.grocery_section,
                    sort_order,
                ),
            )

        await db.commit()
        return await _fetch_recipe(db, recipe_id)


@router.delete("/recipes/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        await db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        await db.commit()
