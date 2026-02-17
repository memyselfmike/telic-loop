import os
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager

DB_PATH = Path(__file__).parent.parent / "data" / "recipes.db"

CREATE_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT NOT NULL,
    prep_time_minutes INTEGER DEFAULT 0,
    cook_time_minutes INTEGER DEFAULT 0,
    servings INTEGER DEFAULT 1,
    instructions TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    item TEXT NOT NULL,
    grocery_section TEXT DEFAULT 'other',
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS meal_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start TEXT NOT NULL,
    day_of_week INTEGER NOT NULL,
    meal_slot TEXT NOT NULL,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS shopping_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS shopping_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL REFERENCES shopping_lists(id) ON DELETE CASCADE,
    item TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    grocery_section TEXT DEFAULT 'other',
    source TEXT DEFAULT 'manual',
    checked INTEGER DEFAULT 0
);
"""

SEED_RECIPES = [
    {
        "title": "Classic Oatmeal",
        "description": "A simple, hearty breakfast oatmeal.",
        "category": "breakfast",
        "prep_time_minutes": 2,
        "cook_time_minutes": 5,
        "servings": 1,
        "instructions": "Bring milk to a boil, stir in oats, cook 3-5 minutes. Drizzle with honey.",
        "tags": "quick,vegetarian",
        "ingredients": [
            (1.0, "cup", "rolled oats", "pantry"),
            (2.0, "cup", "milk", "dairy"),
            (1.0, "tbsp", "honey", "pantry"),
        ],
    },
    {
        "title": "Grilled Chicken Salad",
        "description": "Light and protein-packed lunch salad.",
        "category": "lunch",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 1,
        "instructions": "Grill chicken breast, slice and serve over romaine lettuce drizzled with olive oil.",
        "tags": "high-protein,gluten-free",
        "ingredients": [
            (6.0, "oz", "chicken breast", "meat"),
            (2.0, "cup", "romaine", "produce"),
            (1.0, "tbsp", "olive oil", "pantry"),
        ],
    },
    {
        "title": "Beef Stir Fry",
        "description": "Quick and savory beef and broccoli stir fry.",
        "category": "dinner",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 2,
        "instructions": "Stir fry beef strips in a hot pan, add broccoli and soy sauce, cook until tender.",
        "tags": "high-protein",
        "ingredients": [
            (1.0, "lb", "beef strips", "meat"),
            (2.0, "cup", "broccoli", "produce"),
            (2.0, "tbsp", "soy sauce", "pantry"),
        ],
    },
    {
        "title": "Trail Mix",
        "description": "Easy no-cook energy snack.",
        "category": "snack",
        "prep_time_minutes": 5,
        "cook_time_minutes": 0,
        "servings": 4,
        "instructions": "Combine almonds, raisins, and chocolate chips. Mix well and portion into bags.",
        "tags": "vegetarian,no-cook",
        "ingredients": [
            (0.5, "cup", "almonds", "other"),
            (0.5, "cup", "raisins", "produce"),
            (0.25, "cup", "chocolate chips", "pantry"),
        ],
    },
    {
        "title": "Chocolate Mug Cake",
        "description": "Single-serve chocolate cake made in the microwave.",
        "category": "dessert",
        "prep_time_minutes": 2,
        "cook_time_minutes": 2,
        "servings": 1,
        "instructions": "Mix dry ingredients in mug, add egg and stir. Microwave 90 seconds.",
        "tags": "quick,vegetarian",
        "ingredients": [
            (4.0, "tbsp", "flour", "pantry"),
            (3.0, "tbsp", "sugar", "pantry"),
            (2.0, "tbsp", "cocoa powder", "pantry"),
            (1.0, "whole", "egg", "dairy"),
        ],
    },
]


async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.executescript(CREATE_SCHEMA)
        await db.commit()

        cursor = await db.execute("SELECT COUNT(*) FROM recipes")
        row = await cursor.fetchone()
        count = row[0] if row else 0

        if count == 0:
            for recipe in SEED_RECIPES:
                cursor = await db.execute(
                    """
                    INSERT INTO recipes
                        (title, description, category, prep_time_minutes,
                         cook_time_minutes, servings, instructions, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        recipe["title"],
                        recipe["description"],
                        recipe["category"],
                        recipe["prep_time_minutes"],
                        recipe["cook_time_minutes"],
                        recipe["servings"],
                        recipe["instructions"],
                        recipe["tags"],
                    ),
                )
                recipe_id = cursor.lastrowid
                for sort_order, (qty, unit, item, section) in enumerate(recipe["ingredients"]):
                    await db.execute(
                        """
                        INSERT INTO ingredients
                            (recipe_id, quantity, unit, item, grocery_section, sort_order)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (recipe_id, qty, unit, item, section, sort_order),
                    )
            await db.commit()


@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        try:
            yield db
        finally:
            pass
