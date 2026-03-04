# ADR-0001: Docker Compose Multi-Container Architecture

## Status
Accepted

## Context

The application needs to integrate multiple technologies (web server, API, database, search engine) into a cohesive system that users can run with minimal setup. The PRD explicitly requires "zero manual setup" with a single `docker compose up` command.

We need a deployment approach that:
- Orchestrates multiple services with correct startup order
- Handles inter-service dependencies reliably
- Provides data persistence across restarts
- Works consistently across different development environments
- Requires no manual configuration or installation steps

## Decision

We will use Docker Compose with a four-service architecture:

1. **PostgreSQL** (postgres:16-alpine) - primary data store
2. **MeiliSearch** (getmeili/meilisearch:v1.6) - full-text search
3. **API** (custom Node.js Express) - business logic layer
4. **Frontend** (custom Nginx) - static file serving and API proxy

All services are defined in a single `docker-compose.yml` file with:
- Health checks for PostgreSQL and MeiliSearch
- `depends_on` with health conditions for reliable startup ordering
- Named volumes for data persistence (pgdata, msdata)
- Environment-based configuration (no .env files needed)
- Explicit port mappings for each service

## Consequences

### What Becomes Easier

- **Zero-friction onboarding**: New developers run one command to start everything
- **Consistent environments**: Docker ensures identical behavior across machines
- **Service isolation**: Each component runs in its own container with clear boundaries
- **Dependency management**: Health checks eliminate race conditions during startup
- **Data persistence**: Named volumes preserve data across container restarts
- **Clean teardown**: `docker compose down` stops everything cleanly

### What Becomes More Difficult

- **Resource usage**: Running 4 containers requires more RAM/CPU than a monolith
- **Debugging complexity**: Issues may span multiple containers/logs
- **Build time**: Initial setup takes longer than a simple script
- **Local development**: Making code changes requires container rebuilds (though volumes can mitigate this)
- **Network configuration**: Inter-service communication requires understanding Docker networking

### Mitigations

- Document clear `docker compose` commands for common tasks
- Use Alpine-based images to minimize container size
- Provide health check endpoints for debugging
- Use volume mounts for development to enable live reloading
- Keep service logs visible with `docker compose logs`
