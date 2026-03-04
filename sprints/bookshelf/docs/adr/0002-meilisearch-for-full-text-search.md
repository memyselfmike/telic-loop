# ADR-0002: MeiliSearch for Full-Text Search

## Status
Accepted

## Context

The PRD requires "instant full-text search powered by a dedicated search engine — not just SQL LIKE queries." Users need to search across book titles, authors, genres, and notes with features like typo tolerance and relevance ranking.

Options considered:

1. **PostgreSQL LIKE/ILIKE queries** - Simple, no additional service
2. **PostgreSQL Full-Text Search (tsvector)** - Built-in, more powerful than LIKE
3. **Elasticsearch** - Mature, feature-rich, widely adopted
4. **MeiliSearch** - Lightweight, instant, developer-friendly

## Decision

We will use MeiliSearch v1.6 as a dedicated search service.

MeiliSearch provides:
- Sub-50ms search response times
- Typo tolerance out of the box ("harry poter" → "Harry Potter")
- Relevance ranking with sensible defaults
- Simple REST API (no complex query DSL)
- Minimal configuration required
- Lightweight resource footprint
- Easy Docker integration

The API will sync books to MeiliSearch asynchronously after PostgreSQL writes using a fire-and-forget pattern:
- PostgreSQL remains the source of truth
- Search index updates are non-blocking
- Sync errors are logged but don't fail user requests

## Consequences

### What Becomes Easier

- **Excellent search UX**: Typo tolerance, instant results, relevance ranking
- **Simple integration**: REST API requires minimal client code
- **Fast development**: No complex indexing configuration needed
- **Better performance**: Search queries don't impact database
- **User delight**: Search feels "instant" compared to SQL queries

### What Becomes More Difficult

- **Additional service**: One more container to run and monitor
- **Data synchronization**: Must keep search index in sync with database
- **Eventual consistency**: Brief lag between DB write and search availability
- **Debugging complexity**: Search issues require checking MeiliSearch logs
- **Operational overhead**: Another service to understand and maintain

### Alternatives Considered

**PostgreSQL LIKE queries**: Would fail PRD requirement for "dedicated search engine" and wouldn't provide typo tolerance or relevance ranking.

**PostgreSQL Full-Text Search**: More powerful than LIKE but still limited compared to dedicated search engines. Requires complex tsvector column maintenance and doesn't provide typo tolerance.

**Elasticsearch**: More powerful but significantly heavier (600MB+ vs 50MB for MeiliSearch). Requires complex DSL for queries and extensive configuration. Overkill for this use case.

### Mitigations

- Implement retry logic in MeiliSearch initialization
- Log all search sync errors for visibility
- Use fire-and-forget async pattern to avoid blocking API responses
- Configure searchable and filterable attributes on startup
- Document search limitations (eventual consistency) in architecture docs
