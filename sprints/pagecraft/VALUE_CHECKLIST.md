# Value Checklist: pagecraft
Generated: 2026-02-26T01:56:18.057257

## VRC Status
- Value Score: 100%
- Verified: 8/8
- Blocked: 0
- Recommendation: SHIP_READY
- Summary: Fallback VRC: carried forward from iteration 6 (100%)

## Tasks
- [x] **1.1**: Create 3 template JSON files (saas.json, event.json, portfolio.json) each with 5 sections: hero, features, testimonials, pricing, cta. Each section has type, unique id, and content object per PRD F2 schema. Content must be distinct per template (SaaS = product/feature language, Event = date/speaker/agenda, Portfolio = work/project showcase). No copy-paste filler.
- [x] **1.2**: Build the app shell (index.html) with full builder layout: header bar with app title, template selector panel (for 3 cards), editor workspace area (where sections appear), and a preview panel. Include script tags for app.js and templates.js, link tags for app.css and templates.css. Structure uses semantic HTML with clear region IDs.
- [x] **1.3**: Create app.css with builder UI styles: two-panel grid layout (editor sidebar + preview panel), template card grid with hover states, section block styling in workspace, header/toolbar bar, and responsive layout that works at 1200px+ desktop width. Cards should look clickable with shadows and transitions.
- [x] **1.4**: Create templates.css with styles for all 5 section types as they render in the preview: hero (large headline + CTA button), features (3-card grid), testimonials (3-quote layout), pricing (3-tier table), CTA (centered banner). Use --accent-color CSS custom property for buttons, headings, and borders. Sections must stack on narrow widths.
- [x] **1.5**: Implement app.js with state management foundation: AppState object tracking currentTemplate (name), sections (array of section objects), accentColor (hex string), and sectionVisibility (map of id->boolean). Expose loadTemplate(name) that fetches template JSON, populates state, and calls renderWorkspace(). Export state accessors for use by future modules (editor, dragdrop, export).
- [x] **1.6**: Implement templates.js: fetch/parse template JSON via fetch(), render template selection cards (3 cards with template name and a mini HTML preview snippet showing the hero section), and a renderSections(sections) function that generates full section HTML for all 5 types into the workspace and preview panel based on section type and content data.
- [x] **1.7**: Wire the template selection flow end-to-end: on page load show 3 template cards, clicking a card calls loadTemplate() which fetches JSON, populates AppState, renders sections into workspace and preview panel, and hides the selector. Add template switching: if a template is already loaded, show confirm("Switch template? Changes will be lost.") before loading the new one. Update server.js if needed for any missing routes.
- [D] **CLEANUP-debug-artifacts**: Still 43 debug artifacts in production code
- [x] **REFACTOR-public-css-app-css**: Refactor monolithic file: public/css/app.css (611 lines). Previous attempt created split files (app-base.css, app-templates.css, app-editor.css, app-preview.css) but left app.css at full size for test compatibility. Must update index.html to import the split files and reduce or eliminate app.css to meet the <=400 lines target.
- [x] **SPLIT-FN-public-js-templates-js**: Split long functions in public/js/templates.js: renderTemplateCards(67L). Extract helper functions to keep each function under 50 lines.
- [ ] **SPLIT-FN-public-js-app-js**: Split long functions in public/js/app.js: renderSectionContent(67L). Extract helper functions to keep each function under 50 lines.

## Verifications
- [ ] integration/integration_app_state_management (integration)
- [ ] integration/integration_css_styles_applied (integration)
- [ ] integration/integration_static_assets (integration)
- [ ] integration/integration_template_loading (integration)
- [ ] unit/unit_html_structure (unit)
- [ ] unit/unit_server_starts (unit)
- [ ] unit/unit_template_content_distinct (unit)
- [ ] unit/unit_template_sections_schema (unit)
- [ ] unit/unit_templates_valid_json (unit)
- [ ] value/value_accent_color_changes.spec (value)
- [ ] value/value_all_section_types_render.spec (value)
- [ ] value/value_complete_workflow.spec (value)
- [ ] value/value_html_export.spec (value)
- [ ] value/value_template_distinct_content.spec (value)
- [ ] value/value_template_selection_flow.spec (value)
- [ ] value/value_viewport_toggle.spec (value)