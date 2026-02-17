import os
import sys
from pathlib import Path

# Ensure backend directory is on path when run directly
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import uvicorn

from database import init_db
from routes.recipes import router as recipes_router
from routes.meals import router as meals_router
from routes.shopping import router as shopping_router

PORT = int(os.environ.get("PORT", 8000))

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app = FastAPI(title="Recipe Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await init_db()


app.include_router(recipes_router, prefix="/api")
app.include_router(meals_router, prefix="/api")
app.include_router(shopping_router, prefix="/api")


@app.get("/")
async def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Recipe Manager API — frontend not found"}


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
