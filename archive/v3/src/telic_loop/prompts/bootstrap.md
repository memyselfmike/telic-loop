# Service Bootstrap

You are bootstrapping a greenfield project. Your job is to create the MINIMUM
viable project skeleton that starts the registered services. Do NOT implement
features — that happens in the value loop.

## Context

- **Project Directory**: {PROJECT_DIR}
- **Sprint Context**: {SPRINT_CONTEXT}
- **Registered Services**: {SERVICES}

## PRD (for reference — do NOT implement features)
{PRD}

## Task

Create the minimum files needed for the services listed above to start and
respond to health checks. Specifically:

1. **Initialize the project** — package.json (or equivalent), install deps
2. **Create entry point** — minimal server that starts on the correct port
3. **Database setup** — if a database is specified, create schema initialization
4. **Health endpoint** — ensure the health check URL returns a 200 response
5. **Start the server** — verify it actually runs and responds

## Rules

- Create ONLY skeleton/scaffold code — no feature implementation
- The server must START and RESPOND to the health check URL
- Install all dependencies listed in the PRD (npm install, pip install, etc.)
- Include seed data if the PRD specifies it in the schema
- Do NOT create frontend views, API routes (beyond health), or business logic
- Do NOT call report_task_complete — this is infrastructure, not a task
- Keep total files under 5 — this is a scaffold, not the application
- Start the server process in the background after verifying it works
- If the health check URL is an API endpoint (e.g. /api/dashboard/summary),
  create a minimal route that returns a valid JSON response (e.g. empty object)
  so the health check passes
