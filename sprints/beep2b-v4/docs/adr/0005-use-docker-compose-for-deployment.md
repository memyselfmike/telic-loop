# ADR-0005: Use Docker Compose for Orchestration

## Status
Accepted

## Context
We needed to deploy three services (frontend, CMS, database) in a coordinated manner for both local development and production. Requirements included:
- Single-command startup for the entire stack
- Service dependency management (CMS needs database, frontend needs CMS)
- Data persistence across restarts
- Development environment parity with production
- Easy onboarding for new developers

Candidates considered:
- **Docker Compose** — Multi-container orchestration tool
- **Kubernetes** — Container orchestration platform
- **Manual Docker commands** — Individual `docker run` commands
- **Serverless deployment** — Separate deployments to Vercel (frontend), Railway (CMS), MongoDB Atlas
- **Single monolith** — Combine all services in one Node.js application

## Decision
We chose **Docker Compose** for local development and initial production deployment.

Key factors:
1. **Simplicity** — Single `docker compose up` command starts all three services with correct dependencies
2. **Local development parity** — Development and production use the same orchestration configuration
3. **Declarative configuration** — Service dependencies, health checks, environment variables, and volumes defined in one YAML file
4. **Lower resource overhead** — No orchestration layer overhead (unlike Kubernetes)
5. **Easy debugging** — Logs, health checks, and service dependencies clearly visible in `docker-compose.yml`
6. **Zero configuration** — Works out-of-the-box on any machine with Docker installed

## Consequences

### Positive
- New developers can start the entire stack with one command (`docker compose up`)
- Development environment exactly matches production (same containers, same configuration)
- Service dependencies automatically handled (CMS waits for MongoDB, frontend waits for CMS)
- MongoDB data persists across restarts via named volume
- Hot module reloading works via volume mounts (`./frontend:/app`, `./cms:/app`)
- Easy to add new services (e.g., Redis cache, email service) by adding to `docker-compose.yml`

### Negative
- Not horizontally scalable (cannot easily run multiple CMS instances for load balancing)
- Single point of failure (one server hosts all services)
- Less sophisticated health checking compared to Kubernetes liveness/readiness probes
- Manual deployment process (no CI/CD automation built-in)
- Resource limits not enforced (services can consume all available memory/CPU)

### Mitigations
- For horizontal scaling, can migrate to Kubernetes or Docker Swarm if traffic grows beyond single-server capacity
- For high availability, can use managed services (MongoDB Atlas for database, Vercel for frontend, Railway for CMS)
- Health checks defined for MongoDB (`mongosh --eval "db.adminCommand('ping')"`)
- Can add CI/CD later with GitHub Actions or GitLab CI to automate deployment
- Resource limits can be added to `docker-compose.yml` if needed (`deploy.resources.limits`)

### Future Migration Path
If the site outgrows Docker Compose:
1. **Frontend** → Deploy static build to CDN (Netlify, Vercel, Cloudflare Pages)
2. **CMS** → Deploy to Node.js hosting (Railway, Heroku, DigitalOcean App Platform)
3. **Database** → Migrate to managed MongoDB (MongoDB Atlas)
4. **Orchestration** → Migrate to Kubernetes if multi-region or high availability is required
