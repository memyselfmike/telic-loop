# Vision: Freelancer Time Tracker

## The Outcome

A freelancer opens a web app in their browser and has a complete system for tracking billable hours across multiple client projects. They start a timer, work, stop it, and at the end of the week they generate a professional timesheet showing exactly how many hours they spent on each project — broken down by day, with descriptions of what they did. No spreadsheets, no mental math, no "I think I worked about 6 hours on that."

## Who Is This For

A solo freelancer or consultant who bills hourly. They juggle 2-5 active client projects simultaneously. They need to know: (1) what they're working on right now, (2) how much time they've logged today, (3) how their week looks across all projects, and (4) a clean summary they can attach to an invoice or share with a client.

## What "Value Delivered" Looks Like

### 1. Track Time Effortlessly

The freelancer sees a prominent timer on the dashboard. They select a project from a dropdown, optionally type a description of what they're working on, and click Start. The timer counts up in real-time (HH:MM:SS). When they switch tasks or take a break, they click Stop. The entry is saved automatically.

They can also add time manually — for yesterday's work they forgot to track, or for a meeting that happened offline. Manual entry takes a date, start time, end time, project, and description.

### 2. Manage Client Projects

Each project has a name, client name, hourly rate, and color. The freelancer can create, edit, and archive projects. Archived projects don't appear in the active timer dropdown but their historical time entries remain visible in reports.

Projects are the organizational backbone. Every time entry belongs to exactly one project.

### 3. See Today at a Glance

The dashboard shows:
- The running timer (if active) with project name and elapsed time
- Today's entries listed chronologically with project color indicators
- Today's total hours and a breakdown by project
- A quick-add button for manual entries

### 4. Review the Week

A weekly view shows a 7-day grid (Mon-Sun) with time entries stacked by project. Each day shows total hours. Each project row shows its weekly total. The freelancer can navigate between weeks. They can click any entry to edit or delete it.

### 5. Generate Timesheets

The freelancer selects a date range and optionally a specific project, then generates a timesheet. The timesheet shows:
- Entries grouped by day, then by project within each day
- Description for each entry
- Daily subtotals and a grand total
- Project name, client name, hourly rate, and calculated amount
- Export to CSV for import into invoicing tools

### 6. Trust the Data

All data persists in a SQLite database. The app can be stopped and restarted without losing anything. If the browser is closed while a timer is running, reopening the app shows the timer still counting from when it started (server-side timer tracking, not browser-dependent).

## What This Is NOT

- Not a team tool (single user, no auth needed)
- Not an invoicing system (generates data for invoices, doesn't send them)
- Not a project management tool (no tasks, milestones, or deadlines)
- Not a mobile app (responsive web, but not a native app)

## Architecture

This is a full-stack web application:

- **Backend**: Python FastAPI REST API
- **Database**: SQLite (file-based, zero configuration)
- **Frontend**: Single-page application served as static files
- **Services**: API server on port 8000, frontend served from the same server via static file mounting

The backend is the source of truth. The frontend is a thin client that calls the API. Timer state lives on the server so closing the browser doesn't lose a running timer.

## Constraints

- Python 3.11+ for the backend
- No external database servers (SQLite only)
- No JavaScript frameworks (vanilla JS, single HTML file or minimal file set)
- No authentication (single-user local tool)
- The frontend must work at 1024px desktop width and 768px tablet width
- Professional dark theme consistent across all views
- All API endpoints follow REST conventions with proper HTTP status codes
- Database migrations handled by the application on startup (create tables if not exist)
