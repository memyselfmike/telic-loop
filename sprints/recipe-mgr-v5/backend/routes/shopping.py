"""
Shopping List API routes with unit normalization
"""
from typing import List, Dict, Tuple
from fastapi import APIRouter, HTTPException
from backend.database import get_connection
from backend.models import (
    ShoppingList, ShoppingListCreate, ShoppingListWithItems,
    ShoppingItem, ShoppingItemCreate
)

router = APIRouter(prefix="/api/shopping", tags=["shopping"])


# Unit conversion factors
VOLUME_CONVERSIONS = {
    'tsp': 1.0,
    'tbsp': 3.0,  # 1 tbsp = 3 tsp
    'cup': 48.0,  # 1 cup = 48 tsp
}

WEIGHT_CONVERSIONS = {
    'oz': 1.0,
    'lb': 16.0,  # 1 lb = 16 oz
}

COUNT_UNITS = {'whole', 'piece', 'each', 'unit'}


def normalize_quantity(quantity: float, unit: str) -> Tuple[float, str]:
    """
    Normalize quantity to largest applicable unit >= 1
    Returns (normalized_quantity, normalized_unit)
    Per PRD 2.2: Store as single decimal value with one decimal place
    """
    # Volume conversion (tsp -> tbsp -> cup)
    if unit.lower() in VOLUME_CONVERSIONS:
        base_tsp = quantity * VOLUME_CONVERSIONS[unit.lower()]

        # Try cup first
        if base_tsp >= VOLUME_CONVERSIONS['cup']:
            cups = base_tsp / VOLUME_CONVERSIONS['cup']
            return (round(cups, 1), 'cup')

        # Try tbsp
        if base_tsp >= VOLUME_CONVERSIONS['tbsp']:
            tbsp = base_tsp / VOLUME_CONVERSIONS['tbsp']
            return (round(tbsp, 1), 'tbsp')

        # Keep as tsp
        return (round(quantity, 1), unit)

    # Weight conversion (oz -> lb)
    elif unit.lower() in WEIGHT_CONVERSIONS:
        base_oz = quantity * WEIGHT_CONVERSIONS[unit.lower()]

        # Try lb
        if base_oz >= WEIGHT_CONVERSIONS['lb']:
            lbs = base_oz / WEIGHT_CONVERSIONS['lb']
            return (round(lbs, 1), 'lb')

        # Keep as oz
        return (round(quantity, 1), unit)

    # No conversion needed
    else:
        return (round(quantity, 1), unit)


def aggregate_ingredients(conn, week_start: str) -> Dict[str, List[Dict]]:
    """
    Aggregate ingredients from all meal plans for the week
    Groups by grocery_section and normalizes compatible units
    """
    cursor = conn.cursor()

    # Get all ingredients from recipes in this week's meal plan
    cursor.execute("""
        SELECT
            i.item,
            i.quantity,
            i.unit,
            i.grocery_section
        FROM meal_plans mp
        JOIN ingredients i ON mp.recipe_id = i.recipe_id
        WHERE mp.week_start = ?
        ORDER BY i.item, i.unit
    """, (week_start,))

    rows = cursor.fetchall()
    cursor.close()

    # Group by (item, unit, grocery_section)
    item_groups: Dict[Tuple[str, str, str], float] = {}

    for row in rows:
        item = row["item"].lower().strip()
        unit = row["unit"].lower().strip()
        section = row["grocery_section"]
        quantity = row["quantity"]

        # Normalize count units to "whole"
        if unit in COUNT_UNITS:
            unit = "whole"

        key = (item, unit, section)
        item_groups[key] = item_groups.get(key, 0.0) + quantity

    # Normalize units within each item/section
    # Group by (item, section) to combine compatible units
    item_section_groups: Dict[Tuple[str, str], List[Tuple[float, str]]] = {}

    for (item, unit, section), quantity in item_groups.items():
        key = (item, section)
        if key not in item_section_groups:
            item_section_groups[key] = []
        item_section_groups[key].append((quantity, unit))

    # Combine compatible units and normalize
    normalized_items: Dict[str, List[Dict]] = {}

    for (item, section), quantities in item_section_groups.items():
        # Try to combine volume units
        volume_total_tsp = 0.0
        volume_found = False
        other_quantities = []

        for qty, unit in quantities:
            if unit in VOLUME_CONVERSIONS:
                volume_total_tsp += qty * VOLUME_CONVERSIONS[unit]
                volume_found = True
            else:
                other_quantities.append((qty, unit))

        # Add normalized volume
        if volume_found:
            norm_qty, norm_unit = normalize_quantity(volume_total_tsp / VOLUME_CONVERSIONS['tsp'], 'tsp')
            if section not in normalized_items:
                normalized_items[section] = []
            normalized_items[section].append({
                "item": item,
                "quantity": norm_qty,
                "unit": norm_unit,
                "grocery_section": section
            })

        # Try to combine weight units
        weight_total_oz = 0.0
        weight_found = False
        remaining_quantities = []

        for qty, unit in other_quantities:
            if unit in WEIGHT_CONVERSIONS:
                weight_total_oz += qty * WEIGHT_CONVERSIONS[unit]
                weight_found = True
            else:
                remaining_quantities.append((qty, unit))

        # Add normalized weight
        if weight_found:
            norm_qty, norm_unit = normalize_quantity(weight_total_oz / WEIGHT_CONVERSIONS['oz'], 'oz')
            if section not in normalized_items:
                normalized_items[section] = []
            normalized_items[section].append({
                "item": item,
                "quantity": norm_qty,
                "unit": norm_unit,
                "grocery_section": section
            })

        # Add remaining (non-convertible) units
        for qty, unit in remaining_quantities:
            if section not in normalized_items:
                normalized_items[section] = []
            normalized_items[section].append({
                "item": item,
                "quantity": round(qty, 1),
                "unit": unit,
                "grocery_section": section
            })

    return normalized_items


@router.post("/generate", response_model=ShoppingListWithItems)
async def generate_shopping_list(request: ShoppingListCreate):
    """
    Generate shopping list from week's meal plan
    Aggregates ingredients, normalizes units, groups by grocery section
    Replaces any existing list
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Delete existing shopping lists (replace old one)
        cursor.execute("DELETE FROM shopping_lists")
        conn.commit()

        # Aggregate and normalize ingredients
        normalized_items = aggregate_ingredients(conn, request.week_start)

        # Create new shopping list
        cursor.execute("""
            INSERT INTO shopping_lists (week_start)
            VALUES (?)
        """, (request.week_start,))

        list_id = cursor.lastrowid

        # Insert shopping items
        for section, items in normalized_items.items():
            for item_data in items:
                cursor.execute("""
                    INSERT INTO shopping_items (
                        list_id, item, quantity, unit, grocery_section, source
                    )
                    VALUES (?, ?, ?, ?, ?, 'recipe')
                """, (
                    list_id,
                    item_data["item"],
                    item_data["quantity"],
                    item_data["unit"],
                    item_data["grocery_section"]
                ))

        conn.commit()

        # Fetch and return the created list
        cursor.close()
        conn.close()

        return await get_current_list()

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to generate shopping list: {str(e)}")


@router.get("/current", response_model=ShoppingListWithItems)
async def get_current_list():
    """
    Get the current shopping list with all items
    Returns 404 if no list exists
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get the most recent shopping list
    cursor.execute("""
        SELECT * FROM shopping_lists
        ORDER BY created_at DESC
        LIMIT 1
    """)

    list_row = cursor.fetchone()

    if not list_row:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="No shopping list found")

    list_id = list_row["id"]

    # Get all items for this list
    cursor.execute("""
        SELECT * FROM shopping_items
        WHERE list_id = ?
        ORDER BY grocery_section, item
    """, (list_id,))

    items = []
    for item_row in cursor.fetchall():
        items.append({
            "id": item_row["id"],
            "list_id": item_row["list_id"],
            "item": item_row["item"],
            "quantity": item_row["quantity"],
            "unit": item_row["unit"],
            "grocery_section": item_row["grocery_section"],
            "checked": item_row["checked"],
            "source": item_row["source"]
        })

    cursor.close()
    conn.close()

    return {
        "id": list_row["id"],
        "week_start": list_row["week_start"],
        "created_at": list_row["created_at"],
        "items": items
    }


@router.patch("/items/{item_id}")
async def toggle_item_checked(item_id: int):
    """
    Toggle checked status of a shopping item
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if item exists
        cursor.execute("SELECT checked FROM shopping_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Shopping item not found")

        # Toggle checked status
        new_checked = 0 if row["checked"] == 1 else 1

        cursor.execute("""
            UPDATE shopping_items
            SET checked = ?
            WHERE id = ?
        """, (new_checked, item_id))

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Item checked status updated", "checked": new_checked}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to update item: {str(e)}")


@router.post("/items", response_model=ShoppingItem, status_code=201)
async def add_manual_item(item: ShoppingItemCreate):
    """
    Add a manual item to the current shopping list
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get current list
        cursor.execute("""
            SELECT id FROM shopping_lists
            ORDER BY created_at DESC
            LIMIT 1
        """)

        list_row = cursor.fetchone()

        if not list_row:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="No shopping list found. Generate one first.")

        list_id = list_row["id"]

        # Insert manual item
        cursor.execute("""
            INSERT INTO shopping_items (
                list_id, item, quantity, unit, grocery_section, source
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            list_id,
            item.item,
            item.quantity,
            item.unit,
            item.grocery_section,
            item.source
        ))

        item_id = cursor.lastrowid
        conn.commit()

        # Fetch and return the created item
        cursor.execute("SELECT * FROM shopping_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            "id": row["id"],
            "list_id": row["list_id"],
            "item": row["item"],
            "quantity": row["quantity"],
            "unit": row["unit"],
            "grocery_section": row["grocery_section"],
            "checked": row["checked"],
            "source": row["source"]
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to add item: {str(e)}")


@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """
    Remove an item from the shopping list
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if item exists
        cursor.execute("SELECT id FROM shopping_items WHERE id = ?", (item_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Shopping item not found")

        # Delete item
        cursor.execute("DELETE FROM shopping_items WHERE id = ?", (item_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Item deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete item: {str(e)}")
