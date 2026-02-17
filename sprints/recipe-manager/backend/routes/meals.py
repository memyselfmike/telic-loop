from fastapi import APIRouter, HTTPException, Query
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models import MealPlanCreate, MealPlanResponse

router = APIRouter()


@router.get("/meals", response_model=list[MealPlanResponse])
async def get_meals(week: str = Query(..., description="ISO date for week start")):
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT
                mp.id,
                mp.week_start,
                mp.day_of_week,
                mp.meal_slot,
                mp.recipe_id,
                r.title AS recipe_title,
                (r.prep_time_minutes + r.cook_time_minutes) AS total_time
            FROM meal_plans mp
            JOIN recipes r ON r.id = mp.recipe_id
            WHERE mp.week_start = ?
            ORDER BY mp.day_of_week, mp.meal_slot
            """,
            (week,),
        )
        rows = await cursor.fetchall()
        return [
            MealPlanResponse(
                id=row["id"],
                week_start=row["week_start"],
                day_of_week=row["day_of_week"],
                meal_slot=row["meal_slot"],
                recipe_id=row["recipe_id"],
                recipe_title=row["recipe_title"] or "",
                total_time=row["total_time"] or 0,
            )
            for row in rows
        ]


@router.put("/meals", response_model=MealPlanResponse, status_code=200)
async def upsert_meal(meal: MealPlanCreate):
    async with get_db() as db:
        # Verify recipe exists
        cursor = await db.execute("SELECT id FROM recipes WHERE id = ?", (meal.recipe_id,))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Recipe not found")

        # Remove any existing entry for this slot
        await db.execute(
            """
            DELETE FROM meal_plans
            WHERE week_start = ? AND day_of_week = ? AND meal_slot = ?
            """,
            (meal.week_start, meal.day_of_week, meal.meal_slot),
        )

        cursor = await db.execute(
            """
            INSERT INTO meal_plans (week_start, day_of_week, meal_slot, recipe_id)
            VALUES (?, ?, ?, ?)
            """,
            (meal.week_start, meal.day_of_week, meal.meal_slot, meal.recipe_id),
        )
        meal_id = cursor.lastrowid
        await db.commit()

        cursor = await db.execute(
            """
            SELECT
                mp.id,
                mp.week_start,
                mp.day_of_week,
                mp.meal_slot,
                mp.recipe_id,
                r.title AS recipe_title,
                (r.prep_time_minutes + r.cook_time_minutes) AS total_time
            FROM meal_plans mp
            JOIN recipes r ON r.id = mp.recipe_id
            WHERE mp.id = ?
            """,
            (meal_id,),
        )
        row = await cursor.fetchone()
        return MealPlanResponse(
            id=row["id"],
            week_start=row["week_start"],
            day_of_week=row["day_of_week"],
            meal_slot=row["meal_slot"],
            recipe_id=row["recipe_id"],
            recipe_title=row["recipe_title"] or "",
            total_time=row["total_time"] or 0,
        )


@router.delete("/meals/{meal_id}", status_code=204)
async def delete_meal(meal_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM meal_plans WHERE id = ?", (meal_id,))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Meal plan entry not found")
        await db.execute("DELETE FROM meal_plans WHERE id = ?", (meal_id,))
        await db.commit()
