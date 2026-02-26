# PageCraft Verification Scripts

This directory contains executable verification scripts that prove the Foundation + Template Selection epic delivers its promised value.

## Script Categories

### Unit Verifications (Fast, < 10s)
These verify individual components work correctly in isolation:

- **unit_server_starts.sh** - Express server starts on configurable PORT
- **unit_templates_valid_json.sh** - All 3 template JSON files are valid and parseable
- **unit_template_sections_schema.sh** - Each template has exactly 5 sections (hero, features, testimonials, pricing, cta) with correct schema
- **unit_template_content_distinct.sh** - SaaS/Event/Portfolio templates have meaningfully different content (< 30% similarity)
- **unit_html_structure.sh** - index.html has all required regions (template-selector, workspace, preview-panel) and script/CSS tags

### Integration Verifications (Medium, < 60s)
These verify components work together correctly:

- **integration_template_loading.sh** - Templates load via HTTP and are accessible
- **integration_static_assets.sh** - All static assets (CSS, JS) are served correctly by Express
- **integration_app_state_management.sh** - AppState object initializes and manages state correctly
- **integration_css_styles_applied.sh** - CSS files contain required styles for all section types

### Value Delivery Verifications (Playwright Browser Tests)
These simulate real user workflows and verify the user gets the promised outcome:

- **value_template_selection_flow.spec.js** - User sees 3 template cards and can select one to load into editor
- **value_all_section_types_render.spec.js** - All 5 section types render with correct content in preview
- **value_template_distinct_content.spec.js** - Each template loads with distinct, template-specific content (SaaS/Event/Portfolio)
- **value_viewport_toggle.spec.js** - User can toggle between desktop and mobile preview
- **value_accent_color_changes.spec.js** - User can change accent color and see it applied globally
- **value_html_export.spec.js** - User can export standalone HTML file with inlined CSS
- **value_complete_workflow.spec.js** - Complete Vision workflow: pick template, customize, preview mobile, export

## Running Verifications

### Run Individual Scripts
```bash
# Unit tests (shell scripts)
bash .loop/verifications/unit_server_starts.sh

# Integration tests (shell scripts)
bash .loop/verifications/integration_template_loading.sh

# Playwright tests (individual)
npx playwright test .loop/verifications/value_template_selection_flow.spec.js
```

### Run All Playwright Tests
```bash
npm test
# or
npx playwright test
```

### Run with Isolated Ports (for parallel execution)
```bash
PORT=3456 bash .loop/verifications/unit_server_starts.sh
```

## Test Isolation

All verification scripts support parallel execution:
- **PORT** environment variable - Each script uses `${PORT:-3000}` for server isolation
- **TEST_DATA_DIR** environment variable - For data isolation (if needed)

Scripts that start servers:
1. Use the assigned PORT from the environment
2. Clean up server processes on exit (trap handlers)
3. Wait for server readiness before testing

## What These Tests Prove

These scripts verify that Epic 1 (Foundation + Template Selection) delivers:

1. ✓ Express server serves the app on configurable PORT
2. ✓ 3 template JSON files with distinct, template-specific content
3. ✓ All 5 section types (hero, features, testimonials, pricing, cta) defined
4. ✓ Builder UI layout with template selector, workspace, and preview panel
5. ✓ CSS styling for builder UI and template sections
6. ✓ AppState management foundation
7. ✓ Template selection flow (pick template → load into editor)
8. ✓ Preview rendering for all section types
9. ✓ Viewport toggle (desktop/mobile)
10. ✓ Accent color customization
11. ✓ HTML export with inlined CSS

## Playwright Configuration

The `playwright.config.js` in the project root:
- Automatically starts the server before tests
- Uses PORT environment variable for isolation
- Runs tests in headless mode
- Takes screenshots on failure

## Expected Results

All tests should PASS when the Foundation + Template Selection epic is complete.

Tests may FAIL if:
- Features from later epics (drag-and-drop, inline editing) are not yet implemented - this is EXPECTED
- Server fails to start
- Template JSON files are invalid or missing
- Required HTML elements are missing
- CSS files don't contain required styles
