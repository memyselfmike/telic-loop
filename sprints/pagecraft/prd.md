# PageCraft — Product Requirements Document

## Overview

A single-page browser application for creating landing pages via drag-and-drop. Built with vanilla HTML/CSS/JS (no frameworks). Served by a lightweight Node.js Express server.

## Architecture

```
pagecraft/
  server.js          # Express server (serves static + export API)
  public/
    index.html        # Main app shell
    css/
      app.css         # App styles (builder UI)
      templates.css   # Template section styles
    js/
      app.js          # App initialization + state management
      editor.js       # Inline editing (contenteditable)
      dragdrop.js     # Drag-and-drop reordering
      templates.js    # Template definitions (3 templates, 5 section types)
      preview.js      # Desktop/mobile preview toggle
      export.js       # HTML export (inline all CSS, produce standalone file)
    templates/
      saas.json       # SaaS product template definition
      event.json      # Event/webinar template definition
      portfolio.json  # Portfolio showcase template definition
```

## Functional Requirements

### F1: Template Selection

- Display 3 template cards on initial load: SaaS Product, Event/Webinar, Portfolio Showcase
- Each card shows a thumbnail preview and template name
- Clicking a card loads that template's sections into the editor workspace
- User can switch templates (warns about losing changes)

### F2: Section Management

Five section types, each with editable content:

| Section | Editable Fields |
|---------|----------------|
| **Hero** | Headline, subheadline, CTA button text |
| **Features** | 3 feature cards (icon placeholder, title, description) |
| **Testimonials** | 3 testimonial cards (quote, author name) |
| **Pricing** | 3 pricing tiers (name, price, features list, CTA) |
| **CTA** | Headline, description, button text, button URL |

- Each section is a draggable block in the workspace
- Sections can be reordered via drag-and-drop
- Sections can be hidden/shown via a toggle (eye icon)

### F3: Inline Editing

- All text fields are `contenteditable` — click to edit, click away to save
- Accent color picker (single color applies to buttons, headings, borders)
- Changes apply immediately to the preview — no save button

### F4: Preview

- Preview panel shows the landing page as it will look when exported
- Toggle between desktop (1200px) and mobile (375px) viewport widths
- Preview updates live as edits are made (no reload)

### F5: HTML Export

- "Export" button generates a standalone HTML file
- All CSS is inlined (no external dependencies)
- Exported HTML is a single file that works offline
- Browser downloads the file as `landing-page.html`
- The exported page must visually match the preview

## Non-Functional Requirements

- No build step — vanilla JS, no bundlers
- Server: Express on `PORT` env var (default 3000)
- All state lives in the browser (no database)
- Works in Chrome and Firefox (modern browsers only)
- Responsive builder UI (but mobile editing is not required)

## Acceptance Criteria

1. All 3 templates load and display correctly with distinct layouts
2. Drag-and-drop reorders sections and the new order persists in preview
3. Inline text editing works on all editable fields
4. Accent color changes apply globally to buttons and headings
5. Desktop/mobile preview toggle shows correct viewport widths
6. Exported HTML file is self-contained and renders identically to preview
7. Server starts on configurable PORT and serves the app
