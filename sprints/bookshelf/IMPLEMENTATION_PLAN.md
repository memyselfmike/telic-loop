# Implementation Plan (rendered from state)

Generated: 2026-03-04T18:26:47.642460


## Infrastructure

- [x] **1.1**: Create docker-compose.yml with 4 services: api (node:20-alpine, port 3000, depends_on db+search healthy, env vars MEILI_HOST=http://search:7700 and MEILI_KEY=bookshelf_dev_key), db (postgres:16-alpine, port 5432, pg_isready healthcheck, named volume pgdata, env var DATABASE_URL=postgres://postgres:postgres@db:5432/bookshelf), search (meilisearch:v1.6, port 7700, curl healthcheck, named volume msdata, MEILI_MASTER_KEY=bookshelf_dev_key), frontend (nginx:alpine, port 8080, depends_on api). Create api/Dockerfile (node:20-alpine, npm install, CMD node server.js). Create frontend/Dockerfile and frontend/nginx.conf with /api/* reverse proxy to http://api:3000 (eliminates CORS) and SPA fallback for frontend routes.
  - Value: docker compose up starts all 4 services with zero manual setup - the foundational promise of the Vision
  - Acceptance: docker compose up builds and starts all 4 containers. docker compose ps shows all healthy. curl localhost:8080 returns HTML. curl localhost:7700/health returns available. nginx proxies /api requests to backend.

- [x] **1.2**: Create db/init.sql with books table: id UUID PRIMARY KEY DEFAULT gen_random_uuid(), title VARCHAR(500) NOT NULL, author VARCHAR(500) NOT NULL, genre VARCHAR(100), cover_url TEXT, status VARCHAR(20) DEFAULT want_to_read CHECK(status IN (want_to_read,reading,finished,abandoned)), rating INTEGER CHECK(rating BETWEEN 1 AND 5), notes TEXT, date_added TIMESTAMPTZ DEFAULT NOW(), date_finished TIMESTAMPTZ. Mount in docker-compose.yml as /docker-entrypoint-initdb.d/init.sql.
  - Value: Persistent data store with validated schema ensures books survive restarts and have consistent data
  - Acceptance: After docker compose up, connect to Postgres and SELECT from books table. Schema matches PRD. Constraints enforce valid status values and rating range 1-5. UUID generation works.
  - Deps: 1.1


## Backend

- [x] **2.1**: Create api/package.json with express, pg, and cors dependencies only (no node-fetch — Node 20 has built-in fetch; no uuid — Postgres gen_random_uuid handles IDs). Create api/db.js with pg Pool from DATABASE_URL env var. Create api/server.js with Express app: CORS enabled, JSON parsing, health GET / returning {status:ok}. Verify API starts, connects to Postgres, responds to health check.
  - Value: Working API server connected to Postgres is the backbone for all book CRUD operations
  - Acceptance: docker compose up starts api. curl localhost:3000/ returns {status:ok}. API logs confirm Postgres connection. package.json has only express, pg, cors as dependencies.
  - Deps: 1.2

- [x] **2.2**: Create api/routes/books.js with Express Router: GET /api/books (list all, ?status= filter), GET /api/books/:id (single by UUID), POST /api/books (create, title+author required, status defaults want_to_read, returns 201), PUT /api/books/:id (update fields, returns updated), DELETE /api/books/:id (returns 204). All use parameterized SQL queries via db.js Pool. Proper error handling: 404 for missing, 400 for validation. Register router in server.js.
  - Value: Users can create, view, update, and delete books - the core data operations everything depends on
  - Acceptance: curl POST /api/books with title+author returns 201. GET /api/books returns array. GET /api/books?status=reading filters. PUT updates fields. DELETE returns 204. 404 for missing IDs. 400 for missing required fields.
  - Deps: 2.1

- [x] **2.3**: Create api/search.js wrapping MeiliSearch HTTP API via built-in fetch: reads MEILI_HOST and MEILI_KEY from process.env, passes Authorization: Bearer {MEILI_KEY} header with all requests. init() configures books index (searchable: title/author/genre/notes, filterable: status/genre/rating) with retry loop (up to 10 attempts, 2s delay) since MeiliSearch may still be starting. addOrUpdate(book) upserts doc. remove(id) deletes doc. search(query) returns hits. Call search.init() in server.js on startup after DB connects. Create api/routes/search.js with GET /api/search?q= route that calls search.search(query) and returns results array. Register search router in server.js. Integrate into books.js: after POST/PUT/DELETE, fire-and-forget addOrUpdate/remove call (MeiliSearch processes fast enough for 1s requirement).
  - Value: Instant full-text search across title, author, genre, notes - the key differentiator over SQL LIKE queries
  - Acceptance: POST a book, GET /api/search?q=<partial_title> returns it. Update notes, search by note text works. Delete book, search no longer returns it. All within 1s. Server logs show successful MeiliSearch init on startup.
  - Deps: 2.2

- [x] **2.4**: Create api/routes/stats.js with GET /api/stats: queries Postgres for total_books (COUNT), books_by_status (GROUP BY status with count per status), genres (GROUP BY genre with count, ORDER BY count DESC), average_rating (AVG of non-null ratings rounded to 1 decimal). Returns single JSON object. Register in server.js. Handle empty library gracefully (zeros, empty arrays).
  - Value: Users see reading stats - total books, status breakdown, genre distribution, average rating - fulfilling dashboard promise
  - Acceptance: After adding books with different statuses/genres/ratings, GET /api/stats returns accurate counts. Empty library returns {total_books:0, books_by_status:[], genres:[], average_rating:null}.
  - Deps: 2.1


## Frontend_Foundation

- [x] **3.1**: Create frontend/index.html: header (h1 title, search input, Add Book button), main (filter tabs, book grid, stats dashboard hidden), modal container. Link CSS (variables.css, base.css, components.css) and JS (api.js, library.js, modal.js, search.js, stats.js, app.js via script tags in order). Create frontend/css/variables.css with design tokens: primary blue palette, status colors (amber/blue/green/gray), spacing scale (4-48px), shadow depths (sm/md/lg/xl), border-radius, font stack, transition timing vars.
  - Value: Design token foundation ensures visual consistency and production-quality polish across all components
  - Acceptance: index.html loads at localhost:8080 with proper structure. CSS variables defined. Page has header, main, modal containers. All CSS/JS files linked in correct order.
  - Deps: 1.1

- [x] **3.2**: Create frontend/css/base.css: CSS reset, box-sizing, body typography, responsive container (max-width 1400px), headings. Create frontend/css/components.css with ALL component styles: book cards (cover aspect-ratio, hover elevation+translateY+shadow transition), color-coded status badges, star rating (filled/empty), filter tabs (active underline), sticky header+search, modal (centered, backdrop-blur, slide-in), toast (slide-in-right), empty state, loading skeleton. All use design tokens. Responsive grid: 1col at 320px, 2col 768px, 3-4col 1280px+. Keyboard focus styles.
  - Value: Complete component styling in one file prevents CSS duplication and delivers production-quality polish
  - Acceptance: Cards elevate on hover with smooth transition. Status badges color-coded. Modals have backdrop blur. Responsive at 320px, 768px, 1280px. Focus styles visible for keyboard navigation.
  - Deps: 3.1


## Frontend_Features

- [x] **3.3**: Create frontend/js/api.js as global window.BookAPI object (IIFE pattern, no ES modules since vanilla JS with script tags). Functions: getBooks(status?), getBook(id), createBook(data), updateBook(id,data), deleteBook(id), searchBooks(query), getStats(). Each uses fetch() to /api/* (proxied by nginx to backend), throws on non-2xx with parsed error message, returns parsed JSON. Base URL is /api (relative, nginx proxies).
  - Value: Clean API abstraction lets all UI modules share reliable data fetching with consistent error handling
  - Acceptance: From browser console, BookAPI.getBooks() returns array. BookAPI.createBook({title,author}) returns created book. BookAPI.searchBooks(q) returns results. No CORS errors via nginx proxy.
  - Deps: 3.1, 2.2

- [x] **3.4**: Create frontend/js/library.js as window.Library (IIFE): on load, fetch via BookAPI.getBooks() and render card grid. Each card: cover image (or gradient placeholder with book icon if no URL), title, author, colored status badge, star rating (filled+empty). Filter tabs (All/Want to Read/Reading/Finished/Abandoned) re-fetch with ?status= and update active tab. Empty state message when no books match. Loading skeleton while fetching. Exposes Library.refresh() for other modules to trigger re-render.
  - Value: Users see their library at a glance - covers, ratings, reading status - the core experience promised in the Vision
  - Acceptance: Page loads showing book grid. Filter tabs switch statuses. Empty state shows friendly message. Cards show cover/title/author/badge/stars. Loading skeleton during fetch. Library.refresh() callable from console.
  - Deps: 3.2, 3.3

- [x] **3.5**: Create frontend/js/modal.js as window.Modal (IIFE): Add Book form with title (required), author (required), genre, cover URL (live preview), status dropdown, rating (clickable stars 1-5), notes textarea. Submit calls BookAPI.createBook(), shows toast, refreshes Library. Edit mode: pre-fills form, calls BookAPI.updateBook(). Detail view: full book info with formatted notes, Edit/Delete buttons. Delete shows confirm dialog, calls BookAPI.deleteBook(). Modals use slide-in animation and backdrop blur from components.css.
  - Value: Users can add, view details, edit, and delete books through polished modal interactions
  - Acceptance: Add Book opens form modal. Submit creates book, closes modal, refreshes library, shows success toast. Click card opens detail. Edit pre-fills and saves. Delete confirms and removes. Cover URL shows live preview.
  - Deps: 3.4

- [x] **3.6**: Create frontend/js/search.js as window.Search (IIFE): debounced input handler (300ms) on header search bar calls BookAPI.searchBooks(query). Results replace library grid using same card rendering from Library module. Clear search (empty input or X button) restores normal library view with current filter tab. Empty search results show friendly message. Visual indicator on search input when search is active (border color change, clear X icon).
  - Value: Users instantly find books by typing partial title, author, genre, or notes - the key search promise
  - Acceptance: Type partial title - matching books appear after 300ms debounce. Clear search restores library. Author name search works. Note text search works. Empty results show message. Active search has visual indicator.
  - Deps: 3.4, 2.3

- [x] **3.7**: Create frontend/js/stats.js as window.Stats (IIFE): fetch BookAPI.getStats() and render dashboard cards - total books count (large number), books per status (4 colored cards matching status badge colors with counts), genre distribution as CSS-only horizontal bar chart (bars proportional to count, each genre a distinct color), average rating as large filled stars. Dashboard toggled via Stats button in header. Auto-refreshes on navigate. Empty state shows friendly zeros.
  - Value: Users see reading habit insights - status breakdown, genre chart, average rating - fulfilling stats promise
  - Acceptance: Stats view shows total count, 4 status cards with accurate counts, genre bars proportional to data, average rating as stars. Matches actual book data. Empty library shows zeros gracefully.
  - Deps: 3.4, 2.4


## Integration

- [x] **3.8**: Create frontend/js/app.js as main entry point (IIFE, runs on DOMContentLoaded): initializes Library, wires header nav (Library/Stats toggle), search bar to Search module, Add Book button to Modal.openAdd(). Creates toast notification system (window.Toast) with success/error methods - styled container, auto-dismiss after 3s. Coordinates all modules via their public APIs (Library.refresh, Modal.open*, Search.clear, Stats.show). No console.log in production.
  - Value: All features wired into cohesive SPA with user feedback on actions via toast notifications
  - Acceptance: Page loads showing library. Nav toggles Library/Stats views. Add Book opens modal. Search works from header. Toasts appear on create/edit/delete with auto-dismiss. No console errors.
  - Deps: 3.4, 3.5, 3.6, 3.7


## Polish

- [x] **4.1**: End-to-end verification and visual polish: docker compose up, add 5+ sample books with varied statuses/genres/ratings via UI. Verify search finds books by partial title/author/notes. Verify filter tabs work. Verify stats dashboard accuracy. Verify delete removes from both Postgres and search. Fix any visual glitches at 320px and 1920px viewports. Ensure cover placeholders look intentional. Remove any console.log or debug artifacts. Verify data persists after docker compose down+up.
  - Value: Confirms all Vision promises work end-to-end and the app meets production-quality visual standards
  - Acceptance: All 8 PRD acceptance criteria pass: docker compose up works, CRUD persists+syncs search, partial search works, status filter works, delete removes everywhere, stats accurate, data survives restart, UI is polished.
  - Deps: 3.8


## Unphased

- [x] **CE-4-15**: Add to task 2.3 description: Create api/routes/search.js with GET /api/search?q= route that calls search.search(query) and returns results array. Register in server.js. Add api/routes/search.js to files_expected.
  - Value: Without the search endpoint, the entire frontend search feature (search bar, debounced search, search results) will fail. This is a core Vision promise: instant full-text search.
  - Acceptance: Fix: Task 2.3 missing explicit GET /api/search?q= route creation. The task describes the search module (init, addOrUpdate, remove, search functions) and integrating sync into books.js, but never explicitly mentions creating the HTTP route handler for GET /api/search?q=. The acceptance criteria expect this route to work, and the frontend (tasks 3.3/3.6) depend on it, but the description and files_expected only list api/search.js and api/routes/books.js (for sync integration). A separate api/routes/search.js or explicit route in books.js must be specified.

- [x] **CE-4-16**: Add to task 1.1: set MEILI_HOST=http://search:7700 and MEILI_KEY=bookshelf_dev_key as env vars on the api service. Add to task 2.3: search.js reads MEILI_HOST and MEILI_KEY from process.env and passes Authorization: Bearer header with all MeiliSearch HTTP requests.
  - Value: All MeiliSearch operations from the API (index config, document sync, search queries) will fail with 401 Unauthorized. Search is completely broken.
  - Acceptance: Fix: Task 1.1 and 2.3 missing MeiliSearch API key propagation to API service. Task 1.1 sets MEILI_MASTER_KEY=bookshelf_dev_key on the search container, but the API container also needs this key (or a separate env var like MEILI_URL and MEILI_KEY) to authenticate its HTTP requests to MeiliSearch. Task 2.3 describes search.js wrapping the MeiliSearch HTTP API but never mentions reading the API key from env or passing Authorization headers.

- [x] **CE-4-17**: Change task 1.1 Dockerfile to use npm install instead of npm ci (appropriate for a dev-only project), or add package-lock.json generation to task 2.1 deliverables.
  - Value: Docker build for the API service will fail. The entire application cannot start.
  - Acceptance: Fix: Task 1.1 specifies npm ci in Dockerfile but task 2.1 only creates package.json without package-lock.json. npm ci requires package-lock.json to exist and will fail without it.

- [x] **CE-4-18**: Fix the 3 blocking issues by updating task descriptions: (1) Add search route to task 2.3, (2) Add MeiliSearch env vars to tasks 1.1 and 2.3, (3) Change npm ci to npm install in task 1.1 or add lockfile to task 2.1. Then address the 2 degraded issues.
  - Value: Without fixes, the application will fail to build (npm ci), fail to connect to search (missing auth), and have no search endpoint (missing route). Three of the eight Vision promises broken.
  - Acceptance: Fix: VERDICT: REVISE. The plan has strong overall architecture — clean separation of concerns, correct dependency ordering, excellent completeness against PRD, and no waste. However, 3 blocking issues must be fixed before implementation: (1) Missing GET /api/search?q= route handler — the search endpoint is never created as an HTTP route, only as a module function, (2) MeiliSearch API key not propagated to API service — all search operations will 401, (3) npm ci in Dockerfile without package-lock.json — Docker build will fail. Additionally, 2 degraded issues should be addressed: DATABASE_URL env var not specified in docker-compose, and no search re-index on startup for resilience. The 2 polish items are minor and can be handled by the builder.
