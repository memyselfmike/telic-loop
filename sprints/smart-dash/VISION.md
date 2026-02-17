# Vision: Developer Focus Dashboard

## The Problem

A solo developer working on side projects currently alt-tabs between 5 browser tabs to check the time, weather, their task list, and a pomodoro timer. Each context switch costs ~15 seconds and breaks flow. Over a 4-hour deep work session, they lose 10-15 minutes to tab-switching and often forget what they were checking. There is no single-pane view that shows "everything I need during a focus session" without leaving the editor's split-screen.

## The Outcome

After this sprint, the developer opens one `index.html` file in a browser pane beside their editor. At a glance — without clicking or navigating — they see:
1. Current time and date
2. Local weather (temperature + conditions via a free API)
3. A simple task list (add/complete/delete, persisted in localStorage)
4. A pomodoro timer (25min work / 5min break, with audio notification)

The dashboard fits in a narrow side-pane (400px wide) and uses a dark theme to reduce eye strain during long sessions.

## Causal Logic

- IF we consolidate time, weather, tasks, and timer into one view THEN the developer stops alt-tabbing BECAUSE the four most-checked items during focus sessions are all visible without switching.
- IF the pomodoro timer is always visible THEN the developer takes regular breaks BECAUSE the countdown creates gentle urgency and the audio notification is impossible to miss.
- IF tasks are persisted in localStorage THEN the developer can close/reopen the dashboard without losing their list BECAUSE no server or account is needed.

## Success Signals

1. Running `index.html` in a browser shows all four widgets rendering correctly.
2. Adding a task, refreshing the page, and seeing the task still there (localStorage persistence).
3. Starting the pomodoro timer, waiting for it to count down, and hearing the notification sound.
4. The page layout works at 400px width (side-pane mode) without horizontal scrolling.
5. Weather widget shows real data from a free API (OpenWeatherMap free tier with a hardcoded demo key or fallback to mock data).

## Failure Modes

- **API key exposure**: The weather API key will be in client-side JS. Acceptable for a personal local tool; document this limitation.
- **No sync**: localStorage is browser-local. If the developer uses multiple browsers, tasks won't sync. Acceptable for v1; note as a known limitation.
- **Audio autoplay**: Some browsers block audio without user interaction. The timer start button counts as interaction, so notification should work after the user clicks "Start".
