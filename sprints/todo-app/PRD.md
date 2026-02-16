# PRD: Personal Todo App

## 1. Overview
A single-file web application (`index.html`) providing a personal task tracker with add, complete, delete, filter, and localStorage persistence. No server, no build tools, no external dependencies.

## 2. Functional Requirements

### 2.1 Task Input
- Text input field with placeholder "What needs to be done?"
- Pressing Enter or clicking an "Add" button creates a new task
- Empty input should not create a task (ignore or show subtle feedback)
- Input field clears after successful task creation

### 2.2 Task Display
- Each task shows: checkbox, task text, delete button
- Tasks appear in a vertical list, newest at the bottom
- Completed tasks show strikethrough text styling and reduced opacity
- Checkbox toggles between active and completed states

### 2.3 Task Deletion
- Each task has a delete button (visible on hover or always visible on mobile)
- Clicking delete removes the task immediately and permanently
- No confirmation dialog needed

### 2.4 Filtering
- Three filter buttons: "All", "Active", "Completed"
- "All" shows every task (default view)
- "Active" shows only tasks not yet completed
- "Completed" shows only completed tasks
- Active filter button should be visually highlighted
- A task count label showing "X items left" (counting active tasks only)

### 2.5 Persistence
- All tasks are saved to `localStorage` on every mutation (add, complete, delete)
- On page load, tasks are restored from `localStorage`
- Tasks store: id, text, completed (boolean), createdAt (timestamp)

### 2.6 Responsive Design
- Desktop (1024px+): centered container, max-width 600px, comfortable padding
- Mobile (375px): full-width, touch-friendly tap targets (min 44px), readable font sizes
- No horizontal scrolling at any viewport width

## 3. Technical Constraints
- Single `index.html` file with embedded `<style>` and `<script>` tags
- Pure vanilla HTML, CSS, and JavaScript — no libraries, no frameworks, no CDN links
- Must work in modern browsers (Chrome, Firefox, Edge — latest versions)
- No server required — opens directly via `file://` protocol

## 4. Acceptance Criteria (Browser-Testable)
1. Opening `index.html` shows an input field and empty task list area
2. Typing "Buy groceries" + Enter adds "Buy groceries" to the visible list
3. Clicking the task's checkbox applies strikethrough styling and marks it completed
4. Clicking the delete button removes the task from the DOM
5. With 3 tasks (2 active, 1 completed): "Active" filter shows only 2 tasks, "Completed" filter shows only 1
6. After adding 3 tasks and refreshing the page, all 3 tasks are still present
7. On a 375px viewport, the UI has no horizontal overflow and all tap targets are at least 44px

## 5. Testing Requirements
- Automated browser tests using Playwright (Python: `playwright`, `pytest-playwright`)
- Tests must launch a local file server or use `file://` protocol to load `index.html`
- Tests must cover all 7 acceptance criteria above
- Tests must include a viewport resize test for mobile responsiveness (375px width)
