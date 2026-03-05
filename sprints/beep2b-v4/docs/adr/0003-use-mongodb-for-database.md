# ADR-0003: Use MongoDB for Database

## Status
Accepted

## Context
We needed to choose a database for storing CMS content including blog posts, categories, testimonials, media metadata, and form submissions. Requirements included:
- Support for flexible, evolving content schemas (blog posts may add new fields over time)
- Integration with Payload CMS
- Simple deployment and maintenance
- Good performance for read-heavy workloads (marketing sites have more reads than writes)
- Reliable data persistence

Candidates considered:
- **MongoDB** — Document-oriented NoSQL database
- **PostgreSQL** — Relational database with JSON support
- **MySQL** — Popular relational database
- **SQLite** — Embedded file-based database

## Decision
We chose **MongoDB 7** as the database.

Key factors:
1. **Payload CMS support** — Payload has first-class MongoDB support via `@payloadcms/db-mongodb` with Mongoose ODM
2. **Schema flexibility** — Blog posts, testimonials, and form submissions have varying structures (rich text, nested categories, optional fields)
3. **Document model fit** — CMS content naturally maps to documents (posts are self-contained with embedded metadata)
4. **Simple deployment** — Official MongoDB Docker image requires zero configuration
5. **No migrations** — Adding new fields to collections doesn't require migration scripts
6. **Query performance** — Automatic indexing on common fields (slug, date, categories) via Payload

## Consequences

### Positive
- Adding new fields to blog posts or other collections requires no database migrations
- JSON-like document structure matches JavaScript/TypeScript data models naturally
- Payload's Mongoose adapter handles all database interactions transparently
- Official MongoDB Docker image makes local development identical to production
- Rich query capabilities via Mongoose (filtering, sorting, pagination, population)

### Negative
- No ACID guarantees for complex multi-document transactions (though not needed for this use case)
- Larger disk footprint compared to relational databases for small datasets
- Less strict schema enforcement compared to SQL databases (mitigated by Payload's schema validation)
- Requires learning MongoDB query syntax for complex operations

### Mitigations
- Payload CMS enforces schema validation at the application layer, ensuring data consistency
- For this marketing website, transactions are not required (each blog post, testimonial, or form submission is independent)
- MongoDB Atlas provides managed hosting for production if self-hosting becomes burdensome
- Named Docker volume (`beep2b-mongodata`) ensures data persistence across container restarts
