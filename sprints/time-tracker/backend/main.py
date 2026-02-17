"""
Freelancer Time Tracker — FastAPI Application Entry Point

Port configuration (in priority order):
  1. --port CLI argument
  2. PORT environment variable
  3. Default: 8765 (avoids system port 8000 conflict)

Usage:
  python -m backend.main                  # port 8765
  python -m backend.main --port 9000      # port 9000
  PORT=9000 python -m backend.main        # port 9000
  uvicorn backend.main:app --port 9000    # port 9000 (direct uvicorn)
"""

import argparse
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.database import init_db
from backend.routes.entries import router as entries_router
from backend.routes.projects import router as projects_router
from backend.routes.reports import router as reports_router

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Freelancer Time Tracker",
        description="Track billable hours by project with real-time timer",
        version="1.0.0",
    )

    # ------------------------------------------------------------------
    # Initialise the database schema on startup (idempotent)
    # ------------------------------------------------------------------
    init_db()

    # ------------------------------------------------------------------
    # API routes — registered before static mount so /api/* takes priority
    # ------------------------------------------------------------------

    # Project management endpoints
    application.include_router(projects_router)

    # Timer and time entry endpoints
    application.include_router(entries_router)

    # Reports and CSV export endpoints
    application.include_router(reports_router)

    # ------------------------------------------------------------------
    # Static file serving — mounts the frontend/ directory at root
    # ------------------------------------------------------------------
    frontend_dir = Path(__file__).parent.parent / "frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)

    application.mount(
        "/",
        StaticFiles(directory=str(frontend_dir), html=True),
        name="frontend",
    )

    return application


# Module-level app instance (used by uvicorn and pytest ASGI transport)
app = create_app()


# ---------------------------------------------------------------------------
# CLI entry point — `python -m backend.main`
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freelancer Time Tracker dev server")
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to listen on (overrides PORT env var, default 8765)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development mode)",
    )
    return parser.parse_args()


def main() -> None:
    import uvicorn

    args = _parse_args()

    # Port resolution: CLI arg > PORT env var > 8765 default
    port: int
    if args.port is not None:
        port = args.port
    elif "PORT" in os.environ:
        port = int(os.environ["PORT"])
    else:
        port = 8765

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
