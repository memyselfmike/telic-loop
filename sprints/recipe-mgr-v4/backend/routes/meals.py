"""Meal Plan API routes"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import sqlite3
from backend.database import get_db
from backend.models import MealPlan, MealPlanCreate, MealPlanWithRecipe


router = APIRouter(prefix="/api/meals", tags=["meals"])


@router.get("", response_model=List[MealPlanWithRecipe])
async def get_meal_plan(week: str = Query(..., description="Week start date (ISO format, Monday)")):
    """Get meal plan for a specific week with recipe details"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get meal plans with recipe details joined
        cursor.execute(
            """SELECT
                mp.id, mp.week_start, mp.day_of_week, mp.meal_slot, mp.recipe_id,
                r.title as recipe_title,
                r.prep_time_minutes,
                r.cook_time_minutes
               FROM meal_plans mp
               JOIN recipes r ON mp.recipe_id = r.id
               WHERE mp.week_start = ?
               ORDER BY mp.day_of_week, mp.meal_slot""",
            (week,)
        )
        rows = cursor.fetchall()

        meal_plans = []
        for row in rows:
            meal_plans.append(MealPlanWithRecipe(
                id=row["id"],
                week_start=row["week_start"],
                day_of_week=row["day_of_week"],
                meal_slot=row["meal_slot"],
                recipe_id=row["recipe_id"],
                recipe_title=row["recipe_title"],
                prep_time_minutes=row["prep_time_minutes"],
                cook_time_minutes=row["cook_time_minutes"]
            ))

        return meal_plans


@router.put("", response_model=MealPlanWithRecipe)
async def assign_meal(meal_plan: MealPlanCreate):
    """Assign a recipe to a meal slot (upsert)"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if recipe exists
        cursor.execute("SELECT id FROM recipes WHERE id = ?", (meal_plan.recipe_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Recipe not found")

        try:
            # Use INSERT OR REPLACE to upsert
            cursor.execute(
                """INSERT OR REPLACE INTO meal_plans
                   (week_start, day_of_week, meal_slot, recipe_id)
                   VALUES (?, ?, ?, ?)""",
                (
                    meal_plan.week_start,
                    meal_plan.day_of_week,
                    meal_plan.meal_slot,
                    meal_plan.recipe_id
                )
            )
            meal_plan_id = cursor.lastrowid

            conn.commit()

            # Get the created/updated meal plan with recipe details
            cursor.execute(
                """SELECT
                    mp.id, mp.week_start, mp.day_of_week, mp.meal_slot, mp.recipe_id,
                    r.title as recipe_title,
                    r.prep_time_minutes,
                    r.cook_time_minutes
                   FROM meal_plans mp
                   JOIN recipes r ON mp.recipe_id = r.id
                   WHERE mp.week_start = ? AND mp.day_of_week = ? AND mp.meal_slot = ?""",
                (meal_plan.week_start, meal_plan.day_of_week, meal_plan.meal_slot)
            )
            row = cursor.fetchone()

            return MealPlanWithRecipe(
                id=row["id"],
                week_start=row["week_start"],
                day_of_week=row["day_of_week"],
                meal_slot=row["meal_slot"],
                recipe_id=row["recipe_id"],
                recipe_title=row["recipe_title"],
                prep_time_minutes=row["prep_time_minutes"],
                cook_time_minutes=row["cook_time_minutes"]
            )

        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{meal_plan_id}", status_code=204)
async def clear_meal_slot(meal_plan_id: int):
    """Remove a recipe from a meal slot"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if meal plan exists
        cursor.execute("SELECT id FROM meal_plans WHERE id = ?", (meal_plan_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Meal plan entry not found")

        # Delete meal plan entry
        cursor.execute("DELETE FROM meal_plans WHERE id = ?", (meal_plan_id,))
        conn.commit()

        return None
