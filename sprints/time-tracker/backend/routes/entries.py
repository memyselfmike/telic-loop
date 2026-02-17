"""
Freelancer Time Tracker — Timer & Time Entry API Endpoints

Routes:
  GET    /api/timer              — Return running timer with elapsed_seconds, or null
  POST   /api/timer/start        — Start a new timer (auto-stops any running timer first)
  POST   /api/timer/stop         — Stop the running timer, return completed entry

  GET    /api/entries            — List entries (?date=YYYY-MM-DD or ?from=DATE&to=DATE)
  POST   /api/entries            — Create a manual time entry (start + end required)
  PUT    /api/entries/{id}       — Update an entry (partial fields accepted)
  DELETE /api/entries/{id}       — Delete an entry (204 on success)
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, Response

from backend.database import get_db
from backend.models import (
    EntryCreate,
    EntryResponse,
    EntryUpdate,
    TimerResponse,
    TimerStartRequest,
)

router = APIRouter(tags=["timer", "entries"])


# ---------------------------------------------------------------------------
# SQL helper — entry + project JOIN
# ---------------------------------------------------------------------------

_ENTRY_JOIN = """
    SELECT
        te.*,
        p.name  AS project_name,
        p.color AS project_color
    FROM time_entries te
    JOIN projects p ON p.id = te.project_id
"""


def _get_entry_or_404(entry_id: int, db) -> object:
    """Fetch an entry row (with project join) by ID; raise 404 if not found."""
    row = db.execute(
        f"{_ENTRY_JOIN} WHERE te.id = ?",  # noqa: S608
        (entry_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return row


def _get_running_timer(db) -> Optional[object]:
    """Return the currently running time entry row (end_time IS NULL), or None."""
    return db.execute(
        f"{_ENTRY_JOIN} WHERE te.end_time IS NULL ORDER BY te.start_time DESC LIMIT 1"  # noqa: S608
    ).fetchone()


def _stop_entry(entry_id: int, now: datetime, db) -> None:
    """Set end_time and compute duration_seconds for an entry that is still running."""
    now_iso = now.replace(microsecond=0).isoformat()
    db.execute(
        """
        UPDATE time_entries
           SET end_time          = ?,
               duration_seconds  = CAST(
                   (julianday(?) - julianday(start_time)) * 86400 AS INTEGER
               ),
               updated_at        = datetime('now')
         WHERE id = ?
        """,
        (now_iso, now_iso, entry_id),
    )


# ---------------------------------------------------------------------------
# GET /api/timer — current running timer
# ---------------------------------------------------------------------------

@router.get(
    "/api/timer",
    summary="Get running timer",
    responses={
        200: {"description": "Running timer or null if none"},
    },
)
def get_timer() -> JSONResponse:
    """
    Return the currently running timer entry with computed **elapsed_seconds**,
    or ``null`` if no timer is running.

    The frontend uses ``elapsed_seconds`` as the authoritative baseline so the
    displayed time is always correct regardless of when the page was loaded.
    """
    with get_db() as db:
        row = _get_running_timer(db)

    if row is None:
        return JSONResponse(content=None)

    timer = TimerResponse.from_row(row)
    return JSONResponse(content=timer.model_dump())


# ---------------------------------------------------------------------------
# POST /api/timer/start — start a new timer
# ---------------------------------------------------------------------------

@router.post(
    "/api/timer/start",
    status_code=201,
    summary="Start timer",
    responses={
        201: {"description": "Timer started successfully"},
        404: {"description": "Project not found"},
    },
)
def start_timer(body: TimerStartRequest) -> JSONResponse:
    """
    Start a new running timer for the given project.

    If another timer is already running it is automatically stopped first
    (auto-switch behaviour — only one timer can run at a time).

    Responds with **201 Created** and the new timer details including
    ``elapsed_seconds`` (always 0 or very small on a fresh start).
    """
    now = datetime.now()
    now_iso = now.replace(microsecond=0).isoformat()

    with get_db() as db:
        # Verify the project exists and is not archived
        project_row = db.execute(
            "SELECT * FROM projects WHERE id = ?", (body.project_id,)
        ).fetchone()
        if project_row is None:
            raise HTTPException(status_code=404, detail="Project not found")
        if project_row["archived"]:
            raise HTTPException(
                status_code=409,
                detail="Cannot start timer for an archived project",
            )

        # Auto-stop any currently running timer
        running = _get_running_timer(db)
        if running is not None:
            _stop_entry(running["id"], now, db)

        # Create the new running entry (end_time NULL = timer is live)
        cursor = db.execute(
            """
            INSERT INTO time_entries (project_id, description, start_time)
            VALUES (?, ?, ?)
            """,
            (body.project_id, body.description, now_iso),
        )
        new_id = cursor.lastrowid

        # Fetch back with project join
        row = db.execute(
            f"{_ENTRY_JOIN} WHERE te.id = ?",  # noqa: S608
            (new_id,),
        ).fetchone()

    timer = TimerResponse.from_row(row, now=now)
    return JSONResponse(content=timer.model_dump(), status_code=201)


# ---------------------------------------------------------------------------
# POST /api/timer/stop — stop the running timer
# ---------------------------------------------------------------------------

@router.post(
    "/api/timer/stop",
    summary="Stop running timer",
    responses={
        200: {"description": "Timer stopped, completed entry returned"},
        404: {"description": "No running timer"},
    },
)
def stop_timer() -> JSONResponse:
    """
    Stop the currently running timer.

    Sets ``end_time`` to now and computes ``duration_seconds``.
    Returns the completed time entry (as an **EntryResponse**).

    Responds with **404 Not Found** if no timer is currently running.
    """
    now = datetime.now()

    with get_db() as db:
        running = _get_running_timer(db)
        if running is None:
            raise HTTPException(status_code=404, detail="No running timer")

        _stop_entry(running["id"], now, db)

        # Fetch the updated entry with project join
        row = _get_entry_or_404(running["id"], db)

    entry = EntryResponse.from_row(row)
    return JSONResponse(content=entry.model_dump())


# ---------------------------------------------------------------------------
# GET /api/entries — list time entries
# ---------------------------------------------------------------------------

@router.get(
    "/api/entries",
    response_model=list[EntryResponse],
    summary="List time entries",
)
def list_entries(
    date: Optional[str] = Query(
        default=None,
        description=(
            "Filter to a single day (YYYY-MM-DD). "
            "Matches entries whose start_time falls on that calendar date."
        ),
        examples=["2026-02-17"],
    ),
    from_date: Optional[str] = Query(
        default=None,
        alias="from",
        description="Range start date (YYYY-MM-DD, inclusive)",
        examples=["2026-02-10"],
    ),
    to_date: Optional[str] = Query(
        default=None,
        alias="to",
        description="Range end date (YYYY-MM-DD, inclusive)",
        examples=["2026-02-17"],
    ),
) -> list[EntryResponse]:
    """
    Return a list of time entries, newest first.

    - **?date=YYYY-MM-DD** — entries whose ``start_time`` falls on that date
    - **?from=YYYY-MM-DD&to=YYYY-MM-DD** — entries in a date range (both inclusive)
    - *(no filter)* — all entries

    Each entry includes ``project_name`` and ``project_color`` joined from
    the projects table.
    """
    query = f"{_ENTRY_JOIN}"  # noqa: S608
    params: list = []

    if date is not None:
        # SQLite stores start_time as ISO 8601 text; DATE() extracts the date part
        query += " WHERE DATE(te.start_time) = ?"
        params.append(date)
    elif from_date is not None or to_date is not None:
        conditions = []
        if from_date is not None:
            conditions.append("DATE(te.start_time) >= ?")
            params.append(from_date)
        if to_date is not None:
            conditions.append("DATE(te.start_time) <= ?")
            params.append(to_date)
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY te.start_time DESC"

    with get_db() as db:
        rows = db.execute(query, params).fetchall()

    return [EntryResponse.from_row(row) for row in rows]


# ---------------------------------------------------------------------------
# POST /api/entries — create a manual time entry
# ---------------------------------------------------------------------------

@router.post(
    "/api/entries",
    response_model=EntryResponse,
    status_code=201,
    summary="Create manual time entry",
)
def create_entry(body: EntryCreate) -> EntryResponse:
    """
    Create a completed time entry manually (both start and end times required).

    ``duration_seconds`` is computed automatically from the provided times.
    Useful for backfilling time that was not tracked with the live timer.

    Responds with **201 Created** and the full entry including project details.
    """
    with get_db() as db:
        # Verify the project exists
        project_row = db.execute(
            "SELECT id FROM projects WHERE id = ?", (body.project_id,)
        ).fetchone()
        if project_row is None:
            raise HTTPException(status_code=404, detail="Project not found")

        # Compute duration from the provided times
        start = datetime.fromisoformat(body.start_time)
        end = datetime.fromisoformat(body.end_time)
        duration_seconds = max(0, int((end - start).total_seconds()))

        cursor = db.execute(
            """
            INSERT INTO time_entries
                (project_id, description, start_time, end_time, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                body.project_id,
                body.description,
                body.start_time,
                body.end_time,
                duration_seconds,
            ),
        )
        new_id = cursor.lastrowid

        row = _get_entry_or_404(new_id, db)

    return EntryResponse.from_row(row)


# ---------------------------------------------------------------------------
# PUT /api/entries/{id} — update an entry
# ---------------------------------------------------------------------------

@router.put(
    "/api/entries/{entry_id}",
    response_model=EntryResponse,
    summary="Update time entry",
)
def update_entry(entry_id: int, body: EntryUpdate) -> EntryResponse:
    """
    Partially update a time entry.

    Only the supplied fields are changed; omitted fields retain their current
    values. If ``start_time`` or ``end_time`` are updated, ``duration_seconds``
    is recomputed automatically (if the entry has both times set after the update).

    Responds with **404 Not Found** if the entry does not exist.
    """
    updates = body.model_dump(exclude_none=True)

    with get_db() as db:
        # Ensure the entry exists
        existing_row = _get_entry_or_404(entry_id, db)
        existing = dict(existing_row)

        if not updates:
            return EntryResponse.from_row(existing_row)

        # Build the SET clause from supplied fields only
        set_parts = [f"{col} = ?" for col in updates]
        values = list(updates.values())

        # Recompute duration_seconds if either time boundary changed and the
        # entry is completed (has both start and end times after the merge).
        merged_start = updates.get("start_time", existing.get("start_time"))
        merged_end = updates.get("end_time", existing.get("end_time"))

        if merged_start and merged_end:
            start_dt = datetime.fromisoformat(merged_start)
            end_dt = datetime.fromisoformat(merged_end)
            new_duration = max(0, int((end_dt - start_dt).total_seconds()))
            if "duration_seconds" not in updates:
                set_parts.append("duration_seconds = ?")
                values.append(new_duration)

        set_parts.append("updated_at = datetime('now')")
        set_clause = ", ".join(set_parts)
        values.append(entry_id)

        db.execute(
            f"UPDATE time_entries SET {set_clause} WHERE id = ?",  # noqa: S608
            values,
        )
        row = _get_entry_or_404(entry_id, db)

    return EntryResponse.from_row(row)


# ---------------------------------------------------------------------------
# DELETE /api/entries/{id} — delete an entry
# ---------------------------------------------------------------------------

@router.delete(
    "/api/entries/{entry_id}",
    status_code=204,
    summary="Delete time entry",
    responses={
        204: {"description": "Entry deleted successfully"},
        404: {"description": "Time entry not found"},
    },
)
def delete_entry(entry_id: int) -> Response:
    """
    Delete a time entry permanently.

    Returns **204 No Content** on success, **404 Not Found** if the entry
    does not exist.
    """
    with get_db() as db:
        # Verify existence first
        _get_entry_or_404(entry_id, db)
        db.execute("DELETE FROM time_entries WHERE id = ?", (entry_id,))

    return Response(status_code=204)
