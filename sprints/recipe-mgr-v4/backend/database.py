"""Database initialization and seed data for Recipe Manager"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional


DB_PATH = Path(__file__).parent.parent / "data" / "recipes.db"


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database schema"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_db() as conn:
        cursor = conn.cursor()

        # Create recipes table
        cursor.execute("""
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create ingredients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                item TEXT NOT NULL,
                grocery_section TEXT DEFAULT 'other',
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            )
        """)

        # Create meal_plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meal_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL,
                day_of_week INTEGER NOT NULL,
                meal_slot TEXT NOT NULL,
                recipe_id INTEGER NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                UNIQUE(week_start, day_of_week, meal_slot)
            )
        """)

        # Create shopping_lists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create shopping_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL,
                item TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                grocery_section TEXT DEFAULT 'other',
                checked INTEGER DEFAULT 0,
                source TEXT DEFAULT 'recipe',
                FOREIGN KEY (list_id) REFERENCES shopping_lists(id) ON DELETE CASCADE
            )
        """)

        conn.commit()

        # Seed data if recipes table is empty
        cursor.execute("SELECT COUNT(*) FROM recipes")
        if cursor.fetchone()[0] == 0:
            seed_data(conn)


def seed_data(conn: sqlite3.Connection):
    """Insert seed data for first run"""
    cursor = conn.cursor()

    # Seed recipes with ingredients
    seed_recipes = [
        {
            "title": "Classic Oatmeal",
            "description": "Hearty breakfast to start your day",
            "category": "breakfast",
            "prep_time_minutes": 5,
            "cook_time_minutes": 10,
            "servings": 2,
            "instructions": "1. Bring water to boil\n2. Add oats and reduce heat\n3. Simmer for 5 minutes\n4. Stir in honey and serve",
            "tags": "healthy,quick",
            "ingredients": [
                (1, "cup", "rolled oats", "pantry"),
                (2, "cup", "milk", "dairy"),
                (1, "tbsp", "honey", "pantry"),
                (0.5, "tsp", "cinnamon", "pantry"),
            ]
        },
        {
            "title": "Grilled Chicken Salad",
            "description": "Fresh and light lunch option",
            "category": "lunch",
            "prep_time_minutes": 15,
            "cook_time_minutes": 12,
            "servings": 2,
            "instructions": "1. Season and grill chicken\n2. Chop romaine and vegetables\n3. Slice chicken\n4. Toss with dressing",
            "tags": "healthy,protein",
            "ingredients": [
                (6, "oz", "chicken breast", "meat"),
                (2, "cup", "romaine lettuce", "produce"),
                (1, "whole", "tomato", "produce"),
                (1, "tbsp", "olive oil", "pantry"),
                (0.5, "tbsp", "lemon juice", "produce"),
            ]
        },
        {
            "title": "Beef Stir Fry",
            "description": "Quick weeknight Asian dinner",
            "category": "dinner",
            "prep_time_minutes": 20,
            "cook_time_minutes": 15,
            "servings": 4,
            "instructions": "1. Slice beef thinly\n2. Chop vegetables\n3. Heat wok with oil\n4. Stir fry beef, then vegetables\n5. Add sauce and serve",
            "tags": "quick,asian",
            "ingredients": [
                (1, "lb", "beef strips", "meat"),
                (2, "cup", "broccoli florets", "produce"),
                (1, "whole", "bell pepper", "produce"),
                (2, "tbsp", "soy sauce", "pantry"),
                (1, "tbsp", "sesame oil", "pantry"),
                (2, "tsp", "ginger", "produce"),
            ]
        },
        {
            "title": "Trail Mix",
            "description": "Healthy snack for on the go",
            "category": "snack",
            "prep_time_minutes": 5,
            "cook_time_minutes": 0,
            "servings": 6,
            "instructions": "1. Combine all ingredients in bowl\n2. Mix well\n3. Store in airtight container",
            "tags": "healthy,quick,vegetarian",
            "ingredients": [
                (0.5, "cup", "almonds", "other"),
                (0.5, "cup", "raisins", "produce"),
                (0.25, "cup", "chocolate chips", "pantry"),
                (0.25, "cup", "pumpkin seeds", "other"),
            ]
        },
        {
            "title": "Chocolate Mug Cake",
            "description": "Single-serving dessert in minutes",
            "category": "dessert",
            "prep_time_minutes": 5,
            "cook_time_minutes": 2,
            "servings": 1,
            "instructions": "1. Mix dry ingredients in mug\n2. Add wet ingredients and stir\n3. Microwave for 90 seconds\n4. Let cool for 1 minute",
            "tags": "quick,chocolate",
            "ingredients": [
                (4, "tbsp", "flour", "pantry"),
                (3, "tbsp", "sugar", "pantry"),
                (2, "tbsp", "cocoa powder", "pantry"),
                (1, "whole", "egg", "dairy"),
                (3, "tbsp", "milk", "dairy"),
                (2, "tbsp", "vegetable oil", "pantry"),
            ]
        }
    ]

    for recipe_data in seed_recipes:
        ingredients = recipe_data.pop("ingredients")

        # Insert recipe
        columns = ", ".join(recipe_data.keys())
        placeholders = ", ".join(["?"] * len(recipe_data))
        cursor.execute(
            f"INSERT INTO recipes ({columns}) VALUES ({placeholders})",
            tuple(recipe_data.values())
        )
        recipe_id = cursor.lastrowid

        # Insert ingredients
        for i, (quantity, unit, item, section) in enumerate(ingredients):
            cursor.execute(
                """INSERT INTO ingredients
                   (recipe_id, quantity, unit, item, grocery_section, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (recipe_id, quantity, unit, item, section, i)
            )

    conn.commit()
