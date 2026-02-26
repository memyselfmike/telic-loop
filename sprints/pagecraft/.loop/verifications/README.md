# PageCraft Verification Scripts

This directory contains executable verification scripts that prove the sprint delivers its promised value. All scripts use Playwright and run in parallel.

## Test Organization

### Unit Tests (Fast, <10s each)
Run after every task to catch regressions early:

- **unit_server_starts.js** - Server starts on PORT, serves static files (HTML/CSS/JS)
- **unit_template_json_valid.js** - All 3 template JSONs are valid, have 5 sections each, distinct content
- **unit_ui_layout.js** - App shell has correct layout regions (header, selector, workspace, preview)

### Integration Tests (Medium, <60s each)
Run after related tasks complete:

- **integration_template_selection_flow.js** - Template cards display, clicking loads template, switching works
- **integration_state_management.js** - App state initializes, populates on template load, manages visibility/color
- **integration_section_rendering.js** - All 5 section types render with correct content from JSON

### Value Delivery Tests (Variable time)
Run before exit gate to prove user gets promised outcomes:

- **value_template_visual_preview.js** - Template cards show visual previews (not just text), distinct styling
- **value_template_distinct_layouts.js** - Each template produces visually distinct layout (critical epic criterion)
- **value_user_picks_template.js** - Complete user journey: open app → see 3 cards → pick one → editor loads

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

### Vision Promises Verified:
✅ "User opens PageCraft in a browser and sees 3 template cards (SaaS Product, Event/Webinar, Portfolio Showcase) with visual previews"
✅ "can click one to load it into the editor workspace"
✅ Each template produces "visually distinct landing page layout" (not just different text)

### PRD Requirements Verified:
✅ F1: Template Selection - 3 templates with thumbnails, clicking loads template
✅ F2: Section Management - 5 section types with editable content structure
✅ Architecture - Express server, static file serving, modular JS/CSS
✅ Acceptance Criteria #1: "All 3 templates load and display correctly with distinct layouts"

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

1. **value_template_distinct_layouts.js** - Epic requirement: "Each template produces a visually distinct landing page layout (not just different text on the same layout)"
2. **value_user_picks_template.js** - Vision promise: User can pick template and load it into editor
3. **value_template_visual_preview.js** - Vision promise: Cards show "visual previews" not just text

If these pass, the epic delivers real value. If they fail, the epic is incomplete.
