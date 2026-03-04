# Bookshelf — Personal Book Tracker

A beautiful, fast personal book library application where you can catalog your books, track reading progress, and instantly search across your entire collection using full-text search.

## Features

- **Book Management**: Add, edit, and delete books with cover images, ratings, notes, and reading status
- **Full-Text Search**: Instant search powered by MeiliSearch — search by title, author, genre, or notes
- **Reading Status Tracking**: Organize books by Want to Read, Currently Reading, Finished, or Abandoned
- **Statistics Dashboard**: View total books, status breakdowns, genre distribution, and average ratings
- **Persistent Storage**: All data persists across restarts with PostgreSQL and MeiliSearch volumes
- **Responsive Design**: Clean, polished UI that works across desktop and mobile devices
- **Real-time Updates**: Changes to books are immediately synced to the search index

## Tech Stack

### Backend
- **Node.js 20** with Express
- **PostgreSQL 16** for primary data storage
- **MeiliSearch v1.6** for full-text search

### Frontend
- **Vanilla JavaScript** (no build step required)
- **HTML5 & CSS3** with custom properties
- **Nginx** for static file serving and API proxy

### Infrastructure
- **Docker Compose** for orchestration
- **Named volumes** for data persistence
- **Health checks** for reliable startup

## Getting Started

### Prerequisites

- Docker and Docker Compose installed on your machine
- Ports 8080, 3000, 5432, and 7700 available

### Installation

1. Clone or navigate to the project directory:
   ```bash
   cd sprints/bookshelf
   ```

2. Start all services:
   ```bash
   docker compose up
   ```

3. Open your browser to:
   ```
   http://localhost:8080
   ```

That's it! The application will:
- Initialize the PostgreSQL database with the schema
- Configure MeiliSearch indexes automatically
- Serve the frontend and API

### Stopping the Application

```bash
docker compose down
```

To remove all data volumes:
```bash
docker compose down -v
```

## Usage

### Managing Books

- **Add a Book**: Click the "+ Add Book" button in the header
- **View Details**: Click on any book card to see full details
- **Edit a Book**: Click "Edit" in the book detail modal
- **Delete a Book**: Click "Delete" in the book detail modal (with confirmation)
- **Rate a Book**: Use the interactive star rating in the add/edit form

### Searching

- Type in the search bar at the top of the page
- Search results appear as you type (debounced 300ms)
- Search across title, author, genre, and notes
- Press Escape to clear search

### Filtering

- Use the filter tabs to view books by status:
  - All
  - Want to Read
  - Reading
  - Finished
  - Abandoned

### Statistics

- Click the "📊 Stats" button to view your reading statistics
- See total books, status breakdowns, top genres, and average rating
- Click "📚 Library" to return to the main view

## Project Structure

```
sprints/bookshelf/
├── api/                      # Node.js Express API
│   ├── routes/              # API route handlers
│   │   ├── books.js         # CRUD operations for books
│   │   ├── search.js        # Full-text search endpoint
│   │   └── stats.js         # Statistics endpoint
│   ├── db.js                # PostgreSQL connection pool
│   ├── search.js            # MeiliSearch client
│   ├── server.js            # Express app setup
│   ├── Dockerfile           # API container build
│   └── package.json         # API dependencies
├── frontend/                # Static frontend
│   ├── css/                 # Stylesheets
│   │   ├── variables.css    # CSS custom properties
│   │   ├── base.css         # Base styles
│   │   └── components.css   # Component styles
│   ├── js/                  # JavaScript modules (IIFE pattern)
│   │   ├── api.js           # API client
│   │   ├── app.js           # Main application
│   │   ├── library.js       # Book grid display
│   │   ├── modal.js         # Modal dialogs
│   │   ├── search.js        # Search functionality
│   │   └── stats.js         # Statistics dashboard
│   ├── index.html           # Single-page application
│   ├── nginx.conf           # Nginx configuration
│   └── Dockerfile           # Frontend container build
├── db/
│   └── init.sql             # Database schema initialization
└── docker-compose.yml       # Service orchestration
```

## API Reference

Base URL: `http://localhost:3000/api`

### Books

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/books` | List all books (optional `?status=` query param) |
| GET | `/books/:id` | Get single book by ID |
| POST | `/books` | Create new book |
| PUT | `/books/:id` | Update existing book |
| DELETE | `/books/:id` | Delete book |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search?q=` | Full-text search (searches title, author, genre, notes) |

### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats` | Get reading statistics (total, by status, genres, average rating) |

### Book Schema

```json
{
  "id": "uuid",
  "title": "string (required)",
  "author": "string (required)",
  "genre": "string (optional)",
  "cover_url": "string (optional, URL)",
  "status": "want_to_read | reading | finished | abandoned",
  "rating": "integer 1-5 (optional)",
  "notes": "text (optional)",
  "date_added": "timestamptz",
  "date_finished": "timestamptz (optional)"
}
```

## Configuration

All configuration is managed through environment variables in `docker-compose.yml`:

- **Database**: PostgreSQL connection via `DATABASE_URL`
- **Search**: MeiliSearch host and API key via `MEILI_HOST` and `MEILI_KEY`
- **Ports**: All services use standard ports defined in the compose file

## Development

### API Development

The API uses Node.js with Express and the `pg` library for PostgreSQL. The search module uses native `fetch` to communicate with MeiliSearch.

Key patterns:
- Connection pooling for PostgreSQL
- Fire-and-forget search index updates
- Graceful shutdown handling

### Frontend Development

The frontend uses vanilla JavaScript with the IIFE (Immediately Invoked Function Expression) pattern for module isolation. No build step is required.

Key patterns:
- Global namespace modules (`window.BookAPI`, `window.Library`, etc.)
- Debounced search input
- Toast notifications for user feedback
- Responsive grid layout with CSS Grid

### Database

The PostgreSQL database is initialized automatically from `db/init.sql` on first run. It includes:
- UUID primary keys
- Status and rating constraints
- Indexes on status and genre for query performance

### Search

MeiliSearch is configured on startup with:
- Searchable attributes: title, author, genre, notes
- Filterable attributes: status, genre, rating
- Sortable attributes: date_added

## License

MIT
