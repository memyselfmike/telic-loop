# Implementation Plan (rendered from state)

Generated: 2026-03-04T10:52:02.763791


## Backend-Foundation

- [x] **1.1**: Create project scaffold: backend/__init__.py, backend/main.py (FastAPI app with health endpoint at /api/health, static file mounting from frontend/, CORS middleware, port configurable via PORT env var defaulting to 8000), backend/database.py (SQLite connection with foreign keys enabled, schema creation for all 5 tables from PRD section 2.1, DB path at data/recipes.db), backend/models.py (Pydantic models for Recipe, Ingredient, MealPlan, ShoppingList, ShoppingItem request/response). Create requirements.txt with fastapi, uvicorn, httpx.
  - Value: Establishes the runnable skeleton — user can start the server and hit /api/health, proving the app is alive and the database is initialized.
  - Acceptance: python -m uvicorn backend.main:app starts without error. GET /api/health returns 200. SQLite DB is created at data/recipes.db with all 5 tables. All Pydantic models import without error.

- [x] **1.2**: Implement seed data in database.py: on first run (when recipes table is empty), insert 5 sample recipes covering all categories (breakfast, lunch, dinner, snack, dessert) with 3-6 ingredients each spanning different grocery_section values (produce, meat, dairy, pantry, frozen, other) and different units (tsp, tbsp, cup, oz, lb, whole). Use the examples from PRD section 2.3 as a base. Seed function called from app startup lifespan.
  - Value: User opens the app for the first time and immediately sees real recipe data — no empty-state confusion, instant demonstration of value.
  - Acceptance: After server start on fresh DB, GET /api/recipes returns 5 recipes. Each recipe has 3+ ingredients. Categories breakfast, lunch, dinner, snack, dessert are all represented. Grocery sections produce, meat, dairy, pantry are covered.
  - Deps: 1.1


## Backend-Recipes

- [x] **2.1**: Implement Recipe CRUD API routes in backend/routes/recipes.py. GET /api/recipes with query params: ?category= (exact match), ?tag= (partial match in comma-separated tags), ?search= (searches title, description, and ingredient items via JOIN). GET /api/recipes/{id} returns recipe with ingredients list. POST /api/recipes creates recipe + ingredients in transaction. PUT /api/recipes/{id} updates recipe and replaces ingredients. DELETE /api/recipes/{id} deletes recipe (CASCADE handles ingredients and meal_plans). Register router in main.py.
  - Value: Cook can build and manage their recipe collection — the core data that powers the entire app.
  - Acceptance: POST creates recipe with ingredients, returns 201. GET by ID returns recipe with ingredients array. GET list supports category, tag, and search filters independently and combined. PUT replaces recipe and ingredients. DELETE removes recipe and cascades. All return proper HTTP status codes.
  - Deps: 1.1


## Backend-Meals

- [x] **2.2**: Implement Meal Plan API routes in backend/routes/meals.py. GET /api/meals?week={ISO date} returns all meal plan entries for that week with recipe title, prep_time, cook_time joined from recipes table. PUT /api/meals upserts a recipe assignment to a specific week_start + day_of_week + meal_slot (uses INSERT OR REPLACE on the UNIQUE constraint). DELETE /api/meals/{id} removes a slot assignment. Response includes enough data for the frontend to render the weekly grid. Register router in main.py.
  - Value: Cook can plan their weekly meals by assigning recipes to day/slot combinations — the bridge between recipe collection and shopping.
  - Acceptance: PUT assigns recipe to slot, returns 200. GET with week param returns all slots for that week with recipe titles and times. PUT to same slot replaces previous assignment. DELETE clears a slot. Cascading delete of recipe also removes meal plan entries.
  - Deps: 1.1, 2.1


## Backend-Shopping

- [x] **2.3**: Implement Shopping List API in backend/routes/shopping.py with unit normalization. POST /api/shopping/generate aggregates ingredients across planned meals for a week, normalizes units using decimal format only (4 tsp = 1.3 tbsp, not remainder decomposition). Upconvert to largest unit yielding qty >= 1, round to one decimal. Volume: tsp->tbsp->cup. Weight: oz->lb. Count: whole/piece/each equivalent. GET /api/shopping/current returns latest list. PATCH /api/shopping/items/{id} toggles checked. POST /api/shopping/items adds manual item. DELETE /api/shopping/items/{id} removes. Register router.
  - Value: Cook gets an auto-generated, intelligently aggregated grocery list — the payoff of the entire planning workflow.
  - Acceptance: Generate from week with 2+ meals with overlapping ingredients. Verify quantities summed and units upconverted per decimal format: 4 tsp = 1.3 tbsp (single decimal value, NOT remainder decomposition like 1 tbsp + 1 tsp). DB schema has one qty+unit per shopping_item row so decimal is the only valid format. Items grouped by section. Toggle checked persists. Manual add works. Delete works. New list replaces old.
  - Deps: 1.1, 2.2


## Backend-Testing

- [x] **2.4**: Create pytest API integration tests in tests/test_api.py using httpx AsyncClient with FastAPI TestClient. Test recipe CRUD (create, read, update, delete, filters), meal plan operations (assign, get week, clear slot, cascade delete), and shopping list (generate with aggregation, unit normalization correctness, toggle checked, manual add/remove). Verify seed data loads on fresh DB. Cover edge cases: duplicate slot assignment, empty week generation, search with no results.
  - Value: Proves the entire backend API works correctly before any frontend is built — catches regressions early.
  - Acceptance: pytest tests/test_api.py passes all tests. Covers: recipe CRUD + filters, meal plan CRUD + cascade, shopping generation + unit normalization, seed data presence. At least 15 test cases.
  - Deps: 2.1, 2.2, 2.3


## Frontend-Foundation

- [x] **3.1**: Build the SPA shell: index.html with semantic HTML structure (nav bar with Recipes/Meal Plan/Shopping List tabs, main content area, modal container), css/style.css with professional dark theme (dark background, light text, accent colors, card styles, responsive grid, modal overlay, form styles, button states — must work 320px-1920px+). js/app.js with hash-based SPA router (#recipes, #planner, #shopping), navigation highlighting, shared API helper functions (fetchJSON wrapper with error handling), and view mounting lifecycle.
  - Value: Establishes the visual shell and navigation — user sees a polished, professional app frame that works across screen sizes.
  - Acceptance: Opening localhost:8000 shows dark-themed app with 3 nav tabs. Clicking tabs changes hash and content area. Page works at 320px and 1920px widths. All CSS variables and base styles are defined.
  - Deps: 1.1


## Frontend-Recipes

- [x] **3.2**: Build Recipe Collection UI in js/recipes.js. Grid of recipe cards showing title, category badge, prep+cook time, tag chips. Top filter bar with search input (debounced), category dropdown, tag filter. "Add Recipe" button opens modal form with all fields: title, description, category select, prep/cook time, servings, instructions textarea, tags input, dynamic ingredient rows (add/remove with quantity, unit select, item, grocery_section select). Card click opens detail view with edit/delete. Edit pre-fills form. Delete shows confirmation warning if recipe is assigned to meal plans (Vision requirement). All filters combine.
  - Value: Cook can browse, create, edit, search, and filter their recipe collection — the primary daily interaction with the app.
  - Acceptance: Recipe cards render in grid from API data. Search filters by title/ingredient in real-time. Category and tag filters work. Add form creates recipe with ingredients. Edit updates recipe. Delete removes with confirmation. Responsive at 320px+.
  - Deps: 3.1, 2.1, 1.2


## Frontend-Planner

- [x] **3.3**: Build Weekly Meal Planner UI in js/planner.js. 7-column grid (Mon-Sun) with 4 rows (breakfast, lunch, dinner, snack). Each cell shows assigned recipe title or "+" button. Click "+" opens recipe picker modal (searchable list from collection). Click assigned recipe shows options: view recipe, swap (re-pick), clear, copy to slots (multi-select day/slot modal for meal prep). Week navigation with prev/next arrows and "This Week" button. Day summary row showing total prep+cook time per day. Copy-to-slots fires individual PUT calls per slot.
  - Value: Cook can visually plan their entire week of meals — see gaps, balance effort across days, and meal-prep efficiently.
  - Acceptance: 7-day grid renders with slots. Assign recipe via picker. Clear and swap work. Copy-to-slots assigns same recipe to multiple slots. Week nav loads different weeks. Day totals update. Plan persists on reload.
  - Deps: 3.1, 2.2


## Frontend-Shopping

- [x] **3.4**: Build Shopping List UI in js/shopping.js. "Generate from This Week" button calls POST /api/shopping/generate with current planner week. Confirmation dialog if list already exists ("Replace current list?"). Empty state message when no list generated yet. Items displayed grouped by grocery section with section headers. Each item: checkbox, quantity+unit, item name. Checked items get strikethrough and sort to section bottom. "Add Item" form for manual additions (item name, quantity, unit, section). Remove button per item. Summary bar: "X items, Y checked". All mutations call API immediately for persistence.
  - Value: Cook gets an actionable shopping list they can use in the grocery store — the final value delivery of the entire workflow.
  - Acceptance: Generate creates list grouped by section. Checkboxes toggle with visual feedback. Manual add appears in correct section. Remove deletes item. Summary updates. List persists on page reload. Regenerate shows confirmation.
  - Deps: 3.1, 2.3


## Integration-Polish

- [x] **4.1**: End-to-end integration verification and polish. Test full user flow: browse seed recipes -> create a new recipe -> assign recipes to meal plan -> navigate weeks -> generate shopping list -> verify ingredient aggregation -> check off items -> add manual item -> reload and verify persistence. Fix any visual glitches, responsive breakpoints, keyboard navigation gaps, missing alt text, or error handling holes discovered during the flow. Ensure no console.log/TODO/FIXME remains in any source file.
  - Value: Proves the entire app works as one cohesive system — the promised outcome from the Vision is actually delivered end-to-end.
  - Acceptance: Full flow works without errors. No console.log or TODO/FIXME in source. Responsive at 320px, 768px, 1024px, 1920px. All API errors show user-friendly messages. Keyboard navigation works for core flows. All data persists across reload.
  - Deps: 3.2, 3.3, 3.4, 2.4


## Unphased

- [x] **CE-4-11**: Resolve the contradiction explicitly in the task description. Since the DB schema has one qty+unit per row, the correct approach is: for 4 tsp, create TWO shopping_item rows (1 tbsp + 1 tsp) for the same item, OR switch to decimal-only format (1.3 tbsp) and update the PRD expectation. Pick one and state it clearly. Recommendation: use decimal format (1.3 tbsp) since it is simpler and the DB schema naturally supports it — but the acceptance criteria must match the PRD, so note this as a deliberate deviation.
  - Value: Shopping list will either show incorrect unit conversions (wrong math) or violate the PRD spec. The builder has conflicting instructions and will waste time resolving the ambiguity.
  - Acceptance: Fix: Task 2.3 unit normalization spec contradicts PRD. The task says 'decimal format only (4 tsp = 1.3 tbsp, not remainder decomposition)' but PRD section 2.2 explicitly requires remainder decomposition: '4 tsp -> 1 tbsp + 1 tsp'. The DB schema has one qty+unit per shopping_item row, which cannot represent '1 tbsp + 1 tsp' as a single row. This is an architectural conflict between PRD spec and data model that will cause the builder to guess.

- [x] **CE-4-12**: Add to task 2.1 acceptance criteria: GET /api/recipes/{id} response includes a 'meal_plan_count' integer field (COUNT of meal_plan rows referencing this recipe). The frontend delete confirmation in 3.2 can then check this field. Alternatively, add a query parameter to the meals endpoint.
  - Value: Without a way to check meal plan assignments, the frontend cannot show the warning the Vision requires. The user could delete a recipe without knowing it removes planned meals.
  - Acceptance: Fix: Task 3.2 (Recipe Collection UI) mentions 'Delete shows confirmation warning if recipe is assigned to meal plans' but neither the backend DELETE endpoint (task 2.1) nor any API provides a way to check if a recipe is assigned to meal plans. The frontend would need an endpoint like GET /api/meals?recipe_id={id} or the DELETE response needs to include assignment count, or the recipe detail response should include a meal_plan_count field.

- [x] **CE-4-13**: In task 3.1, specify that app.js maintains a shared state object (e.g., window.appState = { currentWeek: getMondayOfCurrentWeek() }) that the planner updates when navigating weeks, and the shopping view reads when generating. Or simplify: shopping always generates for 'this week' (the Monday of the current calendar week), matching the default planner view.
  - Value: The shopping list generate button won't know which week to generate for. The builder will have to invent a solution (localStorage, global variable, or always use current week), which may not match expectations.
  - Acceptance: Fix: Task 3.4 (Shopping List UI) needs to know the current planner week to call POST /api/shopping/generate, but the shopping view and planner view are separate SPA views with no shared state mechanism defined. Task 3.1 defines a hash-based router and 'shared API helper functions' but does not specify any shared state store. The shopping view needs to know what week the planner is currently viewing.

- [x] **CE-4-14**: Add to task 3.4 description: 'Include week navigation (prev/next/This Week) matching the planner, or reuse the same shared week state from app.js. The Generate button sends the currently displayed week_start to POST /api/shopping/generate.' This also means task 3.1 should define the shared week state.
  - Value: The shopping generate feature will either always use current week (limiting functionality) or fail to work because the week_start parameter is undefined.
  - Acceptance: Fix: Task 2.3 (Shopping API) specifies POST /api/shopping/generate takes a week_start parameter, but task 3.4 (Shopping UI) says the generate button uses 'current planner week'. There is no mechanism for the shopping UI to determine what week_start value to send. Should it: (a) always use the current calendar week, (b) read from a shared state set by the planner, or (c) include its own week picker? The PRD says 'from the weekly plan' and 'for the selected week', implying the user selects which week. But the shopping UI description has no week selector.

- [x] **CE-4-15**: Fix the 4 critical/blocking issues: (1) Decide unit normalization format — decimal-only is correct given DB schema, update acceptance to match. (2) Add meal_plan_count to recipe detail API response in task 2.1. (3) Define shared week state in task 3.1 app.js. (4) Add week context to task 3.4 shopping UI.
  - Value: Without fixing the critical and blocking issues, the builder will encounter ambiguous specs in 3 of the most complex tasks (2.3, 3.2, 3.4) and will either guess wrong or waste cycles asking for clarification.
  - Acceptance: Fix: OVERALL PLAN ASSESSMENT: The plan has strong architecture — good phasing (backend-first, then frontend, then integration), proper dependency chains, comprehensive test coverage, and clear value delivery per task. However, it has 1 critical issue (unit normalization PRD contradiction) and 3 blocking issues (missing meal-plan-count for delete warning, no shared week state mechanism, shopping UI lacks week selector) that will cause builder confusion or missing functionality. These must be resolved before implementation.

- [ ] **CE-9-16**: In filterRecipePicker() (planner.js line 190), the onclick handler is: onclick="assignMeal(${r.id})". It must be: onclick="assignMeal(${dayIndex}, '${slot}', ${r.id})". The dayIndex and slot variables need to be captured via closure — pass them as parameters to filterRecipePicker or capture them in the search event listener closure.
  - Value: When user types in the recipe picker search box (in meal planner), the filtered results render onclick handlers as assignMeal(recipeId) with only 1 argument, but the function signature is assignMeal(dayIndex, slot, recipeId). This means clicking any recipe after filtering will pass the recipe ID as dayIndex, undefined as slot, and undefined as recipeId. The API call will fail with a 404 (recipe not found for recipeId=undefined) or create a corrupt meal plan entry.
  - Acceptance: Fix: Recipe picker search filter breaks meal assignment — assignMeal called with wrong arguments after filtering

- [ ] **CE-9-17**: Add a keydown event listener for Escape in the modal.show() method: document.addEventListener("keydown", (e) => { if (e.key === "Escape") modal.hide(); }). Clean up the listener in modal.hide().
  - Value: Users expect to press Escape to close modals. The app uses modals extensively (recipe detail, recipe form, recipe picker, copy-to-slots, add item, meal options). Without Escape key support, keyboard-only users are stuck and all users lose a standard interaction pattern. The task 4.1 acceptance criteria explicitly requires keyboard navigation for core flows.
  - Acceptance: Fix: No keyboard escape to close modals — modal can only be closed by clicking X button or overlay background

- [ ] **CE-9-18**: merge_quantities() should return a list of (qty, unit) tuples — one per unit family — and the caller should insert multiple shopping_items rows for the same item when incompatible unit families are present. Currently at shopping.py line 146: the function returns only the first non-zero of volume/weight/count/other, discarding the rest.
  - Value: If a recipe has 2 cups flour and another has 100g flour (or a user adds an ingredient with both volume and weight units for the same item name), the shopping list generator silently drops the weight quantity and only shows the volume total. The PRD section 2.2 says incompatible units should be kept as separate lines, but merge_quantities() returns only one (qty, unit) tuple — the first non-zero aggregate. This means weight data is lost.
  - Acceptance: Fix: Mixed unit ingredients (same item with volume AND weight) silently drops weight data — only the first non-zero aggregate is returned

- [ ] **CE-9-19**: Fix the 3 must-fix issues: (1) CRITICAL: Fix filterRecipePicker onclick to pass dayIndex/slot/recipeId (not just recipeId). (2) BLOCKING: Add Escape key listener to modal.show()/hide(). (3) BLOCKING: Make merge_quantities return multiple rows for incompatible unit families. The 4 degraded issues (320px grid, shopping week nav, duplicate escapeHtml, fragile week math) should also be addressed if time permits.
  - Value: The critical bug (recipe picker filter breaks meal assignment) means users cannot search and assign recipes from the planner — a core workflow. The blocking issues (no Escape key for modals, mixed-unit data loss) degrade the experience significantly.
  - Acceptance: Fix: VERDICT: CONTINUE — 1 critical and 2 blocking issues must be fixed before shipping
