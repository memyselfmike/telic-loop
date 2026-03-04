"""
Meal Plan API routes
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from backend.database import get_connection
from backend.models import MealPlan, MealPlanCreate, MealPlanWithRecipe

router = APIRouter(prefix="/api/meals", tags=["meals"])


def validate_monday(week_start: str) -> None:
    """Validate that week_start is a Monday"""
    try:
        date = datetime.strptime(week_start, "%Y-%m-%d")
        if date.weekday() != 0:  # 0 = Monday
            raise HTTPException(
                status_code=400,
                detail=f"week_start must be a Monday. {week_start} is a {date.strftime('%A')}"
            )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="week_start must be in YYYY-MM-DD format"
        )


@router.get("/", response_model=List[MealPlanWithRecipe])
async def get_week_meals(
    week: str = Query(..., description="Week start date (Monday) in YYYY-MM-DD format")
):
    """
    Get all meal assignments for a specific week
    Returns meal plans with recipe details (title, prep_time, cook_time)
    """
    validate_monday(week)

    conn = get_connection()
    cursor = conn.cursor()

    # Fetch meal plans with recipe details
    cursor.execute("""
        SELECT
            mp.id,
            mp.week_start,
            mp.day_of_week,
            mp.meal_slot,
            mp.recipe_id,
            r.title as recipe_title,
            r.prep_time_minutes,
            r.cook_time_minutes
        FROM meal_plans mp
        JOIN recipes r ON mp.recipe_id = r.id
        WHERE mp.week_start = ?
        ORDER BY mp.day_of_week, mp.meal_slot
    """, (week,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "week_start": row["week_start"],
            "day_of_week": row["day_of_week"],
            "meal_slot": row["meal_slot"],
            "recipe_id": row["recipe_id"],
            "recipe_title": row["recipe_title"],
            "prep_time_minutes": row["prep_time_minutes"],
            "cook_time_minutes": row["cook_time_minutes"]
        })

    return results


@router.put("/", response_model=MealPlanWithRecipe)
async def assign_meal(meal_plan: MealPlanCreate):
    """
    Assign recipe to a meal slot (upsert)
    If slot already has a recipe, it will be replaced
    """
    validate_monday(meal_plan.week_start)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if recipe exists
        cursor.execute("SELECT id FROM recipes WHERE id = ?", (meal_plan.recipe_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Recipe not found")

        # Check if slot already has an assignment
        cursor.execute("""
            SELECT id FROM meal_plans
            WHERE week_start = ? AND day_of_week = ? AND meal_slot = ?
        """, (meal_plan.week_start, meal_plan.day_of_week, meal_plan.meal_slot))

        existing = cursor.fetchone()

        if existing:
            # Update existing assignment
            cursor.execute("""
                UPDATE meal_plans
                SET recipe_id = ?
                WHERE week_start = ? AND day_of_week = ? AND meal_slot = ?
            """, (
                meal_plan.recipe_id,
                meal_plan.week_start,
                meal_plan.day_of_week,
                meal_plan.meal_slot
            ))
            meal_plan_id = existing["id"]
        else:
            # Insert new assignment
            cursor.execute("""
                INSERT INTO meal_plans (week_start, day_of_week, meal_slot, recipe_id)
                VALUES (?, ?, ?, ?)
            """, (
                meal_plan.week_start,
                meal_plan.day_of_week,
                meal_plan.meal_slot,
                meal_plan.recipe_id
            ))
            meal_plan_id = cursor.lastrowid

        conn.commit()

        # Fetch and return the meal plan with recipe details
        cursor.execute("""
            SELECT
                mp.id,
                mp.week_start,
                mp.day_of_week,
                mp.meal_slot,
                mp.recipe_id,
                r.title as recipe_title,
                r.prep_time_minutes,
                r.cook_time_minutes
            FROM meal_plans mp
            JOIN recipes r ON mp.recipe_id = r.id
            WHERE mp.id = ?
        """, (meal_plan_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return {
            "id": row["id"],
            "week_start": row["week_start"],
            "day_of_week": row["day_of_week"],
            "meal_slot": row["meal_slot"],
            "recipe_id": row["recipe_id"],
            "recipe_title": row["recipe_title"],
            "prep_time_minutes": row["prep_time_minutes"],
            "cook_time_minutes": row["cook_time_minutes"]
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to assign meal: {str(e)}")


@router.delete("/{meal_plan_id}")
async def clear_meal_slot(meal_plan_id: int):
    """
    Remove recipe assignment from a meal slot
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if meal plan exists
        cursor.execute("SELECT id FROM meal_plans WHERE id = ?", (meal_plan_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Meal plan entry not found")

        # Delete the assignment
        cursor.execute("DELETE FROM meal_plans WHERE id = ?", (meal_plan_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Meal slot cleared successfully"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to clear meal slot: {str(e)}")
