# Implementation Plan (rendered from state)

Generated: 2026-02-16T15:04:37.035220


## Core

- [ ] **1.1**: Build the complete index.html todo application with all core features: task input with Enter/button submission and empty-input guard, task list display with checkbox toggle and strikethrough styling, delete button per task, three-state filtering (All/Active/Completed) with active filter highlighting and live item count, and localStorage persistence that saves on every mutation and restores on page load. The file must be a single self-contained HTML file with embedded CSS and JS — no external dependencies, no CDN links, no frameworks. Task data model: {id, text, completed, createdAt}. Newest tasks appear at bottom. Delete button visible on hover (desktop) and always visible (mobile). Responsive design: centered container with max-width 600px on desktop (1024px+), full-width layout on mobile (375px), touch-friendly tap targets of at least 44px height on all interactive elements (checkboxes, buttons, filters), readable font sizes (>=14px body text), and no horizontal scrolling at any viewport width.
  - Value: Delivers the entire user-facing product: a developer can open this single file in any browser and immediately manage daily tasks with zero setup — the core promise of the Vision.
  - Acceptance: 1) Opening index.html shows a text input with placeholder and an empty task list area. 2) Typing text + Enter adds the task to the visible list; empty input is rejected. 3) Clicking checkbox toggles strikethrough and completed state. 4) Delete button removes task from DOM and storage. 5) Filter buttons switch views correctly; item count reflects active tasks. 6) After page refresh, all tasks are preserved exactly. 7) At 375px viewport width, no element overflows horizontally; all interactive elements have minimum 44px tap targets; delete button is always visible (not hover-gated). 8) At 1024px viewport, task list is centered with max-width ~600px. 9) All of the above works with no console errors in a modern browser.


## Verification

- [ ] **2.1**: Create the Playwright test suite (pytest-playwright) that verifies all 7 PRD acceptance criteria against the built index.html. Tests must: (1) serve the file via a local Python http.server fixture (not file:// protocol, to ensure consistent localStorage behavior), (2) use a conftest.py with the server fixture and base_url configuration, and (3) include these test cases: AC1 — page loads with input field and empty list; AC2 — add task via Enter key; AC3 — checkbox toggles strikethrough styling; AC4 — delete button removes task; AC5 — filter buttons show correct subsets (3 tasks: 2 active, 1 completed); AC6 — tasks survive page refresh (localStorage persistence); AC7 — 375px viewport has no horizontal overflow and 44px minimum tap targets. Each test must be independent and not rely on state from other tests.
  - Value: Provides automated proof that the app delivers on every promised behavior — this is how we KNOW the user gets the value, not just hope they do.
  - Acceptance: 1) Running pytest sprints/todo-app/tests/ executes all 7+ test cases. 2) All tests pass against the built index.html. 3) Tests use a local HTTP server fixture, not file:// protocol. 4) Each test is independent (can run in isolation). 5) Test names clearly map to acceptance criteria (e.g., test_ac1_initial_page_load, test_ac6_persistence_after_refresh).
  - Deps: 1.1

- [ ] **2.2**: Run the full Playwright test suite and fix any failures found in either the test code or index.html. This task covers the feedback loop: execute tests, analyze failures, fix the root cause (whether in the app or the tests), and re-run until all tests pass green. Common issues to watch for: selector mismatches between test expectations and actual DOM structure, timing issues requiring proper Playwright waits (use expect/locator auto-waiting, not sleep), and localStorage serialization edge cases.
  - Value: Closes the verification loop — ensures the automated proofs actually pass, confirming the app delivers every promised behavior to the user.
  - Acceptance: 1) pytest sprints/todo-app/tests/ runs to completion with 0 failures. 2) All 7 acceptance criteria have at least one passing test. 3) No tests are skipped or xfail-marked. 4) Tests run reliably (no flaky failures on re-run).
  - Deps: 1.1, 2.1
