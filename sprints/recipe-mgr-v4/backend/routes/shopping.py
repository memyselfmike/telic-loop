"""Shopping List API routes"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Tuple
import sqlite3
from backend.database import get_db
from backend.models import (
    ShoppingList,
    ShoppingListGenerate,
    ShoppingItem,
    ShoppingItemCreate
)


router = APIRouter(prefix="/api/shopping", tags=["shopping"])


# Unit conversion factors
VOLUME_CONVERSIONS = {
    'tsp': 1,
    'tbsp': 3,
    'cup': 48  # 3 tsp = 1 tbsp, 16 tbsp = 1 cup, so 48 tsp = 1 cup
}

WEIGHT_CONVERSIONS = {
    'oz': 1,
    'lb': 16
}

COUNT_UNITS = {'whole', 'piece', 'each', 'item'}


def normalize_unit(quantity: float, unit: str) -> Tuple[float, str]:
    """
    Normalize units using decimal format only.
    Upconvert to the largest unit yielding quantity >= 1.
    Round to one decimal place.
    """
    unit_lower = unit.lower()

    # Volume conversions
    if unit_lower in VOLUME_CONVERSIONS:
        # Convert to tsp as base
        tsp_amount = quantity * VOLUME_CONVERSIONS[unit_lower]

        # Try upconverting: tsp -> tbsp -> cup
        if tsp_amount >= VOLUME_CONVERSIONS['cup']:
            # Convert to cups
            cups = tsp_amount / VOLUME_CONVERSIONS['cup']
            return round(cups, 1), 'cup'
        elif tsp_amount >= VOLUME_CONVERSIONS['tbsp']:
            # Convert to tbsp
            tbsp = tsp_amount / VOLUME_CONVERSIONS['tbsp']
            return round(tbsp, 1), 'tbsp'
        else:
            # Keep as tsp
            return round(tsp_amount, 1), 'tsp'

    # Weight conversions
    if unit_lower in WEIGHT_CONVERSIONS:
        # Convert to oz as base
        oz_amount = quantity * WEIGHT_CONVERSIONS[unit_lower]

        # Try upconverting: oz -> lb
        if oz_amount >= WEIGHT_CONVERSIONS['lb']:
            lbs = oz_amount / WEIGHT_CONVERSIONS['lb']
            return round(lbs, 1), 'lb'
        else:
            return round(oz_amount, 1), 'oz'

    # Count units - keep as is
    if unit_lower in COUNT_UNITS:
        return round(quantity, 1), 'whole'

    # Unknown units - keep original
    return round(quantity, 1), unit


def aggregate_ingredients(conn: sqlite3.Connection, week_start: str) -> Dict[str, Dict[str, List[Tuple[float, str]]]]:
    """
    Aggregate ingredients from all meals in a week.
    Returns: {item_name: {section: [(quantity, unit), ...]}}
    """
    cursor = conn.cursor()

    # Get all ingredients for recipes in the meal plan for this week
    cursor.execute(
        """SELECT
            i.item,
            i.quantity,
            i.unit,
            i.grocery_section
           FROM meal_plans mp
           JOIN ingredients i ON mp.recipe_id = i.recipe_id
           WHERE mp.week_start = ?""",
        (week_start,)
    )

    # Aggregate by item name (case-insensitive)
    aggregated = {}
    for row in cursor.fetchall():
        item = row["item"].lower().strip()
        quantity = row["quantity"]
        unit = row["unit"]
        section = row["grocery_section"]

        if item not in aggregated:
            aggregated[item] = {}

        if section not in aggregated[item]:
            aggregated[item][section] = []

        aggregated[item][section].append((quantity, unit))

    return aggregated


def merge_quantities(quantities: List[Tuple[float, str]]) -> List[Tuple[float, str]]:
    """
    Merge quantities with unit normalization.
    Returns list of (quantity, unit) tuples - one per unit family.
    When incompatible unit families are present for the same item,
    multiple rows are returned (e.g., both volume and weight).
    """
    if not quantities:
        return []

    # Group by unit family
    volume_total_tsp = 0
    weight_total_oz = 0
    count_total = 0
    other_units = {}

    for qty, unit in quantities:
        unit_lower = unit.lower()

        if unit_lower in VOLUME_CONVERSIONS:
            volume_total_tsp += qty * VOLUME_CONVERSIONS[unit_lower]
        elif unit_lower in WEIGHT_CONVERSIONS:
            weight_total_oz += qty * WEIGHT_CONVERSIONS[unit_lower]
        elif unit_lower in COUNT_UNITS:
            count_total += qty
        else:
            # Keep other units separate
            if unit not in other_units:
                other_units[unit] = 0
            other_units[unit] += qty

    # Return all non-zero aggregates as separate entries
    result = []
    if volume_total_tsp > 0:
        result.append(normalize_unit(volume_total_tsp, 'tsp'))
    if weight_total_oz > 0:
        result.append(normalize_unit(weight_total_oz, 'oz'))
    if count_total > 0:
        result.append(normalize_unit(count_total, 'whole'))
    for unit, qty in other_units.items():
        if qty > 0:
            result.append((round(qty, 1), unit))

    return result


@router.post("/generate", response_model=ShoppingList, status_code=201)
async def generate_shopping_list(request: ShoppingListGenerate):
    """Generate shopping list from weekly meal plan with unit normalization"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if there are any meals planned for this week
        cursor.execute(
            "SELECT COUNT(*) as count FROM meal_plans WHERE week_start = ?",
            (request.week_start,)
        )
        if cursor.fetchone()["count"] == 0:
            raise HTTPException(
                status_code=400,
                detail="No meals planned for this week"
            )

        # Delete existing shopping list for this week (if any)
        cursor.execute(
            "DELETE FROM shopping_lists WHERE week_start = ?",
            (request.week_start,)
        )

        # Create new shopping list
        cursor.execute(
            "INSERT INTO shopping_lists (week_start) VALUES (?)",
            (request.week_start,)
        )
        list_id = cursor.lastrowid

        # Aggregate ingredients
        aggregated = aggregate_ingredients(conn, request.week_start)

        # Merge and normalize quantities, then insert shopping items
        for item_name, sections in aggregated.items():
            for section, quantities in sections.items():
                merged_quantities = merge_quantities(quantities)

                # Insert one row per unit family (handles incompatible units)
                for qty, unit in merged_quantities:
                    if qty > 0:
                        cursor.execute(
                            """INSERT INTO shopping_items
                               (list_id, item, quantity, unit, grocery_section, source)
                               VALUES (?, ?, ?, ?, ?, 'recipe')""",
                            (list_id, item_name, qty, unit, section)
                        )

        conn.commit()

        # Return the created shopping list with items
        return await get_current_shopping_list()


@router.get("/current", response_model=ShoppingList)
async def get_current_shopping_list():
    """Get the most recent shopping list with items"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get most recent shopping list
        cursor.execute(
            "SELECT * FROM shopping_lists ORDER BY created_at DESC LIMIT 1"
        )
        list_row = cursor.fetchone()

        if not list_row:
            raise HTTPException(status_code=404, detail="No shopping list found")

        list_id = list_row["id"]

        # Get items, ordered by section and checked status
        cursor.execute(
            """SELECT * FROM shopping_items
               WHERE list_id = ?
               ORDER BY grocery_section, checked, item""",
            (list_id,)
        )
        item_rows = cursor.fetchall()

        items = []
        for row in item_rows:
            items.append(ShoppingItem(
                id=row["id"],
                list_id=row["list_id"],
                item=row["item"],
                quantity=row["quantity"],
                unit=row["unit"],
                grocery_section=row["grocery_section"],
                checked=bool(row["checked"]),
                source=row["source"]
            ))

        return ShoppingList(
            id=list_row["id"],
            week_start=list_row["week_start"],
            created_at=list_row["created_at"],
            items=items
        )


@router.patch("/items/{item_id}", response_model=ShoppingItem)
async def toggle_item_checked(item_id: int):
    """Toggle the checked status of a shopping item"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get current item
        cursor.execute("SELECT * FROM shopping_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Shopping item not found")

        # Toggle checked
        new_checked = 0 if row["checked"] else 1
        cursor.execute(
            "UPDATE shopping_items SET checked = ? WHERE id = ?",
            (new_checked, item_id)
        )
        conn.commit()

        # Return updated item
        cursor.execute("SELECT * FROM shopping_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()

        return ShoppingItem(
            id=row["id"],
            list_id=row["list_id"],
            item=row["item"],
            quantity=row["quantity"],
            unit=row["unit"],
            grocery_section=row["grocery_section"],
            checked=bool(row["checked"]),
            source=row["source"]
        )


@router.post("/items", response_model=ShoppingItem, status_code=201)
async def add_manual_item(item: ShoppingItemCreate):
    """Add a manual item to the current shopping list"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get current shopping list
        cursor.execute(
            "SELECT id FROM shopping_lists ORDER BY created_at DESC LIMIT 1"
        )
        list_row = cursor.fetchone()

        if not list_row:
            raise HTTPException(
                status_code=400,
                detail="No shopping list exists. Generate one first."
            )

        list_id = list_row["id"]

        # Insert manual item
        cursor.execute(
            """INSERT INTO shopping_items
               (list_id, item, quantity, unit, grocery_section, checked, source)
               VALUES (?, ?, ?, ?, ?, ?, 'manual')""",
            (
                list_id,
                item.item,
                item.quantity,
                item.unit,
                item.grocery_section,
                1 if item.checked else 0
            )
        )
        item_id = cursor.lastrowid
        conn.commit()

        # Return created item
        cursor.execute("SELECT * FROM shopping_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()

        return ShoppingItem(
            id=row["id"],
            list_id=row["list_id"],
            item=row["item"],
            quantity=row["quantity"],
            unit=row["unit"],
            grocery_section=row["grocery_section"],
            checked=bool(row["checked"]),
            source=row["source"]
        )


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int):
    """Remove an item from the shopping list"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if item exists
        cursor.execute("SELECT id FROM shopping_items WHERE id = ?", (item_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Shopping item not found")

        # Delete item
        cursor.execute("DELETE FROM shopping_items WHERE id = ?", (item_id,))
        conn.commit()

        return None
