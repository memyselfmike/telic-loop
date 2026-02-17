# PRD: Personal Kanban Board

## 1. Deliverable

A single HTML file at `sprints/kanban/index.html` containing all HTML, CSS, and JavaScript inline. No external dependencies. Under 30KB total file size.

## 2. Board Structure

### 2.1 Default Columns
The board has three columns: **To Do**, **In Progress**, **Done**. Columns are displayed side-by-side horizontally on screens >= 768px wide.

### 2.2 Column Layout
Each column has:
- A header with the column name and a card count badge (e.g., "To Do (3)")
- An "Add card" button (+ icon) at the top of the card list
- A scrollable card list area (vertical scroll within the column when cards overflow)

### 2.3 Column Sizing
Columns share available width equally using CSS flexbox or grid. Minimum column width: 280px. Maximum column width: 400px. The board itself is horizontally scrollable if viewport is too narrow for all columns.

## 3. Cards

### 3.1 Card Display
Each card shows:
- **Title** (required, max 100 characters) — bold, full text visible
- **Description preview** (optional) — first 2 lines with ellipsis overflow, muted text color
- **Priority indicator** — colored left border: low (blue), medium (yellow), high (orange), urgent (red)
- **Labels** — 0 or more colored chips below the description (each label has auto-assigned color from a palette)
- **Created date** — small muted timestamp at the bottom

### 3.2 Card Creation
Clicking the "+" button on a column opens an inline form at the top of that column's card list:
- Title input (auto-focused, required)
- Pressing **Enter** creates the card with just the title (description, priority, labels use defaults)
- Pressing **Escape** cancels creation
- Default priority: medium. Default labels: none.
- New cards appear at the top of the column

### 3.3 Card Editing
Clicking a card opens a modal overlay with:
- Editable title field
- Editable description textarea (plain text, no markdown)
- Priority selector (dropdown or radio: low/medium/high/urgent)
- Label manager: text input to add new labels, existing labels shown as removable chips
- "Delete" button with confirmation ("Delete this card? This cannot be undone.")
- "Close" button (or click outside modal) saves all changes immediately
- Changes save on every field blur or Enter, not just on close

### 3.4 Card Deletion
Delete button in the edit modal. Requires confirmation dialog before removing. Deleted cards are gone (no trash/archive). Deletion is undoable via Ctrl+Z for one action.

## 4. Drag and Drop

### 4.1 Drag Initiation
Mouse down + move on a card initiates drag. The card becomes semi-transparent (opacity 0.5) at its original position. A visual copy follows the cursor.

### 4.2 Drop Targets
While dragging, valid drop positions are shown with a visual placeholder (a dashed-border empty card shape) that indicates where the card will land. Drop targets include:
- Between any two cards in any column
- At the top or bottom of any column
- Into an empty column

### 4.3 Drop Behavior
Releasing the card over a valid target moves it to that position. The card order and column assignment update immediately. If dropped outside any valid target, the card returns to its original position (no change).

### 4.4 Touch Support
Drag and drop must work on touch devices using touch events (touchstart, touchmove, touchend). Long-press (300ms) initiates drag on touch. Same visual feedback as mouse drag.

### 4.5 Performance
Drag operations must not cause visible layout jank. Cards should move at 60fps during drag. No full re-renders during drag — use CSS transforms for the dragged element.

## 5. Filtering and Search

### 5.1 Search Bar
A text input at the top of the board, full-width, with a search icon and placeholder text "Search cards...". Typing filters cards in real-time (on each keystroke, debounced to 150ms).

### 5.2 Search Matching
Cards match if the search text appears in the title, description, or any label (case-insensitive substring match). Non-matching cards are hidden (display: none). Column structure and headers remain visible. Card count badges update to show filtered count.

### 5.3 Filter by Priority
A row of toggle buttons below the search bar: All, Low, Medium, High, Urgent. Clicking one filters to only cards of that priority. "All" shows all priorities. Active filter is visually highlighted. Priority filter combines with search text (AND logic).

### 5.4 Filter by Label
Clicking a label chip on any card filters the board to show only cards with that label. An active label filter is shown as a removable chip in the filter bar. Label filter combines with search and priority (AND logic).

### 5.5 Clear Filters
A "Clear filters" button appears when any filter is active. Clicking it resets search text, priority filter, and label filter.

## 6. Persistence

### 6.1 Storage
All board state is stored in localStorage under key `kanban_board_state`. State includes:
- All cards with their properties (id, title, description, priority, labels, created date)
- Card ordering within each column
- Column assignments

### 6.2 Save Triggers
State saves to localStorage on every mutation: card create, edit, delete, move, label change, priority change. Saves are synchronous and immediate (no debouncing).

### 6.3 Load
On page load, read from localStorage. If no saved state exists, show an empty board with three columns and no cards. If saved state is corrupted or unparseable, show empty board (don't crash).

### 6.4 Data Format
JSON object with schema:
```json
{
  "columns": [
    {"id": "todo", "name": "To Do", "cardIds": ["card-1", "card-3"]},
    {"id": "in-progress", "name": "In Progress", "cardIds": ["card-2"]},
    {"id": "done", "name": "Done", "cardIds": []}
  ],
  "cards": {
    "card-1": {"id": "card-1", "title": "...", "description": "...", "priority": "medium", "labels": ["bug"], "created": "2026-02-17T10:00:00Z"}
  }
}
```

## 7. Undo

### 7.1 Scope
Undo supports the last single action: card create, card delete, card move, card edit. Only one level of undo (not a full history stack).

### 7.2 Trigger
Ctrl+Z (or Cmd+Z on Mac) triggers undo. An undo notification briefly appears at the bottom of the screen ("Undo: moved card" — auto-dismisses after 3 seconds).

### 7.3 Edge Cases
If no action to undo, Ctrl+Z does nothing. After undo, there is nothing to re-do.

## 8. Keyboard Shortcuts

| Key | Action |
|-----|--------|
| N | Open new card form in the first column (To Do) |
| / | Focus the search input |
| Escape | Close modal, cancel card creation, clear search |
| Ctrl+Z / Cmd+Z | Undo last action |

Shortcuts must not fire when a text input or textarea is focused (except Escape).

## 9. Responsive Design

### 9.1 Desktop (>= 1024px)
Three columns side-by-side, centered on screen with max-width container. Search bar and filters span full board width.

### 9.2 Tablet (768px - 1023px)
Three columns side-by-side but narrower. Touch drag-and-drop enabled.

### 9.3 Mobile (< 768px)
Columns stack vertically. Each column is full-width. Cards can still be dragged within and between columns (vertical drag). The board scrolls vertically to show all columns.

## 10. Visual Design

### 10.1 Theme
Dark theme:
- Background: #0d1117 (board), #161b22 (columns), #21262d (cards)
- Text: #e6edf3 (primary), #8b949e (secondary/muted)
- Accent: #58a6ff (links, active states)
- Card borders: 1px solid #30363d
- Priority colors: low #58a6ff, medium #d29922, high #d18616, urgent #f85149

### 10.2 Typography
System font stack. Card titles: 14px semibold. Descriptions: 13px normal. Labels: 11px.

### 10.3 Animations
- Card drag: CSS transform, 60fps
- Modal open/close: opacity fade (200ms)
- Card creation: slide-down (150ms)
- Undo notification: slide-up + fade-out
- Filter transitions: opacity fade on cards (150ms)

### 10.4 Accessibility
- All interactive elements focusable via Tab
- Modal traps focus when open
- Sufficient color contrast (WCAG AA) for all text
- aria-labels on icon-only buttons (add card, delete, close)

## 11. Testing

Playwright end-to-end tests in `sprints/kanban/tests/` verifying:
- Board loads with three empty columns
- Card CRUD (create, read, update, delete)
- Drag and drop between columns
- Search filtering works in real-time
- Priority filter works
- localStorage persistence across reload
- Keyboard shortcuts work
- Responsive layout at 1024px, 768px, and 375px viewports
- No console errors during all interactions

Tests must be self-contained (start their own HTTP server via conftest.py fixture).

## 12. Acceptance Criteria

The deliverable is accepted when:
1. All features described in sections 2-10 work as specified
2. File size is under 30KB
3. All Playwright tests pass
4. Drag and drop works on both mouse and touch (Chrome, Firefox)
5. Board state survives full page reload
6. No console errors during normal usage
7. WCAG AA contrast ratios met for all text
