# PRD: Freelancer Time Tracker

## 1. System Architecture

### 1.1 Services
- **API Server**: FastAPI application on port 8000
  - REST API endpoints under `/api/`
  - Static file serving for frontend at `/`
  - SQLite database at `sprints/time-tracker/data/timetracker.db`
- **Frontend**: Vanilla JS SPA served as static files from `sprints/time-tracker/frontend/`

### 1.2 Technology Stack
- Backend: Python 3.11+, FastAPI, uvicorn, sqlite3 (stdlib)
- Frontend: HTML, CSS, JavaScript (no frameworks, no build step)
- Database: SQLite 3
- No external dependencies beyond FastAPI and uvicorn

### 1.3 Project Structure
```
sprints/time-tracker/
├── backend/
│   ├── main.py          # FastAPI app, startup, static mounting
│   ├── database.py      # SQLite connection, schema, migrations
│   ├── models.py        # Pydantic models for request/response
│   ├── routes/
│   │   ├── projects.py  # Project CRUD endpoints
│   │   ├── entries.py   # Time entry CRUD + timer endpoints
│   │   └── reports.py   # Timesheet generation + export
│   └── requirements.txt # fastapi, uvicorn
├── frontend/
│   ├── index.html       # SPA shell
│   ├── style.css        # Dark theme styles
│   └── app.js           # Application logic
├── data/                # SQLite database (gitignored)
└── tests/
    ├── conftest.py      # Test fixtures (start server, etc.)
    ├── test_api_projects.py
    ├── test_api_entries.py
    ├── test_api_timer.py
    ├── test_api_reports.py
    ├── test_frontend_timer.py
    ├── test_frontend_entries.py
    ├── test_frontend_projects.py
    ├── test_frontend_weekly.py
    └── test_frontend_reports.py
```

## 2. Database Schema

### 2.1 Projects Table
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    client_name TEXT NOT NULL DEFAULT '',
    hourly_rate REAL NOT NULL DEFAULT 0.0,
    color TEXT NOT NULL DEFAULT '#58a6ff',
    archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 2.2 Time Entries Table
```sql
CREATE TABLE time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    description TEXT NOT NULL DEFAULT '',
    start_time TEXT NOT NULL,
    end_time TEXT,              -- NULL if timer is running
    duration_seconds INTEGER,   -- computed on stop, NULL while running
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 2.3 Timer State
A running timer is represented by a time entry with `end_time IS NULL`. There can be at most one running entry at any time. The API enforces this constraint.

### 2.4 Migrations
On application startup, `database.py` creates tables if they don't exist. No migration framework needed — just `CREATE TABLE IF NOT EXISTS`.

## 3. API Endpoints

### 3.1 Projects

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|-------------|----------|
| GET | `/api/projects` | List all projects | — | `[{id, name, client_name, hourly_rate, color, archived}]` |
| GET | `/api/projects?active=true` | List active (non-archived) projects | — | Same |
| POST | `/api/projects` | Create project | `{name, client_name?, hourly_rate?, color?}` | `{id, name, ...}` (201) |
| GET | `/api/projects/{id}` | Get project | — | `{id, name, ...}` |
| PUT | `/api/projects/{id}` | Update project | `{name?, client_name?, hourly_rate?, color?, archived?}` | `{id, name, ...}` |
| DELETE | `/api/projects/{id}` | Delete project (only if no entries) | — | 204 |

### 3.2 Time Entries

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|-------------|----------|
| GET | `/api/entries` | List entries (supports filters) | — | `[{id, project_id, description, start_time, end_time, duration_seconds, project_name, project_color}]` |
| GET | `/api/entries?date=2026-02-17` | Entries for a specific date | — | Same |
| GET | `/api/entries?from=2026-02-10&to=2026-02-16` | Entries in date range | — | Same |
| GET | `/api/entries?project_id=1` | Entries for a project | — | Same |
| POST | `/api/entries` | Create manual entry | `{project_id, description?, start_time, end_time}` | `{id, ...}` (201) |
| PUT | `/api/entries/{id}` | Update entry | `{project_id?, description?, start_time?, end_time?}` | `{id, ...}` |
| DELETE | `/api/entries/{id}` | Delete entry | — | 204 |

### 3.3 Timer

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|-------------|----------|
| GET | `/api/timer` | Get running timer (if any) | — | `{id, project_id, description, start_time, elapsed_seconds, project_name}` or `null` |
| POST | `/api/timer/start` | Start timer | `{project_id, description?}` | `{id, ...}` (201) |
| POST | `/api/timer/stop` | Stop running timer | — | `{id, ..., duration_seconds}` |

Starting a timer when one is already running must first stop the existing timer, then start the new one (auto-switch behavior).

### 3.4 Reports

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/api/reports/timesheet?from=DATE&to=DATE&project_id=ID` | Generate timesheet | `{entries: [...], daily_totals: {date: seconds}, project_totals: {id: {name, seconds, amount}}, grand_total_seconds, grand_total_amount}` |
| GET | `/api/reports/timesheet/csv?from=DATE&to=DATE&project_id=ID` | Export as CSV | CSV file download |

### 3.5 Error Handling
All errors return JSON: `{"detail": "message"}` with appropriate HTTP status codes:
- 400: Validation errors
- 404: Resource not found
- 409: Conflict (e.g., deleting project with entries)
- 422: Unprocessable entity (FastAPI validation)

### 3.6 Datetime Format
All datetime fields use ISO 8601 format: `2026-02-17T14:30:00`. The API operates in local time (no timezone handling needed for a single-user local tool).

## 4. Frontend

### 4.1 Navigation
Single-page app with tab-based navigation:
- **Timer** (default view) — active timer + today's entries
- **Weekly** — 7-day time grid
- **Projects** — project management
- **Reports** — timesheet generation + export

### 4.2 Timer View (Dashboard)

**Active Timer Section:**
- Project dropdown (active projects only, with color indicators)
- Description text input
- Start/Stop button (toggles based on timer state)
- Running time display: HH:MM:SS, updates every second
- If a timer is running when the page loads, show it with correct elapsed time (computed from `start_time` vs current time)

**Today's Entries Section:**
- List of today's entries, most recent first
- Each entry shows: project color dot, project name, description, start-end times, duration (HH:MM)
- Click entry to edit (inline or modal)
- Delete button on each entry (with confirmation)
- "Add Manual Entry" button opens a form with: date (defaults today), start time, end time, project dropdown, description

**Today's Summary:**
- Total hours today (HH:MM format)
- Breakdown by project: project color + name + hours

### 4.3 Weekly View

**Week Grid:**
- 7 columns (Monday through Sunday) with date headers
- Each column shows entries for that day, stacked vertically
- Each entry shows: project color bar, project name (truncated), duration
- Day total at the bottom of each column
- Click an entry to edit or delete

**Week Navigation:**
- Previous/Next week buttons
- "This Week" button to jump to current week
- Week date range displayed (e.g., "Feb 10 - Feb 16, 2026")

**Week Summary:**
- Project rows showing: project color + name + hours per day + weekly total
- Grand total row

### 4.4 Projects View

**Project List:**
- Cards for each project showing: color swatch, name, client name, hourly rate, total hours logged
- "Active" and "Archived" tabs
- "New Project" button

**Project Form (modal or inline):**
- Name (required)
- Client name
- Hourly rate (number input, currency format)
- Color picker (preset palette of 8-10 colors)
- Archive/Unarchive toggle
- Delete button (disabled if project has entries, with explanation tooltip)

### 4.5 Reports View

**Timesheet Generator:**
- Date range picker: "From" and "To" date inputs
- Project filter dropdown (optional, "All Projects" default)
- "Generate" button
- Preset buttons: "This Week", "Last Week", "This Month", "Last Month"

**Timesheet Display:**
- Entries grouped by date, then by project within each date
- Each entry shows: project name, description, start-end times, duration, amount (rate * hours)
- Daily subtotal row (hours + amount)
- Project summary section: each project's total hours and amount
- Grand total: total hours, total amount
- "Export CSV" button

**CSV Format:**
```
Date,Project,Client,Description,Start,End,Hours,Rate,Amount
2026-02-17,Website Redesign,Acme Corp,Homepage layout,09:00,12:30,3.50,150.00,525.00
```

### 4.6 Visual Design

**Dark Theme:**
- Background: #0d1117 (main), #161b22 (panels), #21262d (cards/inputs)
- Text: #e6edf3 (primary), #8b949e (secondary)
- Accent: #58a6ff (primary actions), #3fb950 (start/success), #f85149 (stop/delete)
- Borders: #30363d
- Project colors palette: #58a6ff, #3fb950, #f85149, #d29922, #bc8cff, #f778ba, #79c0ff, #56d364

**Typography:**
- System font stack
- Headings: 18px semibold
- Body: 14px normal
- Timer display: 32px monospace bold
- Small text: 12px

**Responsiveness:**
- Desktop (>= 1024px): Full layout with sidebar-style navigation
- Tablet (768px - 1023px): Stacked layout, navigation as top tabs

### 4.7 API Communication
All frontend-backend communication via `fetch()` with JSON. Handle loading states (spinner or skeleton) and error states (toast notification with error message). Poll timer status every 5 seconds to keep elapsed time accurate across tabs.

## 5. Testing

### 5.1 API Tests (pytest + httpx)
Test all CRUD operations, timer start/stop/auto-switch, report generation, CSV export, error handling, edge cases (overlapping entries, empty date ranges, deleting project with entries).

### 5.2 Frontend Tests (Playwright)
Test timer flow (start, see counting, stop, see entry), manual entry creation, project CRUD, weekly navigation, report generation and CSV download. Tests start the FastAPI server as a fixture.

### 5.3 Test Infrastructure
`conftest.py` provides:
- A test database (temporary file, cleaned between tests)
- A running FastAPI server (on a dynamic port)
- Playwright page fixture pointed at the running server

## 6. Acceptance Criteria

1. API server starts with `uvicorn backend.main:app` from the sprint directory
2. All API endpoints respond correctly per Section 3
3. Timer survives browser close and page reload (server-side state)
4. Frontend shows all four views with working navigation
5. Time entries persist across server restart (SQLite)
6. Timesheet generation produces correct totals
7. CSV export downloads a valid file
8. No console errors in the frontend during normal usage
9. All API tests pass
10. All Playwright frontend tests pass
11. Responsive layout works at 1024px and 768px
12. Dark theme is visually consistent across all views
