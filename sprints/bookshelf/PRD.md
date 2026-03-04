# Bookshelf — Product Requirements

## Overview

A personal book tracking web application with a Postgres-backed REST API, MeiliSearch for instant full-text search, and a vanilla HTML/CSS/JS frontend. All services run via Docker Compose.

## Technical Architecture

### Services (Docker Compose)

| Service | Image/Build | Port | Purpose |
|---------|------------|------|---------|
| **api** | Custom (Node.js/Express) | 3000 | REST API, business logic |
| **db** | postgres:16-alpine | 5432 | Primary data store |
| **search** | getmeili/meilisearch:v1.6 | 7700 | Full-text search engine |
| **frontend** | Custom (nginx:alpine) | 8080 | Static file serving |

### Infrastructure Requirements

- `docker-compose.yml` at sprint root — `docker compose up` starts everything
- **Health checks**: API waits for Postgres and MeiliSearch to be healthy before starting
- **Data persistence**: Named Docker volumes for Postgres data and MeiliSearch index
- **Search sync**: When a book is created/updated/deleted via the API, the search index is updated synchronously
- **Environment**: All config via environment variables in docker-compose.yml (no .env files needed)

### API Design (Express + pg)

Base URL: `http://localhost:3000/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /books | List all books (supports `?status=` filter) |
| GET | /books/:id | Get single book |
| POST | /books | Create book |
| PUT | /books/:id | Update book |
| DELETE | /books/:id | Delete book |
| GET | /search?q= | Full-text search via MeiliSearch |
| GET | /stats | Reading statistics |

### Book Schema

```json
{
  "id": "uuid",
  "title": "string (required)",
  "author": "string (required)",
  "genre": "string",
  "cover_url": "string (URL to cover image)",
  "status": "want_to_read | reading | finished | abandoned",
  "rating": "integer 1-5 (nullable)",
  "notes": "text",
  "date_added": "timestamp",
  "date_finished": "timestamp (nullable)"
}
```

### Database (Postgres)

- Single `books` table matching the schema above
- UUID primary key (use `gen_random_uuid()`)
- `date_added` defaults to `NOW()`
- Init script in `db/init.sql` mounted into the Postgres container

### Search (MeiliSearch)

- Index name: `books`
- Searchable attributes: `title`, `author`, `genre`, `notes`
- Filterable attributes: `status`, `genre`, `rating`
- API key set via `MEILI_MASTER_KEY` environment variable

### Frontend (Vanilla HTML/CSS/JS)

Single-page app served by nginx. No build step, no framework.

#### Pages/Views

1. **Library View** (default): Grid of book cards showing cover, title, author, status badge, rating stars. Filter tabs for All/Want to Read/Reading/Finished/Abandoned.
2. **Book Detail Modal**: Full book info with edit/delete actions. Notes displayed with nice formatting.
3. **Add/Edit Form**: Modal form for creating or editing a book. Cover URL preview.
4. **Search**: Persistent search bar in the header. Results appear as-you-type (debounced 300ms).
5. **Stats Dashboard**: Cards showing total books, books per status, genre distribution (bar chart or similar), average rating.

#### Visual Requirements

- Responsive layout (looks good on 1280px and 768px)
- Color-coded status badges (distinct colors per reading status)
- Star rating display (filled/empty stars, not just numbers)
- Book cards with hover elevation effect and smooth transitions
- Clean typography, consistent spacing, subtle shadows
- Loading states for async operations
- Empty states ("No books yet — add your first one!")

## Acceptance Criteria

1. `docker compose up` from the sprint directory starts all 4 services with no manual steps
2. Adding a book via the UI persists it in Postgres AND makes it searchable in MeiliSearch within 1 second
3. Search returns relevant results for partial title, author name, or text in notes
4. Filtering by reading status works correctly
5. Deleting a book removes it from both Postgres and MeiliSearch
6. Stats dashboard shows accurate counts and breakdowns
7. Data survives `docker compose down && docker compose up` (volumes persist)
8. UI is visually polished — not a wireframe or prototype
