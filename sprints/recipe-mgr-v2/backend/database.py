import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "recipes.db"

def get_connection():
    """Get SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def _create_recipes_table(cursor):
    """Create recipes table."""
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

def _create_ingredients_table(cursor):
    """Create ingredients table."""
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

def _create_meal_plans_table(cursor):
    """Create meal_plans table."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meal_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start TEXT NOT NULL,
            day_of_week INTEGER NOT NULL,
            meal_slot TEXT NOT NULL,
            recipe_id INTEGER NOT NULL,
            UNIQUE(week_start, day_of_week, meal_slot),
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        )
    """)

def _create_shopping_tables(cursor):
    """Create shopping_lists and shopping_items tables."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

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

def _get_seed_recipes():
    """Return seed recipe data."""
    return [
        ("Classic Oatmeal", "Hearty breakfast", "breakfast", 5, 10, 2,
         "1. Bring milk to boil\n2. Add oats and reduce heat\n3. Simmer 5 min\n4. Stir in honey",
         "quick,healthy"),
        ("Grilled Chicken Salad", "Fresh and protein-packed", "lunch", 15, 10, 2,
         "1. Season and grill chicken\n2. Chop romaine\n3. Toss with oil and vinegar",
         "healthy,protein"),
        ("Beef Stir Fry", "Quick weeknight dinner", "dinner", 10, 20, 4,
         "1. Slice beef thin\n2. Heat wok\n3. Stir fry beef\n4. Add broccoli\n5. Sauce and serve",
         "quick,asian"),
        ("Trail Mix", "Portable energy snack", "snack", 5, 0, 8,
         "1. Mix all ingredients\n2. Store in airtight container",
         "healthy,portable"),
        ("Chocolate Mug Cake", "5-minute dessert", "dessert", 3, 2, 1,
         "1. Mix dry ingredients\n2. Add egg and milk\n3. Microwave 90 seconds",
         "quick,chocolate")
    ]

def _get_seed_ingredients():
    """Return seed ingredient data."""
    return [
        # Classic Oatmeal (id=1)
        (1, 1.0, "cup", "rolled oats", "pantry", 0),
        (1, 2.0, "cup", "milk", "dairy", 1),
        (1, 1.0, "tbsp", "honey", "pantry", 2),
        # Grilled Chicken Salad (id=2)
        (2, 6.0, "oz", "chicken breast", "meat", 0),
        (2, 2.0, "cup", "romaine lettuce", "produce", 1),
        (2, 1.0, "tbsp", "olive oil", "pantry", 2),
        # Beef Stir Fry (id=3)
        (3, 1.0, "lb", "beef strips", "meat", 0),
        (3, 2.0, "cup", "broccoli florets", "produce", 1),
        (3, 2.0, "tbsp", "soy sauce", "pantry", 2),
        # Trail Mix (id=4)
        (4, 0.5, "cup", "almonds", "other", 0),
        (4, 0.5, "cup", "raisins", "produce", 1),
        (4, 0.25, "cup", "chocolate chips", "pantry", 2),
        # Chocolate Mug Cake (id=5)
        (5, 4.0, "tbsp", "flour", "pantry", 0),
        (5, 3.0, "tbsp", "sugar", "pantry", 1),
        (5, 2.0, "tbsp", "cocoa powder", "pantry", 2),
        (5, 1.0, "whole", "egg", "dairy", 3),
        (5, 3.0, "tbsp", "milk", "dairy", 4),
    ]

def _insert_seed_recipes(cursor):
    """Insert seed recipes into database."""
    seed_recipes = _get_seed_recipes()
    for recipe in seed_recipes:
        cursor.execute("""
            INSERT INTO recipes (title, description, category, prep_time_minutes,
                               cook_time_minutes, servings, instructions, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, recipe)

def _insert_seed_ingredients(cursor):
    """Insert seed ingredients into database."""
    seed_ingredients = _get_seed_ingredients()
    for ingredient in seed_ingredients:
        cursor.execute("""
            INSERT INTO ingredients (recipe_id, quantity, unit, item, grocery_section, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ingredient)

def _needs_seed_data(cursor):
    """Check if database needs seed data."""
    cursor.execute("SELECT COUNT(*) FROM recipes")
    return cursor.fetchone()[0] == 0

def init_db():
    """Initialize database schema and seed data."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()

    # Create tables
    _create_recipes_table(cursor)
    _create_ingredients_table(cursor)
    _create_meal_plans_table(cursor)
    _create_shopping_tables(cursor)

    # Insert seed data if needed
    if _needs_seed_data(cursor):
        _insert_seed_recipes(cursor)
        _insert_seed_ingredients(cursor)

    conn.commit()
    conn.close()
