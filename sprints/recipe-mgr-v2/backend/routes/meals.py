from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from database import get_connection

router = APIRouter(prefix="/api/meals", tags=["meals"])


class MealPlanAssignment(BaseModel):
    """Model for assigning a recipe to a meal slot."""
    week_start: str = Field(..., description="ISO date string (YYYY-MM-DD), must be a Monday")
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    meal_slot: str = Field(..., description="One of: breakfast, lunch, dinner, snack")
    recipe_id: int = Field(..., gt=0, description="Recipe ID to assign")


class MealPlanResponse(BaseModel):
    """Model for meal plan response including recipe details."""
    id: int
    week_start: str
    day_of_week: int
    meal_slot: str
    recipe_id: int
    recipe_title: str
    prep_time_minutes: int
    cook_time_minutes: int


@router.get("", response_model=list[MealPlanResponse])
def get_meal_plan(week: str = Query(..., description="ISO date for week start (Monday)")):
    """
    Get meal plan for a specific week.

    Returns all assigned meal slots with recipe details (title, prep+cook time).
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Join meal_plans with recipes to get title and times
        cursor.execute("""
            SELECT mp.id, mp.week_start, mp.day_of_week, mp.meal_slot, mp.recipe_id,
                   r.title as recipe_title, r.prep_time_minutes, r.cook_time_minutes
            FROM meal_plans mp
            JOIN recipes r ON mp.recipe_id = r.id
            WHERE mp.week_start = ?
            ORDER BY mp.day_of_week,
                     CASE mp.meal_slot
                         WHEN 'breakfast' THEN 1
                         WHEN 'lunch' THEN 2
                         WHEN 'dinner' THEN 3
                         WHEN 'snack' THEN 4
                     END
        """, (week,))

        rows = cursor.fetchall()
        conn.close()

        return [
            MealPlanResponse(
                id=row["id"],
                week_start=row["week_start"],
                day_of_week=row["day_of_week"],
                meal_slot=row["meal_slot"],
                recipe_id=row["recipe_id"],
                recipe_title=row["recipe_title"],
                prep_time_minutes=row["prep_time_minutes"],
                cook_time_minutes=row["cook_time_minutes"]
            )
            for row in rows
        ]

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to fetch meal plan: {str(e)}")


@router.put("", response_model=MealPlanResponse, status_code=201)
def assign_meal(assignment: MealPlanAssignment):
    """
    Assign a recipe to a meal slot (upsert).

    If the slot already has a recipe assigned, it will be replaced.
    Uses UNIQUE constraint on (week_start, day_of_week, meal_slot) for upsert behavior.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Verify recipe exists
        cursor.execute("SELECT id FROM recipes WHERE id = ?", (assignment.recipe_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=404,
                detail=f"Recipe {assignment.recipe_id} not found"
            )

        # Upsert: INSERT with ON CONFLICT REPLACE
        cursor.execute("""
            INSERT INTO meal_plans (week_start, day_of_week, meal_slot, recipe_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(week_start, day_of_week, meal_slot)
            DO UPDATE SET recipe_id = excluded.recipe_id
        """, (
            assignment.week_start,
            assignment.day_of_week,
            assignment.meal_slot,
            assignment.recipe_id
        ))

        conn.commit()

        # Fetch the created/updated meal plan with recipe details
        cursor.execute("""
            SELECT mp.id, mp.week_start, mp.day_of_week, mp.meal_slot, mp.recipe_id,
                   r.title as recipe_title, r.prep_time_minutes, r.cook_time_minutes
            FROM meal_plans mp
            JOIN recipes r ON mp.recipe_id = r.id
            WHERE mp.week_start = ? AND mp.day_of_week = ? AND mp.meal_slot = ?
        """, (assignment.week_start, assignment.day_of_week, assignment.meal_slot))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=500, detail="Failed to retrieve created meal plan")

        return MealPlanResponse(
            id=row["id"],
            week_start=row["week_start"],
            day_of_week=row["day_of_week"],
            meal_slot=row["meal_slot"],
            recipe_id=row["recipe_id"],
            recipe_title=row["recipe_title"],
            prep_time_minutes=row["prep_time_minutes"],
            cook_time_minutes=row["cook_time_minutes"]
        )

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to assign meal: {str(e)}")


@router.delete("/{meal_id}", status_code=204)
def remove_meal(meal_id: int):
    """
    Remove a recipe from a meal slot.

    Clears the slot, making it available for a new assignment.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if meal plan exists
        cursor.execute("SELECT id FROM meal_plans WHERE id = ?", (meal_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Meal plan {meal_id} not found")

        # Delete meal plan
        cursor.execute("DELETE FROM meal_plans WHERE id = ?", (meal_id,))
        conn.commit()
        conn.close()

        return None  # 204 No Content

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to remove meal: {str(e)}")
