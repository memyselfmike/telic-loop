# Vision: Recipe Manager with Meal Planner

## The Outcome

A home cook opens a web app in their browser and has a complete system for storing their recipes, planning meals for the week, and generating a shopping list from their plan. No more recipe screenshots scattered across their phone, no more "what's for dinner?" at 5pm, no more wandering the grocery store trying to remember what they need. One app, three workflows: collect recipes, plan the week, shop the list.

## Who Is This For

Someone who cooks at home 4-7 nights a week. They have 20-50 go-to recipes in their head, bookmarked, or screenshot'd. They want to plan meals a week at a time so grocery shopping is one trip, not five. They want to see what ingredients they need, aggregated across all planned meals, so they buy the right amounts and don't forget anything.

## What "Value Delivered" Looks Like

### 1. Build a Recipe Collection

The cook creates recipes with: title, description, prep time, cook time, servings, a list of ingredients (with quantity, unit, and item name), and step-by-step instructions. They can edit any recipe, delete ones they don't want, and browse their full collection.

Each recipe has a category (breakfast, lunch, dinner, snack, dessert) and optional tags (quick, vegetarian, comfort food, etc.) for filtering. The collection view shows recipe cards with title, category, prep+cook time, and tags — enough to pick what to cook without opening each one.

Searching and filtering is essential: the cook can filter by category, search by title or ingredient ("what can I make with chicken?"), and filter by tag. These can combine — show me all "dinner" recipes tagged "quick" that use "pasta."

### 2. Plan Meals for the Week

A weekly planner shows 7 days (Monday-Sunday) with meal slots: breakfast, lunch, dinner, and an optional snack slot per day. The cook assigns recipes to slots by picking from their collection. They can see the full week at a glance — what's planned, what's empty.

They can clear a slot, swap recipes between slots, and copy a recipe to multiple slots (meal prep — same lunch all week). Navigating between weeks lets them plan ahead or review past weeks. The current week is the default view.

Each day shows a calorie/time estimate derived from the assigned recipes (total prep+cook time for the day's meals). This helps the cook balance effort across the week — don't put three 90-minute dinners in a row.

### 3. Generate a Shopping List

From the weekly plan, the cook generates a shopping list. The list aggregates ingredients across all planned meals for the selected week: if Monday's stir fry needs 2 chicken breasts and Thursday's curry needs 3, the list shows 5 chicken breasts.

Ingredients are grouped by common grocery sections (produce, meat, dairy, pantry, frozen, other). The cook can check off items as they shop. They can manually add items not from recipes (paper towels, coffee). They can remove items they already have at home.

The shopping list persists — closing the browser and reopening shows the same list with the same checked/unchecked state. Generating a new list for a different week replaces the current one (with a confirmation prompt).

### 4. Trust the Data

All data persists in a SQLite database. Recipes, meal plans, and shopping lists survive app restarts. The database handles relationships properly: deleting a recipe that's assigned to a meal plan removes it from those slots (with a warning). Editing a recipe's ingredients updates future shopping lists but not already-generated ones.

## What This Is NOT

- Not a social platform (no sharing, no public profiles, no comments)
- Not a nutrition tracker (shows prep/cook time, not detailed macros)
- Not a recipe scraper (manual entry only, no URL import)
- Not a mobile app (responsive web, but not native)
- Not a multi-user system (single user, no authentication)

## Architecture

This is a full-stack web application:

- **Backend**: Python FastAPI REST API
- **Database**: SQLite with proper foreign keys and cascading deletes
- **Frontend**: Single-page application served as static files (vanilla JS, no framework)
- **Services**: API server on port 8000, frontend served from the same server via static file mounting

The backend is the source of truth. The frontend calls the API for all data operations. The database schema enforces referential integrity — recipes, meal plans, and shopping lists are properly linked.

## Constraints

- Python 3.11+ for the backend
- No external database servers (SQLite only)
- No JavaScript frameworks (vanilla JS)
- No authentication (single-user local tool)
- Frontend must work at 1024px desktop and 768px tablet width
- Professional dark theme consistent across all views
- All API endpoints follow REST conventions with proper HTTP status codes
- Database tables created on startup if they don't exist
- Ingredient aggregation must handle unit normalization (2 cups + 1 cup = 3 cups, not two separate lines)
