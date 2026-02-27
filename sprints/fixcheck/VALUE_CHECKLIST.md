# Value Checklist: fixcheck
Generated: 2026-02-27T16:14:57.718217

## VRC Status
- Value Score: 57%
- Verified: 4/7
- Blocked: 0
- Recommendation: CONTINUE
- Summary: Fallback VRC: carried forward from iteration 6 (57%)

## Tasks
- [x] **1.1**: Implement JSON-file persistence module (persistence.js) exporting readNotes() and writeNotes(notes). readNotes returns parsed array from data/notes.json or empty array if file missing/empty. writeNotes serializes and overwrites atomically. Refactor server.js: add express.static for public/ dir with extensions:["html"] so /stats resolves to stats.html, wire express.json() middleware, export app via module.exports and only call app.listen when require.main===module (enables Supertest testing). Create public/ directory.
- [x] **1.2**: Implement Notes CRUD API routes in routes/notes.js, mounted at /api/notes in server.js. GET /api/notes returns all notes (200). POST /api/notes accepts {title,body}, validates both present and non-empty (400 with error message otherwise), generates id via crypto.randomUUID() and createdAt via new Date().toISOString(), persists via writeNotes, returns 201 with created note. GET /api/notes/:id returns note (200) or 404. DELETE /api/notes/:id removes note (204) or 404.
- [x] **1.3**: Build Notes List page: public/index.html, public/app.js, public/style.css. Display all notes as cards with title and first 80 chars of body as preview. New Note button reveals inline form (title input, body textarea, Save button). Save calls POST /api/notes and appends card without reload. Each card has Delete button calling DELETE /api/notes/:id. Clicking title toggles full body expanded inline. Clean CSS with centered max-width layout, card borders/shadows, styled form, nav area with Stats link.
- [x] **1.4**: Install Jest and Supertest as devDependencies. Write API integration tests in tests/api.test.js covering all four CRUD endpoints: GET /api/notes (empty list, populated list), POST /api/notes (valid input returns 201, missing fields returns 400), GET /api/notes/:id (found 200, not-found 404), DELETE /api/notes/:id (found 204, not-found 404). Tests import app from server.js and use supertest. Each test resets data/notes.json to avoid state leakage. Add test script to package.json.
- [B] **1.5**: End-to-end verification through the running app. Start server, create a note via the UI form (POST), verify it appears in the list with correct title and preview. Click title to expand and verify full body displays. Delete the note and verify it disappears from the list. Verify data/notes.json reflects all changes. Restart the server and verify a previously-created note survives the restart (JSON persistence proof).
- [ ] **CLEANUP-debug-artifacts**: Remove debug console.log statements from production code files (persistence.js, routes/notes.js, public/app.js). Replace with proper logging if output is needed. Code health scan found 70 debug statements across production files.
- [x] **VRC-6-gap-1**: Task 1.5 is already in the plan and unblocked — execute it to verify the complete user journey: create note via UI → verify list update → expand → delete → restart server → verify persistence

## Verifications
- [ ] integration/integration_api_crud (integration)
- [ ] integration/integration_persistence_flow (integration)
- [ ] unit/unit_persistence (unit)
- [ ] value/value_notes_ui_create (value)
- [ ] value/value_notes_ui_delete (value)
- [ ] value/value_notes_ui_display (value)
- [ ] value/value_notes_ui_expand (value)