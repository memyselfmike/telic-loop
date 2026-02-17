# PRD: Recipe Manager with Meal Planner

## 1. System Architecture

### 1.1 Services
- **API Server**: FastAPI application on port 8000
  - REST API endpoints under `/api/`
  - Static file serving for frontend at `/`
  - SQLite database at `sprints/recipe-manager/data/recipes.db`
  - **Port conflict**: Before starting, terminate any existing process on port 8000 (e.g., `fuser -k 8000/tcp` on Linux, or `for /f "tokens=5" %p in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %p` on Windows). Alternatively, make the port configurable via a `PORT` environment variable (default: 8000). This prevents `EADDRINUSE` / `[Errno 98] Address already in use` errors when 15+ processes may already occupy the port.
- **Frontend**: Vanilla JS SPA served as static files from `sprints/recipe-manager/frontend/`

### 1.2 Technology Stack
- Backend: Python 3.11+, FastAPI, uvicorn, sqlite3 (stdlib)
- Frontend: HTML, CSS, JavaScript (no frameworks, no build step)
- Database: SQLite 3 with foreign keys enabled
- No external dependencies beyond FastAPI and uvicorn

### 1.3 Project Structure
```
sprints/recipe-manager/
├── backend/
│   ├── main.py          # FastAPI app, startup, static mounting
│   ├── database.py      # SQLite connection, schema, migrations
│   ├── models.py        # Pydantic models for request/response
│   ├── routes/
│   │   ├── recipes.py   # Recipe CRUD endpoints
│   │   ├── meals.py     # Meal plan endpoints
│   │   └── shopping.py  # Shopping list generation + management
│   └── requirements.txt # fastapi, uvicorn
├── frontend/
│   ├── index.html       # SPA shell
│   ├── css/
│   │   └── style.css    # Dark theme styles
│   └── js/
│       ├── app.js       # Router, navigation, shared state
│       ├── recipes.js   # Recipe collection UI
│       ├── planner.js   # Weekly meal planner UI
│       └── shopping.js  # Shopping list UI
├── data/
│   └── recipes.db       # SQLite database (auto-created)
└── tests/
    └── test_api.py      # Pytest API integration tests
```

## 2. Database Schema

### 2.1 Tables

**recipes**
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| title | TEXT | NOT NULL |
| description | TEXT | DEFAULT '' |
| category | TEXT | NOT NULL (breakfast, lunch, dinner, snack, dessert) |
| prep_time_minutes | INTEGER | DEFAULT 0 |
| cook_time_minutes | INTEGER | DEFAULT 0 |
| servings | INTEGER | DEFAULT 1 |
| instructions | TEXT | DEFAULT '' |
| tags | TEXT | DEFAULT '' (comma-separated) |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TEXT | DEFAULT CURRENT_TIMESTAMP |

**ingredients**
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| recipe_id | INTEGER | NOT NULL, FOREIGN KEY → recipes(id) ON DELETE CASCADE |
| quantity | REAL | NOT NULL |
| unit | TEXT | NOT NULL |
| item | TEXT | NOT NULL |
| grocery_section | TEXT | DEFAULT 'other' (produce, meat, dairy, pantry, frozen, other) |
| sort_order | INTEGER | DEFAULT 0 |

**meal_plans**
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| week_start | TEXT | NOT NULL (ISO date, always a Monday) |
| day_of_week | INTEGER | NOT NULL (0=Mon, 6=Sun) |
| meal_slot | TEXT | NOT NULL (breakfast, lunch, dinner, snack) |
| recipe_id | INTEGER | NOT NULL, FOREIGN KEY → recipes(id) ON DELETE CASCADE |
| UNIQUE(week_start, day_of_week, meal_slot) |

**shopping_lists**
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| week_start | TEXT | NOT NULL |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP |

**shopping_items**
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| list_id | INTEGER | NOT NULL, FOREIGN KEY → shopping_lists(id) ON DELETE CASCADE |
| item | TEXT | NOT NULL |
| quantity | REAL | NOT NULL |
| unit | TEXT | NOT NULL |
| grocery_section | TEXT | DEFAULT 'other' |
| checked | INTEGER | DEFAULT 0 |
| source | TEXT | DEFAULT 'recipe' (recipe, manual) |

### 2.2 Unit Normalization

The system must normalize compatible units when aggregating ingredients:
- Volume: tsp → tbsp → cup (3 tsp = 1 tbsp, 16 tbsp = 1 cup)
- Weight: oz → lb (16 oz = 1 lb)
- Count: "whole", "piece", "each" treated as equivalent
- Incompatible units kept separate (e.g., 2 cups flour + 100g flour = two lines)

**Upconversion rules:**
- Upconvert to the largest unit that yields a quantity **>= 1**. Examples:
  - 4 tsp → 1 tbsp + 1 tsp (not 4 tsp, because 4/3 = 1.3 tbsp ≥ 1; keep remainder in smaller unit)
  - 2 tbsp → 2 tbsp (not 0.125 cups, because 2/16 = 0.125 < 1)
  - 2 tsp + 1 tsp = 3 tsp → 1 tbsp (exact threshold)
- **Never downconvert** (e.g., do not convert 0.5 cups back to tbsp).
- Keep fractional quantities to **one decimal place** (e.g., 1.3 tbsp, not 1.333…).

### 2.3 Seed Data

On first run (when the `recipes` table is empty), `database.py` must insert **5 sample recipes** — at least one per category: breakfast, lunch, dinner, snack, dessert. Each recipe must include 3–6 ingredients spanning different `grocery_section` values (produce, meat, dairy, pantry, frozen, other) and different units (tsp, tbsp, cup, oz, lb, whole, etc.).

**Purpose:** Satisfies the value proof "User opens localhost:8000 and sees 5 seed recipes immediately" and populates the planner for Epic 1 demo scenarios without requiring the user to create data manually.

**Example seed set (builder may vary titles/ingredients, but must meet the category and section coverage rules):**
| Title | Category | Key ingredients |
|-------|----------|-----------------|
| Classic Oatmeal | breakfast | 1 cup rolled oats (pantry), 2 cup milk (dairy), 1 tbsp honey (pantry) |
| Grilled Chicken Salad | lunch | 6 oz chicken breast (meat), 2 cup romaine (produce), 1 tbsp olive oil (pantry) |
| Beef Stir Fry | dinner | 1 lb beef strips (meat), 2 cup broccoli (produce), 2 tbsp soy sauce (pantry) |
| Trail Mix | snack | 0.5 cup almonds (other), 0.5 cup raisins (produce), 0.25 cup chocolate chips (pantry) |
| Chocolate Mug Cake | dessert | 4 tbsp flour (pantry), 3 tbsp sugar (pantry), 2 tbsp cocoa powder (pantry), 1 whole egg (dairy) |

## 3. API Endpoints

### 3.1 Recipes

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/recipes | List all recipes (supports ?category=, ?tag=, ?search=) |
| GET | /api/recipes/{id} | Get recipe with ingredients |
| POST | /api/recipes | Create recipe with ingredients |
| PUT | /api/recipes/{id} | Update recipe (replaces ingredients list) |
| DELETE | /api/recipes/{id} | Delete recipe (cascades to meal plans) |

**Query parameters for GET /api/recipes:**
- `category`: filter by exact category
- `tag`: filter by tag (partial match within comma-separated tags)
- `search`: search title, description, and ingredient items

**POST/PUT body:**
```json
{
  "title": "Chicken Stir Fry",
  "description": "Quick weeknight dinner",
  "category": "dinner",
  "prep_time_minutes": 15,
  "cook_time_minutes": 20,
  "servings": 4,
  "instructions": "1. Cut chicken...\n2. Heat wok...",
  "tags": "quick,asian",
  "ingredients": [
    {"quantity": 2, "unit": "lb", "item": "chicken breast", "grocery_section": "meat"},
    {"quantity": 1, "unit": "tbsp", "item": "soy sauce", "grocery_section": "pantry"}
  ]
}
```

### 3.2 Meal Plans

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/meals?week={ISO date} | Get meal plan for a week |
| PUT | /api/meals | Assign recipe to slot (upsert) |
| DELETE | /api/meals/{id} | Remove recipe from slot |

**PUT /api/meals body:**
```json
{
  "week_start": "2026-02-16",
  "day_of_week": 0,
  "meal_slot": "dinner",
  "recipe_id": 42
}
```

**GET response includes recipe title, prep+cook time for display.**

**Copy to Multiple Slots (meal prep):**
The Vision explicitly requires that users can copy a recipe to multiple slots for meal prep (e.g., the same lunch every day). This is handled **at the frontend**: the recipe picker issues one `PUT /api/meals` call per target slot. There is no batch endpoint. The frontend planner UI must support a "Copy to slots…" workflow (e.g., a modal or multi-select) that lets the user pick several day/slot combinations and fires individual PUT calls for each.

Acceptance criterion: User can assign the same recipe to Monday–Friday lunch slots (5 consecutive PUT calls succeed and all 5 cells display the recipe title).

### 3.3 Shopping Lists

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/shopping/generate | Generate list from week's meal plan |
| GET | /api/shopping/current | Get current shopping list with items |
| PATCH | /api/shopping/items/{id} | Toggle checked status |
| POST | /api/shopping/items | Add manual item |
| DELETE | /api/shopping/items/{id} | Remove item |

**POST /api/shopping/generate body:**
```json
{
  "week_start": "2026-02-16"
}
```

Aggregates ingredients across all planned meals for the week, normalizes units, groups by grocery section.

## 4. Frontend Views

### 4.1 Recipe Collection (default view)
- Grid of recipe cards: title, category badge, prep+cook time, tag chips
- Top bar: search input, category filter dropdown, tag filter
- "Add Recipe" button opens a form modal
- Click card opens detail view with full recipe + edit/delete buttons
- Recipe form: all fields from schema, dynamic ingredient list (add/remove rows)

### 4.2 Weekly Meal Planner
- 7-column grid (Mon-Sun), 4 rows (breakfast, lunch, dinner, snack)
- Each cell shows assigned recipe title or "+" to add
- Click "+" opens recipe picker (searchable list from collection)
- Click assigned recipe shows options: view recipe, swap, clear
- Week navigation: prev/next arrows, "This Week" button
- Day summary row: total prep+cook time for that day

### 4.3 Shopping List
- "Generate from This Week" button (with confirmation if list exists)
- Items grouped by grocery section with section headers
- Each item: checkbox, quantity + unit, item name
- Checked items move to bottom / show strikethrough
- "Add Item" input at top for manual additions
- Item count summary: "12 items, 5 checked"

### 4.4 Navigation
- Top nav bar with three tabs: Recipes, Meal Plan, Shopping List
- Active tab highlighted
- SPA routing via hash (#recipes, #planner, #shopping)

## 5. Acceptance Criteria

### Epic 1: Recipe Collection
- [ ] Can create a recipe with title, category, ingredients, and instructions
- [ ] Can edit and delete existing recipes
- [ ] Can filter by category and search by title/ingredient
- [ ] Can filter by tag
- [ ] Recipe cards display correctly in grid layout
- [ ] Ingredient list supports add/remove rows dynamically

### Epic 2: Weekly Meal Planner
- [ ] 7-day grid displays with meal slots
- [ ] Can assign recipes from collection to any slot
- [ ] Can clear and swap slot assignments
- [ ] Can navigate between weeks
- [ ] Day summary shows total prep+cook time
- [ ] Meal plan persists across page reloads

### Epic 3: Shopping List
- [ ] Generate aggregated list from current week's meal plan
- [ ] Ingredients with compatible units are merged (unit normalization)
- [ ] Items grouped by grocery section
- [ ] Can check/uncheck items
- [ ] Can add manual items
- [ ] Can remove items
- [ ] List persists across page reloads
- [ ] Generating new list replaces old one (with confirmation)
