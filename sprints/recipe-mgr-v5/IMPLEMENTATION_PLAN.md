# Implementation Plan (rendered from state)

Generated: 2026-03-04T12:44:11.839156


## Foundation

- [x] **1.1**: Create project scaffold: backend/ with main.py (FastAPI app with health check, static mounting, CORS, startup), database.py (SQLite connection with FK enforcement, schema creation for all 5 tables from PRD section 2.1), models.py (Pydantic models for Recipe, Ingredient, MealPlan, ShoppingList request/response). Create frontend/ with index.html (SPA shell, nav bar), css/ and js/ dirs. Create requirements.txt (fastapi, uvicorn). Create data/ dir with .gitkeep.
  - Value: Establishes the runnable skeleton — user can start the server and see a page load, proving the architecture works end-to-end before any features are built.
  - Acceptance: python -m uvicorn backend.main:app runs without errors. GET /api/health returns 200. GET / serves index.html. All 5 DB tables created on startup. Directory structure matches PRD section 1.3.

- [x] **1.2**: Create CSS design system in frontend/css/style.css: dark theme with CSS custom properties for colors (--bg-primary, --bg-secondary, --bg-card, --text-primary, --text-muted, --accent, --accent-hover, category colors for breakfast/lunch/dinner/snack/dessert), spacing scale (--space-xs through --space-xl), shadow depths (--shadow-sm/md/lg), border-radius scale, transition timing. Base reset, body styles, nav bar, card grid layout, modal overlay, form controls, button variants, badge/chip styles, responsive breakpoints at 768px and 1024px.
  - Value: Consistent professional dark theme across all views — the app looks production-quality from the first screen, not like a prototype.
  - Acceptance: CSS loads without errors. Dark theme renders with consistent colors. Nav bar visible. Cards, buttons, badges, modals all have defined styles. Responsive at 768px and 1024px. Each recipe category has a distinct color variable.
  - Deps: 1.1

- [x] **1.3**: Implement seed data in database.py: on first run (when recipes table is empty), insert 5 sample recipes covering all categories (breakfast, lunch, dinner, snack, dessert) with 3-6 ingredients each spanning produce/meat/dairy/pantry/frozen/other sections and varied units (tsp, tbsp, cup, oz, lb, whole). Use the examples from PRD section 2.3 as a baseline. Ensure ingredients have correct sort_order and grocery_section values.
  - Value: User opens the app for the first time and immediately sees a populated recipe collection — no empty state, no manual data entry needed to explore the app.
  - Acceptance: On fresh DB, 5 recipes appear with correct categories. Each recipe has 3-6 ingredients. All 5 categories represented. Multiple grocery sections and unit types used. GET /api/recipes returns 5 items.
  - Deps: 1.1


## Backend

- [x] **2.1**: Implement Recipe CRUD API routes in backend/routes/recipes.py: GET /api/recipes with query params ?category=, ?tag=, ?search= (search across title, description, ingredient items). GET /api/recipes/{id} returns recipe with ingredients array. POST /api/recipes creates recipe + ingredients in transaction. PUT /api/recipes/{id} updates recipe, replaces ingredients. DELETE /api/recipes/{id} cascades to ingredients and meal_plans with warning if recipe is in active meal plans. Register router in main.py.
  - Value: Cook can create, browse, edit, and delete their recipe collection through a reliable API — the backbone of the entire app.
  - Acceptance: POST creates recipe with ingredients, returns 201. GET list supports category/tag/search filters and combinations. GET by id includes ingredients array. PUT replaces recipe and ingredients. DELETE removes recipe and cascaded data. All return proper HTTP status codes.
  - Deps: 1.1, 1.3

- [x] **2.2**: Implement Meal Plan API routes in backend/routes/meals.py: GET /api/meals?week={ISO date} returns all meal assignments for that week with recipe title, prep_time, cook_time. PUT /api/meals upserts a recipe into a day/slot (week_start + day_of_week + meal_slot). DELETE /api/meals/{id} removes assignment. Validate week_start is a Monday. Include recipe details in response for frontend display. Register router in main.py.
  - Value: Cook can build and modify their weekly meal plan through the API — assigning recipes to specific days and meal slots.
  - Acceptance: PUT assigns recipe to slot, returns 200. Duplicate PUT to same slot replaces existing. GET returns week plan with recipe titles and times. DELETE clears a slot. week_start validated as Monday. Response includes recipe title, prep_time_minutes, cook_time_minutes.
  - Deps: 1.1, 2.1

- [x] **2.3**: Implement Shopping List API in backend/routes/shopping.py: POST /api/shopping/generate aggregates ingredients from all meal plan entries for the given week, normalizes compatible units (tsp->tbsp->cup, oz->lb, count equivalents), groups by grocery_section, creates shopping_list + shopping_items rows. Unit normalization: store as single decimal value in largest applicable unit (e.g., 4 tsp = 1.3 tbsp, per PRD 2.2). GET /api/shopping/current returns current list with items. PATCH /api/shopping/items/{id} toggles checked. POST /api/shopping/items adds manual item. DELETE /api/shopping/items/{id} removes item. Register in main.py.
  - Value: Cook generates a smart shopping list from their meal plan — ingredients auto-aggregated and unit-normalized so they buy the right amounts.
  - Acceptance: Generate merges 2 cups + 1 cup into 3 cups. 4 tsp converts to 1 tbsp + 1 tsp. Items grouped by grocery_section. Check/uncheck persists. Manual items addable. Delete works. Regenerating replaces old list.
  - Deps: 1.1, 2.2

- [x] **2.4**: Write pytest API integration tests in tests/test_api.py using FastAPI TestClient: test recipe CRUD (create, read, update, delete, search/filter), test meal plan operations (assign, get week, clear slot, week_start validation), test shopping list generation (unit normalization: tsp->tbsp, cup aggregation, grouping by section), test manual item add, test check toggle, test cascade delete (recipe deletion removes meal plan entries). At least 15 test cases covering all endpoints.
  - Value: Automated regression safety net — ensures backend correctness is verified and future changes do not break existing functionality.
  - Acceptance: pytest tests/test_api.py passes all tests. Coverage includes: recipe CRUD + filters, meal plan CRUD, shopping generation with unit normalization, manual items, cascade deletes. At least 15 test functions.
  - Deps: 2.1, 2.2, 2.3


## Frontend

- [x] **3.1**: Build SPA router and shared utilities in frontend/js/app.js: hash-based routing (#recipes, #planner, #shopping) with default to #recipes. Navigation tab highlighting. Shared API helper (fetch wrapper with error handling, base URL). Shared state for current week (ISO Monday date). Utility functions: formatTime, formatDate, debounce for search. Extract reusable UI components (modal, toast) to keep modules under 400 lines. Mount navigation click handlers. Load correct view module on hash change.
  - Value: Smooth single-page navigation between the three main views — cook switches between recipes, planner, and shopping without page reloads.
  - Acceptance: Hash navigation works between #recipes, #planner, #shopping. Active tab highlighted. Default route loads recipes. API helper handles fetch with JSON parsing and error display. Week state tracks current Monday.
  - Deps: 1.1, 1.2

- [x] **3.2**: Build Recipe Collection UI in frontend/js/recipes.js: Grid of recipe cards showing title, category color badge, prep+cook time, tag chips with hover elevation effects. Top filter bar with search input (debounced), category dropdown, tag filter. Add Recipe button opens modal form with all fields: title, description, category select, prep/cook time, servings, instructions textarea, tags input, dynamic ingredient rows (quantity, unit select, item, grocery_section select, add/remove buttons). Click card opens detail view with edit/delete (delete shows confirmation warning if recipe is in meal plan).
  - Value: Cook can visually browse their recipe collection with rich cards, search/filter to find recipes fast, and create/edit recipes through an intuitive modal form.
  - Acceptance: Recipe cards render in grid with category badges and tag chips. Search filters by title/description/ingredient. Category dropdown filters. Tag filter works. Add/edit modal has all fields with dynamic ingredient rows. Delete shows confirmation. Cards have hover elevation.
  - Deps: 3.1, 2.1

- [x] **3.3**: Build Weekly Meal Planner UI in frontend/js/planner.js: 7-column grid (Mon-Sun) with 4 rows (breakfast, lunch, dinner, snack). Each cell shows assigned recipe title or "+" button. Click "+" opens recipe picker modal (searchable recipe list from API). Click assigned recipe shows context menu: view recipe, swap (reopens picker), copy to slots (multi-select day/slot modal), clear. Week navigation with prev/next arrows and This Week button. Day summary row showing total prep+cook time.
  - Value: Cook plans their entire week at a glance — assigning recipes to meal slots, copying for meal prep, and seeing time estimates to balance effort across days.
  - Acceptance: 7x4 grid renders with day headers and meal slot labels. "+" opens searchable recipe picker. Assigning recipe shows title in cell. Clear removes assignment. Copy to slots modal allows multi-select and fires PUT calls. Week nav changes displayed week. Day summary shows aggregated prep+cook time.
  - Deps: 3.1, 2.2

- [x] **3.4**: Build Shopping List UI in frontend/js/shopping.js: "Generate from This Week" button with confirmation dialog if list exists. Items grouped by grocery section with styled section headers (produce, meat, dairy, pantry, frozen, other). Each item row: checkbox, quantity + unit, item name. Checked items get strikethrough and move to section bottom. "Add Item" form at top for manual entries (item name, quantity, unit, section). Item count summary bar ("12 items, 5 checked"). Delete button per item.
  - Value: Cook generates a smart shopping list from their plan and uses it while shopping — checking items off, adding extras, all organized by store section.
  - Acceptance: Generate button creates list from current week plan. Items grouped by section with headers. Checkboxes toggle with strikethrough. Checked items sort to bottom. Manual add works with all fields. Summary shows correct counts. Delete removes items. List persists across page reload.
  - Deps: 3.1, 2.3


## Integration

- [x] **4.1**: End-to-end integration testing and bug fixes: Start server, verify all 3 workflows via API. Test recipe creation, assign to meal plan, generate shopping list, check items. Verify unit normalization edge cases. Fix issues found. Verify cascade deletes (delete recipe in meal plan). Verify combined search filters. Ensure 5 seed recipes load. Test week navigation. Verify data persists across server restart.
  - Value: Confidence that the full user journey works end-to-end, every workflow from Vision is verified.
  - Acceptance: Server starts clean. 5 seed recipes visible. Create recipe works. Assign to planner works. Shopping list aggregates correctly. Unit normalization verified. Cascade delete verified. Combined search/filter works. Data persists after restart. All pytest tests pass.
  - Deps: 2.4, 3.2, 3.3, 3.4


## Polish

- [x] **4.2**: Visual polish and UX refinement: Add smooth transitions on card hover (transform + shadow), modal backdrop blur, button press effects, loading spinners during API calls, empty state messages (no recipes yet, no meal plan, no shopping list). Animate section expand/collapse in shopping list. Add toast notifications for success/error feedback. Style form validation errors. Ensure responsive layout works at 320px-1920px+. Add keyboard navigability for modals (Escape to close, Tab order).
  - Value: The app feels polished and responsive, not like a prototype. Visual feedback on every interaction builds user confidence.
  - Acceptance: Cards have hover elevation with smooth transition. Modals have backdrop blur and close on Escape. Loading states shown during API calls. Toast notifications on create/edit/delete. Empty states have helpful messages. Forms show validation errors. Responsive from 320px to 1920px+. Tab order logical in modals.
  - Deps: 3.2, 3.3, 3.4


## Unphased

- [x] **CE-2-13**: Clarify in task 2.3 description: 'When upconversion yields a remainder, store as two separate shopping_items rows (e.g., 4 tsp becomes one row of 1 tbsp and one row of 1 tsp for the same item). Alternatively, store as the largest whole unit with one decimal place (1.3 tbsp) per PRD section 2.2.' Pick one approach explicitly.
  - Value: Unit normalization is a core value proposition. If the builder implements it wrong (e.g., stores '1.3 tbsp' as a decimal vs. splitting into whole + remainder), the shopping list won't match what the user expects and tests will fail against unclear acceptance criteria.
  - Acceptance: Fix: Task 2.3 unit normalization remainder representation is ambiguous. PRD says '4 tsp -> 1 tbsp + 1 tsp' but the shopping_items table has single quantity/unit columns. It is unclear whether this becomes one row with a formatted string like '1 tbsp + 1 tsp' or two separate shopping_items rows. The builder will have to make a design decision with no guidance, risking a rework if the evaluator disagrees.

- [x] **CE-2-14**: 1. Resolve the unit normalization representation in task 2.3 (recommend: store as single decimal value in largest applicable unit, e.g., 1.3 tbsp, per PRD 2.2 one-decimal-place rule). 2. Add delete warning to task 2.1/3.2. 3. Mention shared UI module extraction in task 3.1 for file size management. After these fixes, plan is SHIP_READY.
  - Value: Without resolving the blocking issue, the builder may implement unit normalization one way, the evaluator may expect another, and rework follows. The degraded issues risk incomplete polish and a missing Vision-specified user warning.
  - Acceptance: Fix: VERDICT SUMMARY: Plan has 1 blocking issue (unit normalization representation ambiguity), 3 degraded issues (polish task file coverage, missing delete warning from Vision, frontend file size risk), and 3 polish issues (port config, requirements.txt path, routes dir). The blocking issue must be resolved before the builder starts task 2.3 — the unit normalization design decision affects the DB schema interpretation, the API response format, and the test assertions. The degraded issues are real but a competent builder can navigate them. Overall structure, phasing, dependencies, and value alignment are strong.

- [ ] **CE-7-15**: Either: (1) Add trailing slashes to frontend API calls in recipes.js lines 106 and 441 (/recipes/ instead of /recipes), and planner.js lines 112, 273, 395 (/meals/ instead of /meals). OR (2) Remove trailing slashes from route decorators in recipes.py and meals.py (@router.get('') instead of @router.get('/')). OR (3) Add redirect_slashes=True to FastAPI app constructor (though this may interact poorly with static mount). Option 1 is simplest.
  - Value: User opens the app and sees an empty recipe list (404 error). Clicking Add Recipe and submitting fails silently (405 error). Navigating to Meal Plan shows empty grid that cannot be populated (404/405). The entire application is non-functional in production serving mode.
  - Acceptance: Fix: Trailing slash mismatch: Frontend calls /api/recipes and /api/meals (no trailing slash) but FastAPI routes are registered at /api/recipes/ and /api/meals/ (with trailing slash). The StaticFiles mount at / catches the non-slashed paths first, returning 404 (GET) or 405 (POST/PUT). This breaks ALL primary user workflows: recipe list loading, recipe creation, meal plan loading, and meal assignment.

- [ ] **CE-7-16**: Simplest fix: In recipes.js change line 106 from apiCall('/recipes') to apiCall('/recipes/') and line 441 from apiCall('/recipes') to apiCall('/recipes/'). In planner.js change line 112 from apiCall('/meals?week=') to apiCall('/meals/?week='), lines 273 and 395 from apiCall('/meals') to apiCall('/meals/'). Total: 5 one-character changes.
  - Value: The deliverable has 1 CRITICAL issue that makes the entire frontend non-functional when served by the real FastAPI server. The trailing slash mismatch between frontend API calls and FastAPI route definitions means GET /api/recipes returns 404, POST /api/recipes returns 405, GET /api/meals?week=... returns 404, and PUT /api/meals returns 405. This breaks all three core workflows (recipe browsing/creation, meal planning, shopping list generation from planner). The backend API itself is well-built: 24 tests pass, unit normalization works correctly, cascade deletes work, data persists. The CSS design system is comprehensive with proper dark theme tokens, hover states, transitions, modal animations, and responsive breakpoints. The code architecture is clean with good separation of concerns. But none of this matters if the frontend cannot talk to the backend. FIX REQUIRED: Add trailing slashes to 5 frontend API calls (recipes.js lines 106 and 441, planner.js lines 112, 273, and 395) OR remove trailing slashes from route decorators in recipes.py and meals.py.
  - Acceptance: Fix: VERDICT SUMMARY
