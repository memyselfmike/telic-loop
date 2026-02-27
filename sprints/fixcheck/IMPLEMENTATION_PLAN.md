# Implementation Plan (rendered from state)

Generated: 2026-02-27T15:34:34.413430


## Foundation

- [ ] **1.1**: Implement JSON-file persistence module (persistence.js) exporting readNotes() and writeNotes(notes). readNotes returns parsed array from data/notes.json or empty array if file missing/empty. writeNotes serializes and overwrites atomically. Refactor server.js: add express.static for public/ dir with extensions:["html"] so /stats resolves to stats.html, wire express.json() middleware, export app via module.exports and only call app.listen when require.main===module (enables Supertest testing). Create public/ directory.
  - Value: Enables all downstream features to persist and retrieve note data reliably — the foundation for notes that survive server restarts. App export pattern enables automated testing.
  - Acceptance: 1. require(./persistence) returns {readNotes, writeNotes}. 2. writeNotes([{id,title,body,createdAt}]) creates valid JSON at data/notes.json. 3. readNotes() returns the written array. 4. readNotes() returns [] when file missing or empty. 5. require(./server) returns Express app without starting listener.


## Core

- [ ] **1.2**: Implement Notes CRUD API routes in routes/notes.js, mounted at /api/notes in server.js. GET /api/notes returns all notes (200). POST /api/notes accepts {title,body}, validates both present and non-empty (400 with error message otherwise), generates id via crypto.randomUUID() and createdAt via new Date().toISOString(), persists via writeNotes, returns 201 with created note. GET /api/notes/:id returns note (200) or 404. DELETE /api/notes/:id removes note (204) or 404.
  - Value: Enables the user to create, retrieve, and delete notes programmatically — the API backbone consumed by the UI to deliver the full note management experience.
  - Acceptance: 1. GET /api/notes returns 200 with JSON array. 2. POST with valid {title,body} returns 201 with note including id and createdAt. 3. POST with missing/empty title or body returns 400. 4. GET /api/notes/:id returns 200 or 404. 5. DELETE /api/notes/:id returns 204 or 404.
  - Deps: 1.1

- [ ] **1.3**: Build Notes List page: public/index.html, public/app.js, public/style.css. Display all notes as cards with title and first 80 chars of body as preview. New Note button reveals inline form (title input, body textarea, Save button). Save calls POST /api/notes and appends card without reload. Each card has Delete button calling DELETE /api/notes/:id. Clicking title toggles full body expanded inline. Clean CSS with centered max-width layout, card borders/shadows, styled form, nav area with Stats link.
  - Value: Delivers the core user experience — user opens localhost:3000 and can immediately see, create, expand, and delete notes in a clean interactive interface.
  - Acceptance: 1. GET / serves page showing note cards with title + 80-char preview. 2. New Note form creates note; card appears without reload. 3. Click title expands full body; click again collapses. 4. Delete removes card and persists deletion. 5. Nav link to /stats is present.
  - Deps: 1.2


## Verification

- [ ] **1.4**: Install Jest and Supertest as devDependencies. Write API integration tests in tests/api.test.js covering all four CRUD endpoints: GET /api/notes (empty list, populated list), POST /api/notes (valid input returns 201, missing fields returns 400), GET /api/notes/:id (found 200, not-found 404), DELETE /api/notes/:id (found 204, not-found 404). Tests import app from server.js and use supertest. Each test resets data/notes.json to avoid state leakage. Add test script to package.json.
  - Value: Proves the API works correctly and catches regressions — automated verification that CRUD operations work as specified before the user relies on them.
  - Acceptance: 1. npm test runs Jest and all tests pass. 2. Tests cover all 4 endpoints for both success and error cases. 3. Tests verify status codes and response body shapes. 4. No state leakage between test runs.
  - Deps: 1.2

- [ ] **1.5**: End-to-end verification through the running app. Start server, create a note via the UI form (POST), verify it appears in the list with correct title and preview. Click title to expand and verify full body displays. Delete the note and verify it disappears from the list. Verify data/notes.json reflects all changes. Restart the server and verify a previously-created note survives the restart (JSON persistence proof).
  - Value: Proves the complete user journey works end-to-end — the definitive test that all pieces (UI, API, persistence) are wired together and delivering the promised CRUD experience.
  - Acceptance: 1. Create note via UI form succeeds and note appears in list. 2. Expand note shows full body. 3. Delete note removes it from list and JSON file. 4. Notes survive server restart. 5. All API responses have correct status codes.
  - Deps: 1.3, 1.4
