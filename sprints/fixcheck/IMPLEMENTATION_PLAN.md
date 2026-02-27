# Implementation Plan (rendered from state)

Generated: 2026-02-27T22:29:37.884950


## Foundation

- [x] **1.1**: Implement JSON-file persistence module (persistence.js) exporting readNotes() and writeNotes(notes). readNotes returns parsed array from data/notes.json or empty array if file missing/empty. writeNotes serializes and overwrites atomically. Refactor server.js: add express.static for public/ dir with extensions:["html"] so /stats resolves to stats.html, wire express.json() middleware, export app via module.exports and only call app.listen when require.main===module (enables Supertest testing). Create public/ directory.
  - Value: Enables all downstream features to persist and retrieve note data reliably — the foundation for notes that survive server restarts. App export pattern enables automated testing.
  - Acceptance: 1. require(./persistence) returns {readNotes, writeNotes}. 2. writeNotes([{id,title,body,createdAt}]) creates valid JSON at data/notes.json. 3. readNotes() returns the written array. 4. readNotes() returns [] when file missing or empty. 5. require(./server) returns Express app without starting listener.


## Core

- [x] **1.2**: Implement Notes CRUD API routes in routes/notes.js, mounted at /api/notes in server.js. GET /api/notes returns all notes (200). POST /api/notes accepts {title,body}, validates both present and non-empty (400 with error message otherwise), generates id via crypto.randomUUID() and createdAt via new Date().toISOString(), persists via writeNotes, returns 201 with created note. GET /api/notes/:id returns note (200) or 404. DELETE /api/notes/:id removes note (204) or 404.
  - Value: Enables the user to create, retrieve, and delete notes programmatically — the API backbone consumed by the UI to deliver the full note management experience.
  - Acceptance: 1. GET /api/notes returns 200 with JSON array. 2. POST with valid {title,body} returns 201 with note including id and createdAt. 3. POST with missing/empty title or body returns 400. 4. GET /api/notes/:id returns 200 or 404. 5. DELETE /api/notes/:id returns 204 or 404.
  - Deps: 1.1

- [x] **1.3**: Build Notes List page: public/index.html, public/app.js, public/style.css. Display all notes as cards with title and first 80 chars of body as preview. New Note button reveals inline form (title input, body textarea, Save button). Save calls POST /api/notes and appends card without reload. Each card has Delete button calling DELETE /api/notes/:id. Clicking title toggles full body expanded inline. Clean CSS with centered max-width layout, card borders/shadows, styled form, nav area with Stats link.
  - Value: Delivers the core user experience — user opens localhost:3000 and can immediately see, create, expand, and delete notes in a clean interactive interface.
  - Acceptance: 1. GET / serves page showing note cards with title + 80-char preview. 2. New Note form creates note; card appears without reload. 3. Click title expands full body; click again collapses. 4. Delete removes card and persists deletion. 5. Nav link to /stats is present.
  - Deps: 1.2

- [x] **2.1**: Implement GET /api/stats endpoint in routes/stats.js, mounted at /api/stats in server.js. Read all notes via readNotes(). Compute totalNotes (array length), averageBodyLength (mean of body.length, rounded to integer, 0 when no notes), newestDate (max createdAt ISO string, null when no notes), oldestDate (min createdAt ISO string, null when no notes). Return 200 JSON with all four fields. Handle zero-notes edge case gracefully.
  - Value: Enables the stats dashboard to display real-time aggregate data computed from existing notes — the data backbone for the stats page that lets users understand their notes collection at a glance.
  - Acceptance: 1. GET /api/stats returns 200 with JSON containing totalNotes, averageBodyLength, newestDate, oldestDate. 2. With 3 notes, totalNotes=3 and averageBodyLength reflects actual mean. 3. newestDate/oldestDate match the most recent and earliest createdAt. 4. With zero notes, returns totalNotes=0, averageBodyLength=0, newestDate=null, oldestDate=null.
  - Deps: 1.1

- [x] **2.2**: Build Stats Dashboard page: public/stats.html and public/stats.js. stats.html has same header/nav pattern as index.html with NoteBox title and Back to Notes link. Main section displays four stat cards: Total Notes, Average Body Length, Newest Note Date, Oldest Note Date. stats.js fetches GET /api/stats on load and populates card values. Dates formatted as readable locale strings. Zero-notes state shows sensible defaults (0 counts, "No notes yet" for dates). Append stats-page styles to existing style.css.
  - Value: Delivers the stats dashboard experience — user navigates to /stats and instantly sees a clear summary of their notes collection with four key metrics, fulfilling the Vision promise of a stats page.
  - Acceptance: 1. GET /stats serves stats.html with four stat cards rendered. 2. Stats values match current notes data from /api/stats. 3. Dates displayed in human-readable format (not raw ISO). 4. Zero-notes state shows 0 total, 0 average, no-dates message. 5. Back to Notes link navigates to /.
  - Deps: 2.1


## Verification

- [x] **1.4**: Install Jest and Supertest as devDependencies. Write API integration tests in tests/api.test.js covering all four CRUD endpoints: GET /api/notes (empty list, populated list), POST /api/notes (valid input returns 201, missing fields returns 400), GET /api/notes/:id (found 200, not-found 404), DELETE /api/notes/:id (found 204, not-found 404). Tests import app from server.js and use supertest. Each test resets data/notes.json to avoid state leakage. Add test script to package.json.
  - Value: Proves the API works correctly and catches regressions — automated verification that CRUD operations work as specified before the user relies on them.
  - Acceptance: 1. npm test runs Jest and all tests pass. 2. Tests cover all 4 endpoints for both success and error cases. 3. Tests verify status codes and response body shapes. 4. No state leakage between test runs.
  - Deps: 1.2

- [x] **2.3**: Write stats API tests in tests/stats.test.js using Jest + Supertest. Test GET /api/stats with zero notes returns {totalNotes:0, averageBodyLength:0, newestDate:null, oldestDate:null}. Create 2+ notes via POST /api/notes, then verify stats reflect correct count, average body length, and correct newest/oldest dates. Delete a note, verify stats update. Ensure test isolation by resetting data/notes.json between tests.
  - Value: Proves the stats computation is correct and stays correct — automated regression protection for the aggregate calculations so users always see accurate statistics.
  - Acceptance: 1. npm test runs all tests including stats tests and they pass. 2. Zero-notes case returns correct defaults. 3. Multi-note case returns accurate totalNotes, averageBodyLength, newestDate, oldestDate. 4. Stats update correctly after note deletion. 5. No test state leakage.
  - Deps: 2.1


## Unphased

- [ ] **CLEANUP-debug-artifacts**: Still 69 debug artifacts in production code
  - Value: Remove debug artifacts before shipping
  - Acceptance: Zero print/console.log/breakpoint/debugger in non-test files. No .log, .bak, .tmp, or .orig files in project root or data directories.

- [ ] **SPLIT-FN-final-e2e-check-js**: Split long functions in final-e2e-check.js: finalCheck(87L). Extract helper functions to keep each function under 50 lines.
  - Value: Improve readability and testability of final-e2e-check.js
  - Acceptance: No function in final-e2e-check.js exceeds 50 lines. All existing tests still pass.

- [ ] **SPLIT-FN-verify-e2e-js**: Split long functions in verify-e2e.js: verify(140L). Extract helper functions to keep each function under 50 lines.
  - Value: Improve readability and testability of verify-e2e.js
  - Acceptance: No function in verify-e2e.js exceeds 50 lines. All existing tests still pass.

- [x] **VRC-37-gap-stats-tests**: Complete task 2.3: Write stats API tests in tests/stats.test.js. Test zero-notes edge case, multi-note correctness, stats update after note deletion. Ensure test isolation via notes.json reset between tests.
  - Value: Stats API integration tests not yet written. Task 2.3 pending. Without tests, we cannot verify stats computation correctness or catch regressions.
  - Acceptance: Gap 'gap-stats-tests' resolved: Stats API integration tests not yet written. Task 2.3 pending. Without tests, we cannot verify stats computation correctness or catch regressions.

- [x] **VRC-37-gap-stats-ui**: Complete task 2.2: Build Stats Dashboard page with stats.html and stats.js. Display four stat cards (Total Notes, Average Body Length, Newest Note Date, Oldest Note Date) populated from GET /api/stats. Add back-to-notes navigation link. Styles appended to existing style.css.
  - Value: Stats dashboard page (/stats) not yet implemented. Task 2.2 pending execution. User cannot view the promised stats metrics without this UI.
  - Acceptance: Gap 'gap-stats-ui' resolved: Stats dashboard page (/stats) not yet implemented. Task 2.2 pending execution. User cannot view the promised stats metrics without this UI.

- [x] **VRC-6-gap-1**: Task 1.5 is already in the plan and unblocked — execute it to verify the complete user journey: create note via UI → verify list update → expand → delete → restart server → verify persistence
  - Value: End-to-end verification not yet run — task 1.5 is pending. Cannot confirm that all pieces (UI, API, persistence) work together from the user perspective through the running app. This is the definitive proof of VALUE.
  - Acceptance: Gap 'gap-1' resolved: End-to-end verification not yet run — task 1.5 is pending. Cannot confirm that all pieces (UI, API, persistence) work together from the user perspective through the running app. This is the definitive proof of VALUE.
