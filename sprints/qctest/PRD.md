# PRD: NoteBox

## Overview

NoteBox is a minimal note-taking web app with Node.js + Express backend and
JSON-file persistence. Two pages: notes list and stats dashboard.

## Tech Stack

- **Backend**: Node.js + Express
- **Storage**: JSON file (`data/notes.json`)
- **Frontend**: Vanilla HTML/CSS/JS (no frameworks)
- **Port**: 3000

## Data Model

```json
{
  "id": "uuid-string",
  "title": "string",
  "body": "string",
  "createdAt": "ISO-8601"
}
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/notes` | List all notes |
| POST | `/api/notes` | Create a note (title, body) |
| GET | `/api/notes/:id` | Get single note |
| DELETE | `/api/notes/:id` | Delete a note |
| GET | `/api/stats` | Aggregate stats |

### Stats Response

```json
{
  "totalNotes": 5,
  "averageBodyLength": 142,
  "newestDate": "2026-02-27T10:00:00Z",
  "oldestDate": "2026-02-20T08:30:00Z"
}
```

## Pages

### Notes List (`/`)
- Shows all notes as cards (title + first 80 chars of body)
- "New Note" button opens an inline form (title + body textarea + Save button)
- Each card has a Delete button
- Clicking a card title shows the full note body expanded inline

### Stats Dashboard (`/stats`)
- Displays total notes, average body length, newest date, oldest date
- Link back to notes list

## Non-Goals
- No authentication
- No editing notes after creation
- No search or filtering
- No markdown rendering
