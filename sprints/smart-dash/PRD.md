# PRD: Developer Focus Dashboard

## Overview

A single-file HTML dashboard (`index.html`) that a developer opens in a browser side-pane during focus sessions. Shows time, weather, task list, and pomodoro timer — all without leaving the page. No build tools, no frameworks, no server.

## Requirements

### Widgets

1. **Clock Widget**: Displays current time (HH:MM:SS, 24h format) and date (Day, Month DD). Updates every second.

2. **Weather Widget**: Shows temperature (°C) and condition text (e.g. "Cloudy"). Fetches from OpenWeatherMap free API on page load. Falls back to "Weather unavailable" on error. Refreshes every 30 minutes. Uses a hardcoded demo API key with a comment explaining how to replace it.

3. **Task List Widget**: Add task via text input + Enter key. Mark complete (strikethrough + checkbox). Delete with an × button. Persists to localStorage on every change. Loads from localStorage on page load. Shows task count ("3 tasks, 1 done").

4. **Pomodoro Timer Widget**: Start/Pause/Reset buttons. Displays MM:SS countdown. Default 25:00 work, 5:00 break. Plays a short beep sound (generated via Web Audio API, no external files) when timer reaches 00:00. Auto-switches between work and break. Shows "WORK" or "BREAK" label. Tracks completed pomodoro count for the session.

### Layout & Styling

- Single column layout, optimized for 400px width
- Dark theme: dark background (#1a1a2e or similar), light text, accent colors for interactive elements
- No external CSS frameworks — vanilla CSS in a `<style>` block
- Responsive: works at 400px (side pane) and full width (standalone)
- Clean visual hierarchy: clock at top, then weather, then tasks, then timer

### Technical Constraints

- **Single file**: Everything in one `index.html` — HTML, CSS, JS
- **No dependencies**: No npm, no CDN imports, no build step
- **No server**: Opens directly via `file://` or any static server
- **Browser support**: Modern Chrome/Firefox/Edge (ES6+ is fine)

## Out of Scope

- User authentication
- Cloud sync
- Mobile-specific optimizations beyond basic responsiveness
- Multiple themes
- Widget drag-and-drop or reordering
- Backend or database

## Acceptance Criteria

1. Opening `index.html` in Chrome shows all 4 widgets without errors in the console (except the weather API network call if offline)
2. Task CRUD works and survives page refresh
3. Pomodoro timer counts down and produces an audible beep at zero
4. Layout renders correctly at 400px viewport width
5. Total file size under 15KB (it's a single HTML file with inline CSS/JS)
