# Implementation Plan (rendered from state)

Generated: 2026-02-26T19:51:57.856575


## Foundation

- [ ] **1.1**: Create 3 template JSON files (saas.json, event.json, portfolio.json) each with 5 sections: hero, features, testimonials, pricing, cta. Each section has type, unique id, and content object per PRD F2 schema. Content must be distinct per template (SaaS = product/feature language, Event = date/speaker/agenda, Portfolio = work/project showcase). No copy-paste filler.
  - Value: Provides the data foundation for the entire template system. Without structured, distinct template data, no template card can show a meaningful preview and no section can render real content.
  - Acceptance: Each JSON is valid and parseable. Each has exactly 5 sections with types hero/features/testimonials/pricing/cta. Each section has unique id and content matching PRD F2 fields. SaaS/Event/Portfolio have meaningfully different text content.

- [x] **1.2**: Build the app shell (index.html) with full builder layout: header bar with app title, template selector panel (for 3 cards), editor workspace area (where sections appear), and a preview panel. Include script tags for app.js and templates.js, link tags for app.css and templates.css. Structure uses semantic HTML with clear region IDs.
  - Value: Gives users the visual workspace where all interactions happen. The layout regions (selector, workspace, preview) are the containers that all subsequent features render into.
  - Acceptance: index.html loads without errors. Has #template-selector area, #workspace area, #preview-panel area. All JS/CSS files are referenced via script/link tags. Layout has identifiable regions visible in the DOM.

- [x] **1.3**: Create app.css with builder UI styles: two-panel grid layout (editor sidebar + preview panel), template card grid with hover states, section block styling in workspace, header/toolbar bar, and responsive layout that works at 1200px+ desktop width. Cards should look clickable with shadows and transitions.
  - Value: Makes the builder visually usable. Without styling, the workspace is raw HTML where users cannot distinguish regions or interact confidently with template cards.
  - Acceptance: Builder shows clear two-panel layout (editor left, preview right). Template cards are styled as clickable cards with visual hover feedback. Section blocks are visually separated. No overlapping or broken layout at 1200px+ width.
  - Deps: 1.2

- [ ] **1.4**: Create templates.css with styles for all 5 section types as they render in the preview: hero (large headline + CTA button), features (3-card grid), testimonials (3-quote layout), pricing (3-tier table), CTA (centered banner). Use --accent-color CSS custom property for buttons, headings, and borders. Sections must stack on narrow widths.
  - Value: Ensures the landing page sections look professional in the preview panel. Visual quality of rendered sections is what convinces users their page is ready to publish.
  - Acceptance: Each section type has distinct visual styling. Hero has prominent headline. Features/testimonials/pricing display as 3-column grids. CTA is centered. --accent-color controls button backgrounds and heading colors. Sections stack vertically below 600px.
  - Deps: 1.2


## Core

- [ ] **1.5**: Implement app.js with state management foundation: AppState object tracking currentTemplate (name), sections (array of section objects), accentColor (hex string), and sectionVisibility (map of id->boolean). Expose loadTemplate(name) that fetches template JSON, populates state, and calls renderWorkspace(). Export state accessors for use by future modules (editor, dragdrop, export).
  - Value: Provides the single source of truth for the entire app. All features (editing, reorder, export) read and write through this state model, so getting it right prevents epic 2/3 refactors.
  - Acceptance: AppState initializes with empty/default values. loadTemplate("saas") fetches saas.json and populates state.sections with 5 section objects. State is accessible from the browser console (window.appState or equivalent). Re-calling loadTemplate replaces state cleanly.
  - Deps: 1.1, 1.2

- [ ] **1.6**: Implement templates.js: fetch/parse template JSON via fetch(), render template selection cards (3 cards with template name and a mini HTML preview snippet showing the hero section), and a renderSections(sections) function that generates full section HTML for all 5 types into the workspace and preview panel based on section type and content data.
  - Value: Enables users to see template cards to choose from and see rendered section content after selection. This is the rendering engine that transforms JSON data into visible HTML.
  - Acceptance: getTemplate(name) returns parsed JSON. Template cards render with name and a visual preview snippet. renderSections() produces correct HTML for hero/features/testimonials/pricing/cta types. Each section type shows all its editable fields from the content object.
  - Deps: 1.1, 1.2, 1.3, 1.4

- [ ] **2.1**: Create dragdrop.js implementing HTML5 drag-and-drop reordering on section blocks in the workspace sidebar. Handle dragstart/dragover/dragend/drop events on .section-block elements. On drop, reorder AppState.sections array to match the new visual order, then call renderSections() and renderPreview() so the preview immediately reflects the new section order. Add drag placeholder/indicator for drop position.
  - Value: Enables the core drag-and-drop interaction: user drags sections to reorder them and sees the preview update instantly, which is the primary editing interaction promised by the Vision.
  - Acceptance: 1. Dragging a section block shows visual feedback (opacity/placeholder). 2. Dropping a section in a new position reorders AppState.sections. 3. Preview re-renders immediately showing sections in the new order. 4. Section order persists across subsequent edits (not reset on re-render).

- [ ] **2.2**: Add section visibility toggle to each section block in the workspace sidebar. Add an eye icon button to each .section-block in renderSections(). Clicking the eye toggles a 'visible' property on the section in AppState.sections (default true). When visible is false, the eye icon shows as crossed-out and renderPreview() skips that section entirely (omits from DOM, not display:none).
  - Value: Enables users to hide/show individual sections so they can customize which sections appear on their landing page without deleting content they might want back later.
  - Acceptance: 1. Each section block shows an eye icon button. 2. Clicking eye toggles section visibility in AppState. 3. Hidden sections are omitted from preview DOM entirely. 4. Eye icon visually indicates hidden state (crossed-out/dimmed). 5. Toggling back to visible immediately shows section in preview.

- [ ] **2.3**: Create editor.js implementing contenteditable inline text editing on all editable fields in the preview panel. Add data-field and data-section-id attributes to rendered text elements (h1, h2, h3, p, button, blockquote, cite, li) in renderSectionContent(). On click, make the element contenteditable. On blur, read the new text and update the corresponding field in AppState.sections content object.
  - Value: Enables click-to-edit on any text field in the preview so users can customize all landing page content inline without forms or modals - the core inline editing experience promised by the Vision.
  - Acceptance: 1. Clicking any editable text element in preview makes it contenteditable. 2. Editing text and clicking away updates AppState.sections content. 3. Changes persist when preview re-renders. 4. All PRD F2 fields are editable: headlines, descriptions, button text, quotes, author names, pricing details.

- [ ] **2.4**: Enhance accent color picker to apply globally and verify full coverage. Ensure the color picker input change updates AppState.accentColor AND re-renders preview. Verify --accent-color CSS variable propagates to all buttons, headings (h2, h3), borders (pricing cards), cite elements, hero gradients, and CTA backgrounds across all 3 template types. Add a label next to the color picker for clarity.
  - Value: Ensures the accent color picker delivers on the Vision promise: user picks a color and ALL buttons, headings, and borders across the entire page update to that color in real-time.
  - Acceptance: 1. Changing accent color updates --accent-color CSS variable immediately. 2. All h2/h3 headings use accent color. 3. All buttons use accent color (background or text). 4. Pricing card borders use accent color. 5. CTA section background uses accent color. Hero gradient incorporates accent color.


## Integration

- [x] **1.7**: Wire the template selection flow end-to-end: on page load show 3 template cards, clicking a card calls loadTemplate() which fetches JSON, populates AppState, renders sections into workspace and preview panel, and hides the selector. Add template switching: if a template is already loaded, show confirm("Switch template? Changes will be lost.") before loading the new one. Update server.js if needed for any missing routes.
  - Value: Delivers the complete epic_1 user journey: open app, see cards, pick one, see sections. Without this wiring, individual modules exist but the user cannot complete the template selection flow.
  - Acceptance: On load: 3 template cards visible. Click SaaS card: sections render in workspace+preview, selector hides. Click a back/change button: selector reappears with confirm dialog if changes exist. All 3 templates load distinct content. No console errors during the full flow.
  - Deps: 1.5, 1.6

- [ ] **2.5**: Wire dragdrop.js and editor.js into the app and verify all interactive features work together end-to-end. Add script tags to index.html. Ensure drag reorder + inline edit + visibility toggle + accent color all work in combination without conflicts (e.g., editing text inside a draggable section, re-rendering after drag preserves edited text, hidden sections stay hidden after color change).
  - Value: Ensures all epic_2 interactive features compose correctly - the user can drag, edit, toggle, and recolor in any order without losing state, delivering the seamless editing experience promised by the Vision.
  - Acceptance: 1. User can drag-reorder then inline-edit without losing order. 2. Inline edits persist through drag-reorder operations. 3. Hidden sections remain hidden after accent color change. 4. All 4 features (drag, edit, toggle, color) work on all 3 templates. 5. No console errors during combined interactions.
  - Deps: 2.1, 2.2, 2.3, 2.4


## Unphased

- [x] **CE-85-11**: Add template-specific CSS classes (e.g., template-saas, template-event, template-portfolio) to the preview container and define distinct visual treatments: different color schemes, hero layout variations (centered vs left-aligned vs split), different feature grid layouts (3-column vs 2-column vs list), different testimonial styles (cards vs inline quotes vs carousel-style).
  - Value: A user browsing templates sees no visual difference between SaaS, Event, and Portfolio layouts. The entire point of having multiple templates is undermined — there is effectively one template with three text variations. The user cannot make a meaningful choice.
  - Acceptance: Fix: All 3 templates produce visually identical layouts — same blue gradient hero, same 3-card feature grid, same testimonial cards, same pricing grid, same CTA banner. Only the text content differs. The epic completion criteria explicitly states: Each template produces a visually distinct landing page layout (not just different text on the same layout).

- [x] **CE-85-12**: Add a mini HTML preview snippet inside each template card showing a scaled-down rendering of the hero section (or a representative visual), using CSS transform: scale() to create a thumbnail effect. Alternatively, render a static preview image or an inline SVG illustration per template.
  - Value: User cannot visually compare templates before choosing. The cards look like a plain text list rather than the visual preview experience promised. Since all templates produce identical layouts (see critical finding), the text-only cards compound the problem — user has no way to know what they are choosing.
  - Acceptance: Fix: Template selection cards show only text (template name + one-line description) with no visual preview or thumbnail. The Vision promises templates displayed as visual cards with live previews, and the epic deliverables specify template selection screen with 3 visual cards showing template name and thumbnail preview.

- [x] **CE-85-13**: Add a Change Template button in the editor header or sidebar that shows the template selector again (setting template-selector display back to block). This button should trigger the same confirm() dialog to warn about losing changes.
  - Value: User who picks the wrong template or wants to try a different one must manually reload the browser — a confusing and non-obvious action. This violates the User control and freedom usability heuristic. The template switching confirm dialog exists in the code but is unreachable because the template cards are hidden.
  - Acceptance: Fix: No way to return to template selector from the editor. Once a user clicks a template, the selector is hidden (display:none) and there is no Back button, Change Template link, or any navigation element to return to the template selection screen. The only way back is to reload the page.

- [ ] **CLEANUP-debug-artifacts**: Still 43 debug artifacts in production code
  - Value: Remove debug artifacts before shipping
  - Acceptance: Zero console.log in non-test source files. console.error statements for genuine error handling may remain. console.warn for missing dependencies removed (should be resolved by feature completion). Server startup log in server.js is acceptable (standard practice). No .log, .bak, .tmp, or .orig files in project.
  - Deps: 1.7

- [x] **REFACTOR-public-css-app-css**: Refactor monolithic file: public/css/app.css (611 lines). Previous attempt created split files (app-base.css, app-templates.css, app-editor.css, app-preview.css) but left app.css at full size for test compatibility. Must update index.html to import the split files and reduce or eliminate app.css to meet the <=400 lines target.
  - Value: Reduce monolithic file risk — public/css/app.css is 548 lines, making it hard to maintain and prone to merge conflicts
  - Acceptance: File public/css/app.css is split into multiple files, each <=400 lines. All existing tests still pass. No functionality is lost.

- [x] **SPLIT-FN-public-js-app-js**: Long functions still present in public/js/app.js: getCombinedCSS(65L)
  - Value: Improve readability and testability of public/js/app.js
  - Acceptance: No function in public/js/app.js exceeds 50 lines. All existing tests still pass.

- [x] **SPLIT-FN-public-js-templates-js**: Long functions still present in public/js/templates.js: generateTemplatePreview(56L)
  - Value: Improve readability and testability of public/js/templates.js
  - Acceptance: No function in public/js/templates.js exceeds 50 lines. All existing tests still pass.
