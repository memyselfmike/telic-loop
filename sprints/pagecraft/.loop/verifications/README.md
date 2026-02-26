# PageCraft Verification Scripts

This directory contains executable verification scripts that prove the sprint delivers its promised value. All scripts use Playwright and run in parallel.

## Test Organization

### Unit Tests (Fast, <10s each)
Run after every task to catch regressions early:

**Epic 1 - Foundation + Template Selection:**
- **unit_server_starts.js** - Server starts on PORT, serves static files (HTML/CSS/JS)
- **unit_template_json_valid.js** - All 3 template JSONs are valid, have 5 sections each, distinct content
- **unit_ui_layout.js** - App shell has correct layout regions (header, selector, workspace, preview)

**Epic 2 - Interactive Editor:**
- **unit_dragdrop_module.js** - Drag-drop module initializes, attaches handlers, draggable sections
- **unit_visibility_toggle.js** - Eye icon toggle buttons render, change state, show visual feedback
- **unit_inline_editing.js** - Editable elements have data-field, click makes contenteditable
- **unit_accent_color.js** - Accent color picker present, updates CSS custom property

### Integration Tests (Medium, <60s each)
Run after related tasks complete:

**Epic 1 - Foundation + Template Selection:**
- **integration_template_selection_flow.js** - Template cards display, clicking loads template, switching works
- **integration_state_management.js** - App state initializes, populates on template load, manages visibility/color
- **integration_section_rendering.js** - All 5 section types render with correct content from JSON

**Epic 2 - Interactive Editor:**
- **integration_dragdrop_reorder.js** - Dragging section reorders state, preview reflects new order, persists
- **integration_visibility_toggle.js** - Hidden sections omitted from DOM, toggle bidirectional, persists through drag
- **integration_inline_editing.js** - Editing updates state, persists through re-renders, nested fields work
- **integration_accent_color_coverage.js** - Accent applies to buttons, headings, borders, CTA, hero gradient

### Value Delivery Tests (Variable time)
Run before exit gate to prove user gets promised outcomes:

**Epic 1 - Foundation + Template Selection:**
- **value_template_visual_preview.js** - Template cards show visual previews (not just text), distinct styling
- **value_template_distinct_layouts.js** - Each template produces visually distinct layout (critical epic criterion)
- **value_user_picks_template.js** - Complete user journey: open app → see 3 cards → pick one → editor loads

**Epic 2 - Interactive Editor:**
- **value_combined_interactions.js** - Drag+edit+toggle+color work together, no conflicts, state persists
- **value_vision_workflow.js** - Complete Vision scenario: pick SaaS → drag CTA → edit headline → set color → preview mobile

## What These Tests Verify

### Epic 1 Deliverables Covered:
✅ Express server serving static files on configurable PORT
✅ App shell (index.html) with builder UI layout
✅ App CSS with clean builder UI styles
✅ 3 template JSON definitions with distinct content
✅ Template selection screen with 3 visual cards
✅ templates.js module loading and rendering sections
✅ Template section CSS for all 5 section types
✅ app.js state management foundation

### Epic 2 Deliverables Covered:
✅ dragdrop.js module implementing HTML5 drag-and-drop reordering
✅ Section show/hide toggle (eye icon) on each section
✅ editor.js module implementing contenteditable inline text editing
✅ Accent color picker that applies globally
✅ Updated app.js state tracking section order, visibility, text content, accent color

### Vision Promises Verified:
✅ "User opens PageCraft in a browser and sees 3 template cards with visual previews, can click one to load it into the editor workspace"
✅ "User drags sections (hero, features, testimonials, pricing, CTA) to reorder them in the workspace, and the preview immediately reflects the new order"
✅ "User clicks on any text field and edits it inline — changes appear instantly in the preview without saving or reloading"
✅ "User picks an accent color and all buttons, headings, and borders across the entire page update to that color in real-time"
✅ "User hides/shows individual sections using eye-icon toggles, and hidden sections disappear from the preview entirely"
✅ Complete workflow: "picks SaaS Product template, drags CTA above testimonials, changes headline to custom text, selects blue accent color"

### PRD Requirements Verified:
✅ F1: Template Selection - 3 templates with thumbnails, clicking loads template
✅ F2: Section Management - 5 section types, drag-and-drop reordering, hide/show toggle
✅ F3: Inline Editing - contenteditable text fields, accent color picker, changes apply immediately
✅ Architecture - Express server, static file serving, modular JS/CSS (app.js, editor.js, dragdrop.js)
✅ Acceptance Criteria #1: "All 3 templates load and display correctly with distinct layouts"
✅ Acceptance Criteria #2: "Drag-and-drop reorders sections and the new order persists in preview"
✅ Acceptance Criteria #3: "Inline text editing works on all editable fields"
✅ Acceptance Criteria #4: "Accent color changes apply globally to buttons and headings"

## Running Tests

```bash
# Run all tests
npm test

# Run specific category
npm test -- --grep "^unit_"
npm test -- --grep "^integration_"
npm test -- --grep "^value_"

# Run single test file
npm test -- unit_server_starts.js
```

## Test Isolation

Each test runs in parallel with unique PORT assignment. Tests use:
- `PORT` env variable for server port (falls back to 3000)
- `TEST_DATA_DIR` for isolated test data (if needed)
- Playwright's `webServer` config handles server lifecycle

## Expected Behavior

- **Unit tests** should all pass if foundation is built correctly
- **Integration tests** may fail if features are not yet implemented (expected)
- **Value tests** prove the user experience - these are the ultimate acceptance criteria

## Critical Tests

These tests verify the MOST IMPORTANT epic completion criteria:

**Epic 1 (Foundation + Template Selection):**
1. **value_template_distinct_layouts.js** - Epic requirement: "Each template produces a visually distinct landing page layout (not just different text on the same layout)"
2. **value_user_picks_template.js** - Vision promise: User can pick template and load it into editor
3. **value_template_visual_preview.js** - Vision promise: Cards show "visual previews" not just text

**Epic 2 (Interactive Editor):**
1. **value_combined_interactions.js** - All 4 features (drag, edit, toggle, color) work together without conflicts
2. **value_vision_workflow.js** - Complete Vision scenario: user customizes landing page end-to-end
3. **integration_dragdrop_reorder.js** - Drag-drop reordering with immediate preview update (core interaction)
4. **integration_inline_editing.js** - Inline text editing with state persistence (core interaction)

If these pass, the epic delivers real value. If they fail, the epic is incomplete.
