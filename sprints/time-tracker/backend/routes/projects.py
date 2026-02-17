"""
Freelancer Time Tracker — Project API Endpoints

Routes:
  GET    /api/projects           — List all projects (?active=true excludes archived)
  POST   /api/projects           — Create a new project (returns 201)
  GET    /api/projects/{id}      — Get a single project by ID (404 if missing)
  PUT    /api/projects/{id}      — Update a project (partial fields accepted)
  DELETE /api/projects/{id}      — Delete a project (409 if has entries, 204 on success)
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.database import get_db
from backend.models import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_project_or_404(project_id: int, db) -> object:
    """Fetch a project row by ID; raise 404 if not found."""
    row = db.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return row


# ---------------------------------------------------------------------------
# GET /api/projects
# ---------------------------------------------------------------------------

@router.get("", response_model=list[ProjectResponse], summary="List projects")
def list_projects(
    active: Optional[bool] = Query(
        default=None,
        description=(
            "When true, return only non-archived projects. "
            "When false, return only archived projects. "
            "Omit to return all projects."
        ),
    ),
) -> list[ProjectResponse]:
    """
    Return a list of projects, optionally filtered by archive status.

    - **active=true** — only projects where archived = 0 (active projects)
    - **active=false** — only archived projects
    - *(omitted)* — all projects regardless of archive status
    """
    with get_db() as db:
        if active is None:
            rows = db.execute(
                "SELECT * FROM projects ORDER BY name ASC"
            ).fetchall()
        elif active:
            rows = db.execute(
                "SELECT * FROM projects WHERE archived = 0 ORDER BY name ASC"
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM projects WHERE archived = 1 ORDER BY name ASC"
            ).fetchall()

    return [ProjectResponse.from_row(row) for row in rows]


# ---------------------------------------------------------------------------
# POST /api/projects
# ---------------------------------------------------------------------------

@router.post("", response_model=ProjectResponse, status_code=201, summary="Create project")
def create_project(body: ProjectCreate) -> ProjectResponse:
    """
    Create a new project.

    Returns the newly created project with its auto-generated ID and timestamps.
    Responds with **201 Created**.
    """
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO projects (name, client_name, hourly_rate, color)
            VALUES (?, ?, ?, ?)
            """,
            (body.name, body.client_name, body.hourly_rate, body.color),
        )
        project_id = cursor.lastrowid
        row = db.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

    return ProjectResponse.from_row(row)


# ---------------------------------------------------------------------------
# GET /api/projects/{id}
# ---------------------------------------------------------------------------

@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project")
def get_project(project_id: int) -> ProjectResponse:
    """
    Retrieve a single project by its ID.

    Responds with **404 Not Found** if the project does not exist.
    """
    with get_db() as db:
        row = _get_project_or_404(project_id, db)
    return ProjectResponse.from_row(row)


# ---------------------------------------------------------------------------
# PUT /api/projects/{id}
# ---------------------------------------------------------------------------

@router.put("/{project_id}", response_model=ProjectResponse, summary="Update project")
def update_project(project_id: int, body: ProjectUpdate) -> ProjectResponse:
    """
    Partially update a project.

    Only the fields present in the request body are updated; omitted fields
    retain their current values. Responds with **404 Not Found** if the project
    does not exist.
    """
    # Build the SET clause dynamically from supplied fields only
    updates = body.model_dump(exclude_none=True)
    if not updates:
        # Nothing to update — return the current state
        with get_db() as db:
            row = _get_project_or_404(project_id, db)
        return ProjectResponse.from_row(row)

    # Convert Python bool to SQLite integer for the archived column
    if "archived" in updates:
        updates["archived"] = 1 if updates["archived"] else 0

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    set_clause += ", updated_at = datetime('now')"
    values = list(updates.values()) + [project_id]

    with get_db() as db:
        # Verify the project exists before attempting the update
        _get_project_or_404(project_id, db)

        db.execute(
            f"UPDATE projects SET {set_clause} WHERE id = ?",  # noqa: S608
            values,
        )
        row = db.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

    return ProjectResponse.from_row(row)


# ---------------------------------------------------------------------------
# DELETE /api/projects/{id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{project_id}",
    status_code=204,
    summary="Delete project",
    responses={
        204: {"description": "Project deleted successfully"},
        404: {"description": "Project not found"},
        409: {"description": "Project has time entries and cannot be deleted"},
    },
)
def delete_project(project_id: int) -> None:
    """
    Delete a project.

    - Returns **204 No Content** on success.
    - Returns **404 Not Found** if the project does not exist.
    - Returns **409 Conflict** if the project has associated time entries
      (delete the entries first, or archive the project instead).
    """
    with get_db() as db:
        # Verify project exists
        _get_project_or_404(project_id, db)

        # Check for associated time entries
        entry_count = db.execute(
            "SELECT COUNT(*) FROM time_entries WHERE project_id = ?",
            (project_id,),
        ).fetchone()[0]

        if entry_count > 0:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot delete project: it has {entry_count} time "
                    "entr" + ("y" if entry_count == 1 else "ies") + ". "
                    "Archive the project instead, or delete its entries first."
                ),
            )

        db.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    # 204 No Content — return None (FastAPI will send an empty body)
    return None
