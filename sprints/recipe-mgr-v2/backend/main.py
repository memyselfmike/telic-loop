import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from database import init_db
from routes.recipes import router as recipes_router
from routes.meals import router as meals_router
from routes.shopping import router as shopping_router

app = FastAPI(title="Recipe Manager API")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Include routers
app.include_router(recipes_router)
app.include_router(meals_router)
app.include_router(shopping_router)

# Mount frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/")
    def read_root():
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"status": "ok", "message": "Recipe Manager API"}
else:
    @app.get("/")
    def read_root():
        return {"status": "ok", "message": "Recipe Manager API"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
