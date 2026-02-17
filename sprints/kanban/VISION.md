# Vision: Personal Kanban Board

## The Outcome

A developer opens a single HTML file in their browser and has a fully functional personal Kanban board — the kind of tool they'd actually use daily to manage their work. No server, no build step, no accounts. Just open the file and start organizing.

## Who Is This For

A solo developer or freelancer who wants a lightweight, private task board. They don't want Trello's complexity or Jira's overhead. They want something they can keep in a project folder, open in any browser, and have it just work — with their data staying on their machine.

## What "Value Delivered" Looks Like

The user can:

1. **See their work at a glance.** Three default columns (To Do, In Progress, Done) with cards that show title, description preview, priority, and labels — all visible without clicking into anything.

2. **Manage cards fluidly.** Create a card with a title and optional description, edit it inline, delete it with confirmation. Adding a card should feel instant — click "+" on a column, type a title, press Enter, done.

3. **Drag cards between columns.** Pick up a card, drag it to another column, drop it. The card stays where you put it. This must feel native — smooth visual feedback during drag, clear drop targets, no jank or flicker.

4. **Organize with priority and labels.** Each card can have a priority level (low/medium/high/urgent) shown as a colored left border, and one or more text labels (shown as colored chips). The user can filter the entire board by label or priority to focus on what matters.

5. **Find cards quickly.** A search box at the top filters cards in real-time as the user types — matching against title, description, and labels. The board updates instantly, hiding non-matching cards while preserving column structure.

6. **Trust that nothing is lost.** Every change persists to localStorage immediately. Close the tab, reopen the file tomorrow — everything is exactly where they left it. The board also supports undo for the last action (Ctrl+Z).

7. **Work efficiently with keyboard.** Power users can navigate and manage the board without touching the mouse: keyboard shortcuts for new card (N), search focus (/), undo (Ctrl+Z), and Escape to close modals/cancel edits.

8. **Use it anywhere.** The board works on a 1920px desktop monitor and a 768px tablet. On narrow viewports, columns stack vertically and remain usable with touch scrolling.

## What This Is NOT

- Not a team collaboration tool (no sharing, no real-time sync)
- Not a project management suite (no timelines, no sprints, no burndown)
- Not a backend application (no server, no database, no API)

## Constraints

- Single HTML file, under 30KB
- Zero external dependencies (no CDN links, no npm packages)
- Works offline in any modern browser (Chrome, Firefox, Safari, Edge)
- Dark theme with professional appearance
- All state in localStorage — no cookies, no server
