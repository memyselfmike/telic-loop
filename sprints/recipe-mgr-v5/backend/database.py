"""
Database connection and schema management for Recipe Manager
"""
import sqlite3
from pathlib import Path
from typing import Optional

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "recipes.db"


def get_connection() -> sqlite3.Connection:
    """
    Get database connection with foreign keys enabled
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """
    Initialize database schema and seed data
    Creates all tables if they don't exist and inserts seed data on first run
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Create recipes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            category TEXT NOT NULL CHECK(category IN ('breakfast', 'lunch', 'dinner', 'snack', 'dessert')),
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
            grocery_section TEXT DEFAULT 'other' CHECK(grocery_section IN ('produce', 'meat', 'dairy', 'pantry', 'frozen', 'other')),
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        )
    """)

    # Create meal_plans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meal_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start TEXT NOT NULL,
            day_of_week INTEGER NOT NULL CHECK(day_of_week >= 0 AND day_of_week <= 6),
            meal_slot TEXT NOT NULL CHECK(meal_slot IN ('breakfast', 'lunch', 'dinner', 'snack')),
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
            grocery_section TEXT DEFAULT 'other' CHECK(grocery_section IN ('produce', 'meat', 'dairy', 'pantry', 'frozen', 'other')),
            checked INTEGER DEFAULT 0,
            source TEXT DEFAULT 'recipe' CHECK(source IN ('recipe', 'manual')),
            FOREIGN KEY (list_id) REFERENCES shopping_lists(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Seed data: insert 5 sample recipes if database is empty
    cursor.execute("SELECT COUNT(*) FROM recipes")
    recipe_count = cursor.fetchone()[0]

    if recipe_count == 0:
        seed_recipes = [
            # Breakfast: Classic Oatmeal
            {
                "title": "Classic Oatmeal",
                "description": "Hearty breakfast to start your day",
                "category": "breakfast",
                "prep_time_minutes": 2,
                "cook_time_minutes": 5,
                "servings": 2,
                "instructions": "1. Bring milk to a boil\n2. Add oats and reduce heat\n3. Simmer for 5 minutes\n4. Stir in honey\n5. Serve warm",
                "tags": "quick,healthy",
                "ingredients": [
                    (1.0, "cup", "rolled oats", "pantry", 0),
                    (2.0, "cup", "milk", "dairy", 1),
                    (1.0, "tbsp", "honey", "pantry", 2),
                    (0.5, "tsp", "cinnamon", "pantry", 3),
                ]
            },
            # Lunch: Grilled Chicken Salad
            {
                "title": "Grilled Chicken Salad",
                "description": "Light and protein-packed lunch",
                "category": "lunch",
                "prep_time_minutes": 10,
                "cook_time_minutes": 15,
                "servings": 2,
                "instructions": "1. Season and grill chicken\n2. Chop romaine lettuce\n3. Slice cherry tomatoes\n4. Toss with olive oil and lemon\n5. Top with sliced chicken",
                "tags": "healthy,protein",
                "ingredients": [
                    (6.0, "oz", "chicken breast", "meat", 0),
                    (2.0, "cup", "romaine lettuce", "produce", 1),
                    (1.0, "cup", "cherry tomatoes", "produce", 2),
                    (1.0, "tbsp", "olive oil", "pantry", 3),
                    (1.0, "whole", "lemon", "produce", 4),
                ]
            },
            # Dinner: Beef Stir Fry
            {
                "title": "Beef Stir Fry",
                "description": "Quick Asian-inspired dinner",
                "category": "dinner",
                "prep_time_minutes": 15,
                "cook_time_minutes": 12,
                "servings": 4,
                "instructions": "1. Slice beef into thin strips\n2. Heat oil in wok\n3. Stir-fry beef until browned\n4. Add broccoli and cook 5 minutes\n5. Add soy sauce and garlic\n6. Serve over rice",
                "tags": "quick,asian",
                "ingredients": [
                    (1.0, "lb", "beef sirloin", "meat", 0),
                    (2.0, "cup", "broccoli florets", "produce", 1),
                    (2.0, "tbsp", "soy sauce", "pantry", 2),
                    (1.0, "tbsp", "vegetable oil", "pantry", 3),
                    (2.0, "tsp", "minced garlic", "produce", 4),
                    (2.0, "cup", "cooked rice", "pantry", 5),
                ]
            },
            # Snack: Trail Mix
            {
                "title": "Trail Mix",
                "description": "Energy-packed snack for on the go",
                "category": "snack",
                "prep_time_minutes": 5,
                "cook_time_minutes": 0,
                "servings": 8,
                "instructions": "1. Combine all ingredients in a large bowl\n2. Mix well\n3. Store in airtight container\n4. Portion into snack bags",
                "tags": "quick,healthy,snack",
                "ingredients": [
                    (0.5, "cup", "almonds", "other", 0),
                    (0.5, "cup", "raisins", "produce", 1),
                    (0.25, "cup", "chocolate chips", "pantry", 2),
                    (0.25, "cup", "dried cranberries", "produce", 3),
                ]
            },
            # Dessert: Chocolate Mug Cake
            {
                "title": "Chocolate Mug Cake",
                "description": "Quick microwave dessert in 2 minutes",
                "category": "dessert",
                "prep_time_minutes": 3,
                "cook_time_minutes": 2,
                "servings": 1,
                "instructions": "1. Mix dry ingredients in mug\n2. Add egg and milk\n3. Stir until smooth\n4. Microwave 90 seconds\n5. Let cool 1 minute",
                "tags": "quick,dessert,chocolate",
                "ingredients": [
                    (4.0, "tbsp", "all-purpose flour", "pantry", 0),
                    (3.0, "tbsp", "sugar", "pantry", 1),
                    (2.0, "tbsp", "cocoa powder", "pantry", 2),
                    (1.0, "whole", "egg", "dairy", 3),
                    (3.0, "tbsp", "milk", "dairy", 4),
                    (2.0, "tbsp", "vegetable oil", "pantry", 5),
                ]
            },
        ]

        for recipe_data in seed_recipes:
            ingredients = recipe_data.pop("ingredients")

            # Insert recipe
            cursor.execute("""
                INSERT INTO recipes (title, description, category, prep_time_minutes, cook_time_minutes, servings, instructions, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recipe_data["title"],
                recipe_data["description"],
                recipe_data["category"],
                recipe_data["prep_time_minutes"],
                recipe_data["cook_time_minutes"],
                recipe_data["servings"],
                recipe_data["instructions"],
                recipe_data["tags"]
            ))

            recipe_id = cursor.lastrowid

            # Insert ingredients
            for quantity, unit, item, section, sort_order in ingredients:
                cursor.execute("""
                    INSERT INTO ingredients (recipe_id, quantity, unit, item, grocery_section, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (recipe_id, quantity, unit, item, section, sort_order))

        conn.commit()
        print(f"[OK] Seeded database with {len(seed_recipes)} sample recipes")

    cursor.close()
    conn.close()
