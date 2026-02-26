# Value Checklist: pagecraft
Generated: 2026-02-26T12:04:55.202881

## VRC Status
- Value Score: 45%
- Verified: 3/6
- Blocked: 0
- Recommendation: CONTINUE
- Summary: Fallback VRC: carried forward from iteration 87 (45%)

## Tasks
- [D] **1.1**: Create 3 template JSON files (saas.json, event.json, portfolio.json) each with 5 sections: hero, features, testimonials, pricing, cta. Each section has type, unique id, and content object per PRD F2 schema. Content must be distinct per template (SaaS = product/feature language, Event = date/speaker/agenda, Portfolio = work/project showcase). No copy-paste filler.
- [x] **1.2**: Build the app shell (index.html) with full builder layout: header bar with app title, template selector panel (for 3 cards), editor workspace area (where sections appear), and a preview panel. Include script tags for app.js and templates.js, link tags for app.css and templates.css. Structure uses semantic HTML with clear region IDs.
- [x] **1.3**: Create app.css with builder UI styles: two-panel grid layout (editor sidebar + preview panel), template card grid with hover states, section block styling in workspace, header/toolbar bar, and responsive layout that works at 1200px+ desktop width. Cards should look clickable with shadows and transitions.
- [D] **1.4**: Create templates.css with styles for all 5 section types as they render in the preview: hero (large headline + CTA button), features (3-card grid), testimonials (3-quote layout), pricing (3-tier table), CTA (centered banner). Use --accent-color CSS custom property for buttons, headings, and borders. Sections must stack on narrow widths.
- [D] **1.5**: Implement app.js with state management foundation: AppState object tracking currentTemplate (name), sections (array of section objects), accentColor (hex string), and sectionVisibility (map of id->boolean). Expose loadTemplate(name) that fetches template JSON, populates state, and calls renderWorkspace(). Export state accessors for use by future modules (editor, dragdrop, export).
- [D] **1.6**: Implement templates.js: fetch/parse template JSON via fetch(), render template selection cards (3 cards with template name and a mini HTML preview snippet showing the hero section), and a renderSections(sections) function that generates full section HTML for all 5 types into the workspace and preview panel based on section type and content data.
- [x] **1.7**: Wire the template selection flow end-to-end: on page load show 3 template cards, clicking a card calls loadTemplate() which fetches JSON, populates AppState, renders sections into workspace and preview panel, and hides the selector. Add template switching: if a template is already loaded, show confirm("Switch template? Changes will be lost.") before loading the new one. Update server.js if needed for any missing routes.
- [D] **CLEANUP-debug-artifacts**: Still 43 debug artifacts in production code
- [x] **REFACTOR-public-css-app-css**: Refactor monolithic file: public/css/app.css (611 lines). Previous attempt created split files (app-base.css, app-templates.css, app-editor.css, app-preview.css) but left app.css at full size for test compatibility. Must update index.html to import the split files and reduce or eliminate app.css to meet the <=400 lines target.
- [ ] **SPLIT-FN-public-js-templates-js**: Long functions still present in public/js/templates.js: generateTemplatePreview(56L)
- [ ] **SPLIT-FN-public-js-app-js**: Long functions still present in public/js/app.js: getCombinedCSS(65L)
- [x] **CE-85-11**: Add template-specific CSS classes (e.g., template-saas, template-event, template-portfolio) to the preview container and define distinct visual treatments: different color schemes, hero layout variations (centered vs left-aligned vs split), different feature grid layouts (3-column vs 2-column vs list), different testimonial styles (cards vs inline quotes vs carousel-style).
- [x] **CE-85-12**: Add a mini HTML preview snippet inside each template card showing a scaled-down rendering of the hero section (or a representative visual), using CSS transform: scale() to create a thumbnail effect. Alternatively, render a static preview image or an inline SVG illustration per template.
- [ ] **CE-85-13**: Add a Change Template button in the editor header or sidebar that shows the template selector again (setting template-selector display back to block). This button should trigger the same confirm() dialog to warn about losing changes.
- [ ] **EVAL-1**: Make each template visually distinct: add template-specific CSS classes and define unique visual treatments per template. SaaS needs a different color scheme and layout pattern from Event and Portfolio. Each template should have distinct hero style (e.g., gradient vs solid vs image placeholder), different feature grid layout (3-col vs 2-col vs list), and unique color palettes so users can see meaningful differences when browsing templates.
- [ ] **EVAL-2**: Add visual thumbnail previews to template selection cards. Each card should show a mini rendered preview of what the template looks like (e.g., a scaled-down hero section or representative visual). Use CSS transform: scale() on a small inline-rendered preview, or generate a static visual snapshot per template.
- [ ] **EVAL-3**: Add a Change Template or Back button visible in the editor view that returns the user to the template selection screen. When clicked, show the same confirm dialog (Switch template? Changes will be lost.) if a template is loaded. On confirm, hide the editor container and show the template selector.

## Verifications
- [ ] integration/integration_app_state_management (integration)
- [ ] integration/integration_change_template_button (integration)
- [ ] integration/integration_css_styles_applied (integration)
- [ ] integration/integration_preview_thumbnails (integration)
- [ ] integration/integration_static_assets (integration)
- [ ] integration/integration_template_css_classes (integration)
- [ ] integration/integration_template_loading (integration)
- [ ] unit/unit_css_accent_color_vars (unit)
- [ ] unit/unit_html_structure (unit)
- [ ] unit/unit_server_starts (unit)
- [ ] unit/unit_template_content_distinct (unit)
- [ ] unit/unit_template_css_completeness (unit)
- [ ] unit/unit_template_sections_schema (unit)
- [ ] unit/unit_templates_valid_json (unit)
- [ ] value/value_accent_color_changes.spec (value)
- [ ] value/value_all_section_types_render.spec (value)
- [ ] value/value_change_template_button.spec (value)
- [ ] value/value_complete_workflow.spec (value)
- [ ] value/value_foundation_epic_complete.spec (value)
- [ ] value/value_html_export.spec (value)
- [ ] value/value_template_distinct_content.spec (value)
- [ ] value/value_template_selection_flow.spec (value)
- [ ] value/value_template_thumbnails.spec (value)
- [ ] value/value_template_visual_distinction.spec (value)
- [ ] value/value_viewport_toggle.spec (value)