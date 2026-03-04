# Docker Environment Setup

You are setting up Docker management scripts so that ALL agents in the sprint use a consistent, standardized way to manage containers.

## Context

- **Project Directory**: {PROJECT_DIR}
- **Sprint Directory**: {SPRINT_DIR}
- **Docker Configuration**: {DOCKER_CONFIG}
- **Sprint Context**: {SPRINT_CONTEXT}

## Task

Generate Docker management scripts in `{PROJECT_DIR}/.telic-docker/`. These scripts will be used by every agent (Builder, Evaluator, QC) throughout the sprint.

### Scripts to Create

#### 1. `docker-up.sh` — Start all containers

- Run `docker compose up -d` (use `-f <file>` if compose file is not at project root)
- Wait for containers to be healthy (poll with `docker compose ps` or health checks)
- Print service URLs when ready (e.g., "App: http://localhost:3000")
- Must be idempotent — safe to run when containers are already running
- Timeout after 120 seconds if services fail to start

#### 2. `docker-down.sh` — Stop all containers

- Run `docker compose down`
- Confirm containers are stopped
- Do NOT remove volumes by default (preserve data between sessions)

#### 3. `docker-health.sh` — Health check all services

- Check each service's exposed port is reachable (use `curl` or `nc`)
- Check each service's health endpoint if available
- Exit 0 if ALL services are healthy, exit 1 if ANY are unhealthy
- Print status for each service: `[OK] app:3000` or `[FAIL] db:5432`

#### 4. `docker-logs.sh` — Tail container logs

- Accept optional service name as first argument
- Default (no argument): tail all services
- Run `docker compose logs --tail=50 -f [service]`

### Requirements

- All scripts use `#!/usr/bin/env bash` shebang
- All scripts use `set -euo pipefail`
- Use `docker compose` (v2 CLI plugin syntax), NOT the legacy `docker-compose` command
- Scripts must work on Windows (Git Bash) and Linux/macOS
- Make scripts executable with `chmod +x`
- Use the compose file path from Docker Configuration if one exists

### Docker Compose File

If no `docker-compose.yml` (or `compose.yml`) exists in the project directory:
1. Read the Sprint Context to understand what services the project needs
2. Generate an appropriate `docker-compose.yml` at the project root
3. Include health checks in the compose file where possible
4. Expose ports that match what the Sprint Context services expect

If a compose file already exists, do NOT modify it — generate scripts that work with it.

### README

Create `.telic-docker/README.md` explaining what each script does and how agents should use them.

## Important

- Do NOT call `report_task_complete` — this is infrastructure setup, not a sprint task
- Do NOT start the containers — just create the scripts
- Do NOT install any packages or dependencies
