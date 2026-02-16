# Vision: Personal Todo App

## Promise
A developer wants a lightweight, self-contained personal task tracker they can open in any browser — no server, no build step, no dependencies. They want to add tasks, mark them done, filter by status, and have everything persist across browser sessions via localStorage. Currently they resort to sticky notes or heavyweight apps like Notion for simple daily task lists.

## Primary Goal
G1: A single `index.html` file (with embedded CSS and JS) that provides a fully functional todo app in the browser — add, complete, delete, filter, and persist tasks — with zero setup.

## Success Metrics
1. Opening `index.html` in a browser shows a clean task input field and an empty task list.
2. Typing "Buy groceries" and pressing Enter adds it to the visible list.
3. Clicking a task's checkbox toggles it between active and completed (with visual strikethrough).
4. Clicking a delete button removes a task permanently.
5. Filter buttons (All / Active / Completed) show only the matching tasks.
6. Refreshing the browser preserves all tasks (localStorage persistence).
7. The UI is responsive and usable on both desktop (1024px+) and mobile (375px) widths.

## Target User
Individual developer who wants a frictionless daily task list without leaving their local environment.

## Scope Boundary
- Single HTML file, no server, no npm, no framework
- Pure HTML + CSS + JS (vanilla)
- localStorage for persistence (no backend)
- No authentication, no multi-user, no sync
