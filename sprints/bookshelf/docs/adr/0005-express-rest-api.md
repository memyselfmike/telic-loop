# ADR-0005: Express REST API with Modular Routes

## Status
Accepted

## Context

The application needs a backend API to handle:
- CRUD operations for books
- Search query proxying to MeiliSearch
- Statistical aggregations from PostgreSQL
- Data validation and error handling
- Search index synchronization

Options considered:

1. **Express** - Minimal, flexible Node.js framework
2. **Fastify** - High-performance alternative to Express
3. **NestJS** - Full-featured TypeScript framework
4. **Koa** - Lightweight, modern middleware-based framework
5. **No framework** (raw Node.js http module)

## Decision

We will use Express 4.x with a modular route-based architecture.

Structure:
- `server.js` - App initialization, middleware, health checks
- `db.js` - PostgreSQL connection pool
- `search.js` - MeiliSearch client module
- `routes/books.js` - Book CRUD endpoints
- `routes/search.js` - Search endpoint
- `routes/stats.js` - Statistics endpoint

Patterns:
- RESTful endpoints (GET, POST, PUT, DELETE)
- Async/await for all database and search operations
- Fire-and-forget search sync (non-blocking)
- Proper HTTP status codes (200, 201, 204, 400, 404, 500)
- JSON request/response bodies
- CORS enabled for development (eliminated by nginx proxy in production)

## Consequences

### What Becomes Easier

- **Rapid development**: Express is minimal and unopinionated
- **Large ecosystem**: Extensive middleware and tooling available
- **Team familiarity**: Express is widely known and documented
- **Flexible architecture**: Easy to organize routes and middleware as needed
- **Debugging**: Simple request/response flow, easy to add logging
- **Testing**: Straightforward to test routes with supertest or similar

### What Becomes More Difficult

- **Type safety**: JavaScript lacks compile-time type checking (vs TypeScript/NestJS)
- **Performance ceiling**: Not as fast as Fastify or raw Node.js
- **Convention**: No enforced structure, team must establish patterns
- **Boilerplate**: Must manually set up error handling, validation, etc.

### Alternatives Considered

**Fastify**: Faster than Express but:
- Less familiar to most developers
- Smaller ecosystem
- Performance difference negligible for this app's scale

**NestJS**: Full-featured with TypeScript, but:
- Heavy framework for simple CRUD API
- Steeper learning curve
- Slower iteration for small team
- PRD doesn't require TypeScript

**No framework**: Maximum control, but:
- Manual routing implementation
- More boilerplate code
- Reinventing middleware patterns
- Not worth the complexity

### Key Design Decisions

**Modular Routes**: Each resource (books, search, stats) has its own route file for clear separation of concerns.

**Fire-and-Forget Search Sync**:
```javascript
search.addOrUpdate(book).catch(err =>
  console.error('[Search Sync] Error:', err)
);
```
This ensures API responses aren't blocked by search indexing. PostgreSQL is the source of truth; search sync failures are logged but don't fail the request.

**Connection Pooling**:
```javascript
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});
```
Reuses connections for better performance under load.

**Health Checks**: Root endpoint (`GET /`) tests database connectivity and returns service status.

**Graceful Shutdown**: SIGTERM handler closes database pool cleanly.

### Mitigations

- Establish clear route organization pattern from the start
- Use async/await consistently (no callback mixing)
- Add input validation for all user-provided data
- Return descriptive error messages with appropriate status codes
- Log errors but don't expose internal details to clients
- Consider adding TypeScript in future if type safety becomes critical
