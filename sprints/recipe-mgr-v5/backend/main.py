"""
Recipe Manager with Meal Planner - FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from backend.database import init_database
from backend.routes import recipes, meals, shopping


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle"""
    # Startup: initialize database
    init_database()
    yield
    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title="Recipe Manager with Meal Planner",
    description="Full-stack web app for recipe collection, meal planning, and shopping list generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# Register API routers
app.include_router(recipes.router)
app.include_router(meals.router)
app.include_router(shopping.router)


# Mount static files (frontend) at root - must be LAST
# StaticFiles with html=True serves index.html for unknown paths
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    # Note: Static file mount must be registered AFTER all API routes
    # to prevent it from catching API paths
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")
