# Bookshelf Architecture

## Overview

Bookshelf is a containerized personal book tracking application built with a microservices architecture. The system provides book management, full-text search, and reading statistics through a clean separation between data storage (PostgreSQL), search indexing (MeiliSearch), API layer (Node.js/Express), and frontend presentation (vanilla JavaScript SPA).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Browser                              │
│                     http://localhost:8080                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   Frontend     │
                    │  (Nginx:8080)  │
                    │                │
                    │  Static Files  │
                    │  API Proxy     │
                    └────────┬───────┘
                             │
                             │ /api/*
                             ▼
                    ┌────────────────┐
                    │   API Server   │
                    │  (Express:3000)│
                    │                │
                    │  - Books CRUD  │
                    │  - Search      │
                    │  - Stats       │
                    └───┬───────┬────┘
                        │       │
              ┌─────────┘       └─────────┐
              │                           │
              ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐
    │   PostgreSQL    │         │  MeiliSearch    │
    │   (Port 5432)   │         │  (Port 7700)    │
    │                 │         │                 │
    │  - books table  │         │  - books index  │
    │  - Named volume │         │  - Named volume │
    └─────────────────┘         └─────────────────┘
```

## Components

### 1. Frontend (Nginx + Vanilla JS)

**Technology**: Nginx Alpine serving static HTML/CSS/JS

**Responsibilities**:
- Serve the single-page application
- Proxy API requests to backend (eliminates CORS)
- Cache static assets
- Provide fallback routing for SPA

**Key Files**:
- `index.html`: Application shell
- `js/app.js`: Main application controller, toast notifications
- `js/api.js`: REST API client using Fetch API
- `js/library.js`: Book grid rendering and filtering
- `js/modal.js`: Add/edit/detail modal dialogs
- `js/search.js`: Debounced search functionality
- `js/stats.js`: Statistics dashboard
- `css/`: Modular stylesheets with CSS custom properties

**Design Patterns**:
- IIFE (Immediately Invoked Function Expression) for module isolation
- Global namespace pattern for inter-module communication
- Event delegation for dynamic content

### 2. API Server (Node.js/Express)

**Technology**: Node.js 20 with Express framework

**Responsibilities**:
- RESTful API for book CRUD operations
- Search query routing to MeiliSearch
- Statistical aggregations from PostgreSQL
- Search index synchronization
- Database connection pooling
- Service health checks

**Key Modules**:
- `server.js`: Express app setup, middleware, health checks
- `db.js`: PostgreSQL connection pool configuration
- `search.js`: MeiliSearch client with retry logic
- `routes/books.js`: Book CRUD endpoints
- `routes/search.js`: Search endpoint
- `routes/stats.js`: Statistics aggregation endpoint

**Design Patterns**:
- Router-based modular endpoints
- Fire-and-forget async operations for search sync
- Error handling with appropriate HTTP status codes
- Graceful shutdown handling (SIGTERM)

### 3. Database (PostgreSQL 16)

**Technology**: PostgreSQL 16 Alpine

**Responsibilities**:
- Primary data store for all books
- Relational integrity and constraints
- Indexed queries for filtering and statistics

**Schema**:
```sql
books (
  id UUID PRIMARY KEY,
  title VARCHAR(500) NOT NULL,
  author VARCHAR(500) NOT NULL,
  genre VARCHAR(100),
  cover_url TEXT,
  status VARCHAR(20) CHECK(status IN (...)),
  rating INTEGER CHECK(rating BETWEEN 1 AND 5),
  notes TEXT,
  date_added TIMESTAMPTZ DEFAULT NOW(),
  date_finished TIMESTAMPTZ
)

Indexes:
- idx_books_status ON status
- idx_books_genre ON genre
```

**Features**:
- Automatic UUID generation via `gen_random_uuid()`
- Enum-like constraints for status values
- Range constraints for ratings
- Timestamp defaults for audit trail

### 4. Search Engine (MeiliSearch)

**Technology**: MeiliSearch v1.6

**Responsibilities**:
- Full-text search across multiple fields
- Typo tolerance
- Instant results (< 50ms typically)
- Relevance ranking

**Configuration**:
```javascript
{
  searchableAttributes: ['title', 'author', 'genre', 'notes'],
  filterableAttributes: ['status', 'genre', 'rating'],
  sortableAttributes: ['date_added']
}
```

**Sync Strategy**:
- API sends updates to MeiliSearch after PostgreSQL writes
- Fire-and-forget pattern (non-blocking)
- Eventual consistency model
- Error logging for sync failures

## Data Flow

### Adding a Book

```
User → Frontend Form → API POST /books
  → PostgreSQL INSERT → Return Book Object
  → MeiliSearch addOrUpdate (async) → 201 Response
  → Frontend Refresh Library View
```

1. User fills out add book form and submits
2. Frontend sends POST request to `/api/books`
3. API validates required fields (title, author) and constraints
4. API inserts book into PostgreSQL
5. API fires async request to MeiliSearch to index the book
6. API returns created book with 201 status
7. Frontend shows success toast and refreshes the library

### Searching for Books

```
User Types → Debounced Input (300ms)
  → API GET /search?q={query}
  → MeiliSearch Search → Ranked Results
  → Frontend Render Results
```

1. User types in search input
2. After 300ms debounce, frontend sends GET request
3. API forwards query to MeiliSearch
4. MeiliSearch performs full-text search with ranking
5. API returns results array
6. Frontend renders book cards from results

### Viewing Statistics

```
User Clicks Stats → API GET /stats
  → PostgreSQL Aggregation Queries (COUNT, AVG, GROUP BY)
  → Return Structured Stats
  → Frontend Render Dashboard
```

1. User clicks "📊 Stats" button
2. Frontend sends GET request to `/api/stats`
3. API executes multiple aggregation queries:
   - Total book count
   - Count by status (GROUP BY)
   - Genre distribution (GROUP BY, ORDER BY)
   - Average rating (AVG)
4. API returns structured JSON response
5. Frontend renders stat cards and genre chart

## Key Design Decisions

### 1. Vanilla JavaScript Frontend

**Rationale**: No framework overhead, no build step, fast iteration

The frontend uses plain JavaScript with the IIFE pattern for modular code organization. This approach:
- Eliminates build tooling complexity
- Reduces deployment size (no framework bundles)
- Provides instant development feedback
- Uses standard browser APIs (Fetch, DOM)

Trade-off: Less abstraction means more manual DOM manipulation, but the app is simple enough that this is manageable.

### 2. MeiliSearch for Full-Text Search

**Rationale**: PostgreSQL LIKE queries don't provide true full-text search

MeiliSearch provides:
- Typo tolerance ("harry poter" finds "Harry Potter")
- Relevance ranking
- Multi-field search
- Sub-50ms response times
- Simple REST API

Trade-off: Adds complexity (another service, data sync) but delivers significantly better search UX.

### 3. Fire-and-Forget Search Sync

**Rationale**: Don't block API responses on search indexing

When creating/updating books:
- PostgreSQL write completes first (source of truth)
- Response returns immediately
- MeiliSearch sync happens asynchronously
- Errors are logged but don't fail the request

Trade-off: Eventual consistency between DB and search (typically < 100ms), but better API performance and reliability.

### 4. Docker Compose with Health Checks

**Rationale**: Reliable startup order without race conditions

Services declare dependencies with health checks:
```yaml
api:
  depends_on:
    db:
      condition: service_healthy
    search:
      condition: service_healthy
```

This ensures:
- PostgreSQL is accepting connections before API starts
- MeiliSearch is ready before API configures indexes
- Zero manual coordination required

### 5. Nginx API Proxy

**Rationale**: Eliminate CORS, single origin for frontend

The Nginx frontend container proxies `/api/*` requests to the API server:
```nginx
location /api/ {
    proxy_pass http://api:3000/api/;
}
```

Benefits:
- No CORS configuration needed
- Single port for user (8080)
- Static asset caching
- Production-ready pattern

### 6. Named Docker Volumes

**Rationale**: Persistent data across container restarts

Both PostgreSQL and MeiliSearch use named volumes:
```yaml
volumes:
  pgdata:
  msdata:
```

This provides:
- Data persistence across `docker compose down && up`
- Easy backup/restore targets
- Explicit volume management

## Infrastructure

### Docker Compose Services

| Service | Base Image | Port | Volume | Health Check |
|---------|-----------|------|--------|--------------|
| db | postgres:16-alpine | 5432 | pgdata | pg_isready |
| search | getmeili/meilisearch:v1.6 | 7700 | msdata | curl /health |
| api | Custom (Node 20 Alpine) | 3000 | - | - |
| frontend | Custom (Nginx Alpine) | 8080 | - | - |

### Environment Configuration

All configuration is environment-based:

**Database**:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DATABASE_URL` (connection string for API)

**Search**:
- `MEILI_MASTER_KEY` (authentication)
- `MEILI_HOST` (API connection)

**API**:
- `NODE_ENV` (development/production)
- `PORT` (defaults to 3000)

### Startup Sequence

1. **PostgreSQL** starts, initializes from `init.sql` (first run only)
2. **MeiliSearch** starts, creates data directory
3. **API** waits for DB and Search health checks, then:
   - Connects to PostgreSQL
   - Configures MeiliSearch indexes
   - Starts Express server on port 3000
4. **Frontend** starts Nginx, proxies to API

### Development Workflow

1. Edit source files (no build step for frontend)
2. `docker compose up --build` to rebuild changed containers
3. API auto-restarts on code changes (if using nodemon)
4. Database schema changes require new migration scripts
5. Frontend changes reflect immediately (Nginx serves static files)

## Security Considerations

**Current State** (Development):
- MeiliSearch uses a development master key
- PostgreSQL uses default credentials
- No HTTPS (local development)
- CORS eliminated via proxy

**Production Recommendations**:
- Use strong, unique MeiliSearch master key
- Use PostgreSQL secrets management
- Terminate TLS at Nginx or load balancer
- Add rate limiting to API endpoints
- Implement input sanitization/validation
- Add authentication/authorization layer
- Use read-only database user for search/stats queries

## Performance Characteristics

**Expected Performance**:
- Book list: < 100ms (PostgreSQL indexed queries)
- Search: < 50ms (MeiliSearch)
- Stats: < 200ms (PostgreSQL aggregations)
- Add/Edit/Delete: < 150ms (PostgreSQL write + async search sync)

**Scalability**:
- Current design handles 10,000+ books comfortably
- PostgreSQL indexes support fast filtering
- MeiliSearch designed for millions of documents
- Horizontal scaling would require load balancer + read replicas

## Monitoring and Debugging

**Health Checks**:
- API root (`GET /`) checks database connectivity
- Docker health checks ensure service availability

**Logging**:
- API logs to stdout (Docker captures)
- PostgreSQL logs to container stderr
- MeiliSearch logs search operations

**Common Issues**:
- Search sync failures: Check MeiliSearch logs
- Slow queries: Check PostgreSQL query plans
- Startup failures: Check service dependencies and health checks
