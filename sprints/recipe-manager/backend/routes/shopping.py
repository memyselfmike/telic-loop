from fastapi import APIRouter, HTTPException
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models import (
    GenerateShoppingRequest,
    ShoppingItemCreate,
    ShoppingItemResponse,
    ShoppingListResponse,
)

router = APIRouter()

_VOLUME_TO_TSP = {"tsp": 1.0, "tbsp": 3.0, "cup": 48.0}
_VOLUME_UNITS = set(_VOLUME_TO_TSP.keys())
_WEIGHT_TO_OZ = {"oz": 1.0, "lb": 16.0}
_WEIGHT_UNITS = set(_WEIGHT_TO_OZ.keys())
_COUNT_SYNONYMS = {"whole", "piece", "each"}


def _upconvert_volume(total_tsp: float) -> list[tuple[float, str]]:
    results: list[tuple[float, str]] = []
    if total_tsp >= 48.0:
        whole_cups = int(total_tsp / 48.0)
        remainder_tsp = round(total_tsp - whole_cups * 48.0, 1)
        results.append((float(whole_cups), "cup"))
        if remainder_tsp >= 3.0:
            whole_tbsp = int(remainder_tsp / 3.0)
            rem2 = round(remainder_tsp - whole_tbsp * 3.0, 1)
            results.append((float(whole_tbsp), "tbsp"))
            if rem2 >= 1.0:
                results.append((rem2, "tsp"))
        elif remainder_tsp >= 1.0:
            results.append((remainder_tsp, "tsp"))
        return results
    if total_tsp >= 3.0:
        whole_tbsp = int(total_tsp / 3.0)
        remainder_tsp = round(total_tsp - whole_tbsp * 3.0, 1)
        results.append((float(whole_tbsp), "tbsp"))
        if remainder_tsp >= 1.0:
            results.append((remainder_tsp, "tsp"))
        return results
    return [(round(total_tsp, 1), "tsp")]


def _upconvert_weight(total_oz: float) -> list[tuple[float, str]]:
    if total_oz >= 16.0:
        whole_lbs = int(total_oz / 16.0)
        remainder_oz = round(total_oz - whole_lbs * 16.0, 1)
        out: list[tuple[float, str]] = [(float(whole_lbs), "lb")]
        if remainder_oz >= 1.0:
            out.append((remainder_oz, "oz"))
        return out
    return [(round(total_oz, 1), "oz")]


def normalize_and_aggregate(raw):
    def classify(unit):
        u = unit.lower().strip()
        if u in _VOLUME_UNITS:
            return "volume", u
        if u in _WEIGHT_UNITS:
            return "weight", u
        if u in _COUNT_SYNONYMS:
            return "count", "whole"
        return "other_" + u, u

    accumulator = defaultdict(float)
    meta = {}
    for item, qty, unit, section in raw:
        item_key = item.lower().strip()
        family, canonical = classify(unit)
        if family == "volume":
            base = qty * _VOLUME_TO_TSP[canonical]
            key = (item_key, "volume")
        elif family == "weight":
            base = qty * _WEIGHT_TO_OZ[canonical]
            key = (item_key, "weight")
        elif family == "count":
            base = qty
            key = (item_key, "count")
        else:
            base = qty
            key = (item_key, canonical)
        accumulator[key] += base
        if key not in meta:
            meta[key] = (item.strip(), section, family, canonical)

    results = []
    for key, total in accumulator.items():
        item_display, section, family, canonical = meta[key]
        if family == "volume":
            for q, u in _upconvert_volume(total):
                results.append((item_display, q, u, section))
        elif family == "weight":
            for q, u in _upconvert_weight(total):
                results.append((item_display, q, u, section))
        else:
            unit_display = "whole" if family == "count" else canonical
            results.append((item_display, round(total, 1), unit_display, section))
    return results


async def _fetch_shopping_list(db, list_id: int) -> ShoppingListResponse:
    cursor = await db.execute(
        "SELECT id, week_start, created_at FROM shopping_lists WHERE id = ?",
        (list_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    cursor = await db.execute(
        "SELECT * FROM shopping_items WHERE list_id = ? ORDER BY grocery_section, item",
        (list_id,),
    )
    item_rows = await cursor.fetchall()
    items = [
        ShoppingItemResponse(
            id=r["id"],
            list_id=r["list_id"],
            item=r["item"],
            quantity=r["quantity"],
            unit=r["unit"],
            grocery_section=r["grocery_section"],
            source=r["source"],
            checked=bool(r["checked"]),
        )
        for r in item_rows
    ]
    return ShoppingListResponse(
        id=row["id"],
        week_start=row["week_start"],
        created_at=row["created_at"],
        items=items,
    )


@router.post("/shopping/generate", response_model=ShoppingListResponse, status_code=201)
async def generate_shopping_list(req: GenerateShoppingRequest):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT i.item, i.quantity, i.unit, i.grocery_section"
            " FROM meal_plans mp"
            " JOIN ingredients i ON i.recipe_id = mp.recipe_id"
            " WHERE mp.week_start = ?",
            (req.week_start,),
        )
        rows = await cursor.fetchall()
        raw = [(r["item"], r["quantity"], r["unit"], r["grocery_section"]) for r in rows]
        aggregated = normalize_and_aggregate(raw)

        cursor = await db.execute(
            "SELECT id FROM shopping_lists WHERE week_start = ?", (req.week_start,)
        )
        existing = await cursor.fetchone()
        if existing:
            await db.execute("DELETE FROM shopping_lists WHERE id = ?", (existing["id"],))
            await db.commit()

        cursor = await db.execute(
            "INSERT INTO shopping_lists (week_start) VALUES (?)", (req.week_start,)
        )
        list_id = cursor.lastrowid
        await db.commit()

        for item, qty, unit, section in aggregated:
            await db.execute(
                "INSERT INTO shopping_items"
                " (list_id, item, quantity, unit, grocery_section, source)"
                " VALUES (?, ?, ?, ?, ?, \"generated\")",
                (list_id, item, qty, unit, section),
            )
        await db.commit()
        return await _fetch_shopping_list(db, list_id)


@router.get("/shopping/current", response_model=ShoppingListResponse)
async def get_current_shopping_list():
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM shopping_lists ORDER BY created_at DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="No shopping list found")
        return await _fetch_shopping_list(db, row["id"])


@router.patch("/shopping/items/{item_id}", response_model=ShoppingItemResponse)
async def toggle_item(item_id: int):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM shopping_items WHERE id = ?", (item_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Shopping item not found")
        new_checked = 0 if row["checked"] else 1
        await db.execute(
            "UPDATE shopping_items SET checked = ? WHERE id = ?", (new_checked, item_id)
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM shopping_items WHERE id = ?", (item_id,)
        )
        updated = await cursor.fetchone()
        return ShoppingItemResponse(
            id=updated["id"],
            list_id=updated["list_id"],
            item=updated["item"],
            quantity=updated["quantity"],
            unit=updated["unit"],
            grocery_section=updated["grocery_section"],
            source=updated["source"],
            checked=bool(updated["checked"]),
        )


@router.post("/shopping/items", response_model=ShoppingItemResponse, status_code=201)
async def add_manual_item(item: ShoppingItemCreate):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM shopping_lists ORDER BY created_at DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail="No shopping list exists. Generate one first.",
            )
        list_id = row["id"]
        cursor = await db.execute(
            "INSERT INTO shopping_items"
            " (list_id, item, quantity, unit, grocery_section, source)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (list_id, item.item, item.quantity, item.unit, item.grocery_section, item.source),
        )
        new_id = cursor.lastrowid
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM shopping_items WHERE id = ?", (new_id,)
        )
        created = await cursor.fetchone()
        return ShoppingItemResponse(
            id=created["id"],
            list_id=created["list_id"],
            item=created["item"],
            quantity=created["quantity"],
            unit=created["unit"],
            grocery_section=created["grocery_section"],
            source=created["source"],
            checked=bool(created["checked"]),
        )


@router.delete("/shopping/items/{item_id}", status_code=204)
async def delete_item(item_id: int):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM shopping_items WHERE id = ?", (item_id,)
        )
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Shopping item not found")
        await db.execute("DELETE FROM shopping_items WHERE id = ?", (item_id,))
        await db.commit()
