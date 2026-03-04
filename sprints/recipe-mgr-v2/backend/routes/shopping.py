from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from database import get_connection
from collections import defaultdict

router = APIRouter(prefix="/api/shopping", tags=["shopping"])


class GenerateListRequest(BaseModel):
    """Request model for generating a shopping list from meal plan."""
    week_start: str = Field(..., description="ISO date for week start (Monday)")


class ManualItemCreate(BaseModel):
    """Model for manually adding an item to shopping list."""
    item: str = Field(..., min_length=1, description="Item name")
    quantity: float = Field(default=1, gt=0, description="Quantity")
    unit: str = Field(default="unit", description="Unit of measurement")
    grocery_section: str = Field(default="other", description="Grocery section")


class ShoppingItemResponse(BaseModel):
    """Model for shopping list item response."""
    id: int
    list_id: int
    item: str
    quantity: float
    unit: str
    grocery_section: str
    checked: bool


class ShoppingListResponse(BaseModel):
    """Model for shopping list response."""
    id: int
    week_start: str
    created_at: str
    items: list[ShoppingItemResponse]


# Unit normalization rules: convert smaller units to larger when possible
VOLUME_CONVERSIONS = {
    'tsp': 1,
    'tbsp': 3,  # 1 tbsp = 3 tsp
    'cup': 48,  # 1 cup = 48 tsp
}

WEIGHT_CONVERSIONS = {
    'oz': 1,
    'lb': 16,  # 1 lb = 16 oz
}


def normalize_units(items: list[dict]) -> list[dict]:
    """
    Aggregate and normalize ingredient units.

    Groups items by (item_name, grocery_section), then attempts to merge quantities
    for compatible units (tsp/tbsp/cup for volume, oz/lb for weight).

    Returns list of aggregated items with normalized units.
    """
    # Group by (item, section)
    groups = defaultdict(lambda: {'quantities': [], 'section': ''})

    for item in items:
        key = (item['item'].lower().strip(), item['grocery_section'])
        groups[key]['quantities'].append({
            'quantity': item['quantity'],
            'unit': item['unit'].lower().strip()
        })
        groups[key]['section'] = item['grocery_section']

    # Aggregate each group
    aggregated = []

    for (item_name, section), data in groups.items():
        quantities = data['quantities']

        # Try volume conversion
        volume_total_tsp = 0
        has_volume = False
        for q in quantities:
            if q['unit'] in VOLUME_CONVERSIONS:
                volume_total_tsp += q['quantity'] * VOLUME_CONVERSIONS[q['unit']]
                has_volume = True

        if has_volume:
            # Convert back to largest appropriate unit
            if volume_total_tsp >= 48:
                cups = volume_total_tsp / 48
                aggregated.append({
                    'item': item_name,
                    'quantity': round(cups, 2),
                    'unit': 'cup',
                    'grocery_section': section
                })
            elif volume_total_tsp >= 3:
                tbsp = volume_total_tsp / 3
                aggregated.append({
                    'item': item_name,
                    'quantity': round(tbsp, 2),
                    'unit': 'tbsp',
                    'grocery_section': section
                })
            else:
                aggregated.append({
                    'item': item_name,
                    'quantity': round(volume_total_tsp, 2),
                    'unit': 'tsp',
                    'grocery_section': section
                })
            continue

        # Try weight conversion
        weight_total_oz = 0
        has_weight = False
        for q in quantities:
            if q['unit'] in WEIGHT_CONVERSIONS:
                weight_total_oz += q['quantity'] * WEIGHT_CONVERSIONS[q['unit']]
                has_weight = True

        if has_weight:
            # Convert back to largest appropriate unit
            if weight_total_oz >= 16:
                lbs = weight_total_oz / 16
                aggregated.append({
                    'item': item_name,
                    'quantity': round(lbs, 2),
                    'unit': 'lb',
                    'grocery_section': section
                })
            else:
                aggregated.append({
                    'item': item_name,
                    'quantity': round(weight_total_oz, 2),
                    'unit': 'oz',
                    'grocery_section': section
                })
            continue

        # If no conversion possible, just sum quantities with same unit
        unit_groups = defaultdict(float)
        for q in quantities:
            unit_groups[q['unit']] += q['quantity']

        for unit, total_qty in unit_groups.items():
            aggregated.append({
                'item': item_name,
                'quantity': round(total_qty, 2),
                'unit': unit,
                'grocery_section': section
            })

    return aggregated


@router.post("/generate", response_model=ShoppingListResponse, status_code=201)
def generate_shopping_list(request: GenerateListRequest):
    """
    Generate a shopping list from the meal plan for a specific week.

    Aggregates all ingredients from recipes in the meal plan, normalizes units,
    and groups by grocery section. Replaces any existing shopping list.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Delete existing shopping lists (we only keep one at a time)
        cursor.execute("DELETE FROM shopping_lists")
        conn.commit()

        # Fetch all ingredients from recipes in this week's meal plan
        cursor.execute("""
            SELECT i.item, i.quantity, i.unit, i.grocery_section
            FROM meal_plans mp
            JOIN recipes r ON mp.recipe_id = r.id
            JOIN ingredients i ON r.id = i.recipe_id
            WHERE mp.week_start = ?
        """, (request.week_start,))

        ingredient_rows = cursor.fetchall()

        if not ingredient_rows:
            # No meals planned for this week
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"No meals planned for week starting {request.week_start}"
            )

        # Convert to list of dicts for normalization
        ingredients = [
            {
                'item': row['item'],
                'quantity': row['quantity'],
                'unit': row['unit'],
                'grocery_section': row['grocery_section']
            }
            for row in ingredient_rows
        ]

        # Normalize and aggregate
        aggregated_items = normalize_units(ingredients)

        # Create shopping list
        cursor.execute("""
            INSERT INTO shopping_lists (week_start)
            VALUES (?)
        """, (request.week_start,))

        list_id = cursor.lastrowid

        # Insert aggregated items
        for item in aggregated_items:
            cursor.execute("""
                INSERT INTO shopping_items (list_id, item, quantity, unit, grocery_section, checked)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (
                list_id,
                item['item'],
                item['quantity'],
                item['unit'],
                item['grocery_section']
            ))

        conn.commit()

        # Fetch created list with items
        cursor.execute("""
            SELECT id, week_start, created_at
            FROM shopping_lists
            WHERE id = ?
        """, (list_id,))

        list_row = cursor.fetchone()

        cursor.execute("""
            SELECT id, list_id, item, quantity, unit, grocery_section, checked
            FROM shopping_items
            WHERE list_id = ?
            ORDER BY grocery_section, item
        """, (list_id,))

        item_rows = cursor.fetchall()

        conn.close()

        items = [
            ShoppingItemResponse(
                id=row['id'],
                list_id=row['list_id'],
                item=row['item'],
                quantity=row['quantity'],
                unit=row['unit'],
                grocery_section=row['grocery_section'],
                checked=bool(row['checked'])
            )
            for row in item_rows
        ]

        return ShoppingListResponse(
            id=list_row['id'],
            week_start=list_row['week_start'],
            created_at=list_row['created_at'],
            items=items
        )

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to generate shopping list: {str(e)}")


@router.get("/current", response_model=Optional[ShoppingListResponse])
def get_current_shopping_list():
    """
    Get the current shopping list with all items.

    Returns null if no shopping list exists.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get most recent shopping list
        cursor.execute("""
            SELECT id, week_start, created_at
            FROM shopping_lists
            ORDER BY created_at DESC
            LIMIT 1
        """)

        list_row = cursor.fetchone()

        if not list_row:
            conn.close()
            return None

        list_id = list_row['id']

        # Fetch items
        cursor.execute("""
            SELECT id, list_id, item, quantity, unit, grocery_section, checked
            FROM shopping_items
            WHERE list_id = ?
            ORDER BY grocery_section, item
        """, (list_id,))

        item_rows = cursor.fetchall()

        conn.close()

        items = [
            ShoppingItemResponse(
                id=row['id'],
                list_id=row['list_id'],
                item=row['item'],
                quantity=row['quantity'],
                unit=row['unit'],
                grocery_section=row['grocery_section'],
                checked=bool(row['checked'])
            )
            for row in item_rows
        ]

        return ShoppingListResponse(
            id=list_row['id'],
            week_start=list_row['week_start'],
            created_at=list_row['created_at'],
            items=items
        )

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to fetch shopping list: {str(e)}")


@router.patch("/items/{item_id}", response_model=ShoppingItemResponse)
def toggle_item_checked(item_id: int):
    """
    Toggle the checked status of a shopping list item.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if item exists
        cursor.execute("SELECT * FROM shopping_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Shopping item {item_id} not found")

        # Toggle checked status
        new_checked = 0 if row['checked'] else 1
        cursor.execute("""
            UPDATE shopping_items
            SET checked = ?
            WHERE id = ?
        """, (new_checked, item_id))

        conn.commit()

        # Fetch updated item
        cursor.execute("SELECT * FROM shopping_items WHERE id = ?", (item_id,))
        updated_row = cursor.fetchone()

        conn.close()

        return ShoppingItemResponse(
            id=updated_row['id'],
            list_id=updated_row['list_id'],
            item=updated_row['item'],
            quantity=updated_row['quantity'],
            unit=updated_row['unit'],
            grocery_section=updated_row['grocery_section'],
            checked=bool(updated_row['checked'])
        )

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to toggle item: {str(e)}")


@router.post("/items", response_model=ShoppingItemResponse, status_code=201)
def add_manual_item(item: ManualItemCreate):
    """
    Add a manual item to the current shopping list.

    Manual items are items not from recipes (e.g., paper towels, coffee).
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get current shopping list
        cursor.execute("""
            SELECT id FROM shopping_lists
            ORDER BY created_at DESC
            LIMIT 1
        """)

        list_row = cursor.fetchone()

        if not list_row:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="No shopping list exists. Generate a list first."
            )

        list_id = list_row['id']

        # Insert manual item
        cursor.execute("""
            INSERT INTO shopping_items (list_id, item, quantity, unit, grocery_section, checked)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (
            list_id,
            item.item,
            item.quantity,
            item.unit,
            item.grocery_section
        ))

        item_id = cursor.lastrowid
        conn.commit()

        # Fetch created item
        cursor.execute("SELECT * FROM shopping_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()

        conn.close()

        return ShoppingItemResponse(
            id=row['id'],
            list_id=row['list_id'],
            item=row['item'],
            quantity=row['quantity'],
            unit=row['unit'],
            grocery_section=row['grocery_section'],
            checked=bool(row['checked'])
        )

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to add manual item: {str(e)}")


@router.delete("/items/{item_id}", status_code=204)
def remove_item(item_id: int):
    """
    Remove an item from the shopping list.

    Used to remove items the user already has at home or added by mistake.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if item exists
        cursor.execute("SELECT id FROM shopping_items WHERE id = ?", (item_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Shopping item {item_id} not found")

        # Delete item
        cursor.execute("DELETE FROM shopping_items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

        return None  # 204 No Content

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to remove item: {str(e)}")
