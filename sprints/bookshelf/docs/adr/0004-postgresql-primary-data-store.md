# ADR-0004: PostgreSQL as Primary Data Store

## Status
Accepted

## Context

The application needs persistent storage for book data with support for:
- ACID transactions
- Relational integrity (books with multiple attributes)
- Efficient filtering by status and genre
- Statistical aggregations (counts, averages, group by)
- Data persistence across application restarts

Options considered:

1. **PostgreSQL** - Full-featured relational database
2. **SQLite** - Embedded, file-based database
3. **MySQL/MariaDB** - Alternative relational database
4. **MongoDB** - Document database
5. **In-memory JSON file** - Simplest possible option

## Decision

We will use PostgreSQL 16 Alpine as the primary data store.

Schema design:
- Single `books` table with UUID primary key
- Constraints for status (enum-like CHECK) and rating (range CHECK)
- Indexes on `status` and `genre` for filter performance
- Automatic timestamp for `date_added`
- Init script mounted as Docker entrypoint for zero-setup schema creation

## Consequences

### What Becomes Easier

- **Relational integrity**: Constraints enforce valid data (ratings 1-5, valid status values)
- **Rich queries**: Support for filtering, grouping, aggregations, and joins (if needed later)
- **ACID guarantees**: No data loss, consistent state
- **Scalability**: PostgreSQL handles 10,000+ books with ease
- **Tooling**: Excellent ecosystem (pgAdmin, psql, ORMs)
- **Performance**: Indexes make filtering by status/genre fast
- **Data persistence**: Named volume preserves data across container restarts
- **Production-ready**: Battle-tested, widely deployed

### What Becomes More Difficult

- **Setup complexity**: Requires Docker container vs. simple file
- **Resource usage**: PostgreSQL uses more memory than SQLite
- **Schema migrations**: Structural changes require migration scripts
- **Connection pooling**: Must manage connections properly in API

### Alternatives Considered

**SQLite**: Simpler, no server process, but:
- Poor concurrency under write load
- No network access (requires file mounting)
- Limited constraint types
- Less suitable for future scaling

**MongoDB**: Document flexibility, but:
- No schema enforcement (books could have invalid data)
- Aggregations more complex than SQL
- Overkill for simple relational data
- Less familiar to most developers

**JSON file**: Simplest option, but:
- No ACID guarantees
- No constraints or validation
- Poor performance at scale
- Race conditions with concurrent writes
- Completely inappropriate for production

### Schema Highlights

```sql
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    author VARCHAR(500) NOT NULL,
    status VARCHAR(20) DEFAULT 'want_to_read'
        CHECK(status IN ('want_to_read', 'reading', 'finished', 'abandoned')),
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    -- ... other fields
);

CREATE INDEX idx_books_status ON books(status);
CREATE INDEX idx_books_genre ON books(genre);
```

These indexes ensure fast filtering (e.g., "show all 'reading' books") and efficient statistics queries (e.g., "count books per genre").

### Mitigations

- Use connection pooling in API to manage connections efficiently
- Include `init.sql` script for automatic schema setup
- Use Alpine image to minimize container size (20MB vs 100MB+)
- Named volume ensures data survives `docker compose down`
- Health checks prevent API from starting before database is ready
