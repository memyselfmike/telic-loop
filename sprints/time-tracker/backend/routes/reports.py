"""
Freelancer Time Tracker — Reports / Timesheet API Endpoints

Routes:
  GET  /api/reports/timesheet      — JSON timesheet grouped by date with totals
  GET  /api/reports/timesheet/csv  — Downloadable CSV with date/project/hours/amount
"""

import csv
import io
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from backend.database import get_db

router = APIRouter(tags=["reports"])


# ---------------------------------------------------------------------------
# SQL helper — fetch entries with project details for a date range
# ---------------------------------------------------------------------------

_REPORT_SQL = """
    SELECT
        DATE(te.start_time)  AS entry_date,
        te.id                AS entry_id,
        te.description,
        te.start_time,
        te.end_time,
        te.duration_seconds,
        p.id                 AS project_id,
        p.name               AS project_name,
        p.client_name,
        p.hourly_rate,
        p.color              AS project_color
    FROM time_entries te
    JOIN projects p ON p.id = te.project_id
    WHERE te.end_time IS NOT NULL
      AND te.duration_seconds IS NOT NULL
"""


def _fetch_report_rows(from_date: str, to_date: str, project_id: Optional[int]):
    """
    Query completed time entries within [from_date, to_date], optionally
    filtered by project_id. Returns raw sqlite3.Row objects sorted by date
    then start_time.
    """
    query = _REPORT_SQL
    params: list[Any] = []

    query += " AND DATE(te.start_time) >= ?"
    params.append(from_date)

    query += " AND DATE(te.start_time) <= ?"
    params.append(to_date)

    if project_id is not None:
        query += " AND te.project_id = ?"
        params.append(project_id)

    query += " ORDER BY entry_date ASC, te.start_time ASC"

    with get_db() as db:
        rows = db.execute(query, params).fetchall()

    return rows


def _seconds_to_hours(seconds: int) -> float:
    """Convert duration in seconds to hours, rounded to 2 decimal places."""
    return round(seconds / 3600, 2)


def _build_timesheet(rows) -> dict:
    """
    Transform raw DB rows into a structured timesheet response:
    {
      "from": "YYYY-MM-DD",
      "to": "YYYY-MM-DD",
      "by_date": [
        {
          "date": "YYYY-MM-DD",
          "entries": [
            {
              "entry_id": int,
              "project_id": int,
              "project_name": str,
              "client_name": str,
              "hourly_rate": float,
              "project_color": str,
              "description": str,
              "start_time": str,
              "end_time": str,
              "duration_seconds": int,
              "hours": float,
              "amount": float
            }
          ],
          "daily_hours": float,
          "daily_amount": float
        }
      ],
      "grand_total_hours": float,
      "grand_total_amount": float,
      "entry_count": int
    }
    """
    # Group entries by date (preserving order — rows are already sorted by date ASC)
    by_date: dict[str, list[dict]] = {}
    for row in rows:
        d = row["entry_date"]
        if d not in by_date:
            by_date[d] = []

        hours = _seconds_to_hours(row["duration_seconds"])
        amount = round(hours * row["hourly_rate"], 2)

        by_date[d].append(
            {
                "entry_id": row["entry_id"],
                "project_id": row["project_id"],
                "project_name": row["project_name"],
                "client_name": row["client_name"],
                "hourly_rate": row["hourly_rate"],
                "project_color": row["project_color"],
                "description": row["description"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "duration_seconds": row["duration_seconds"],
                "hours": hours,
                "amount": amount,
            }
        )

    # Build per-day summaries
    date_groups = []
    grand_hours = 0.0
    grand_amount = 0.0

    for date_str, entries in by_date.items():
        daily_hours = round(sum(e["hours"] for e in entries), 2)
        daily_amount = round(sum(e["amount"] for e in entries), 2)
        grand_hours += daily_hours
        grand_amount += daily_amount

        date_groups.append(
            {
                "date": date_str,
                "entries": entries,
                "daily_hours": daily_hours,
                "daily_amount": daily_amount,
            }
        )

    return {
        "by_date": date_groups,
        "grand_total_hours": round(grand_hours, 2),
        "grand_total_amount": round(grand_amount, 2),
        "entry_count": len(rows),
    }


# ---------------------------------------------------------------------------
# GET /api/reports/timesheet — JSON timesheet
# ---------------------------------------------------------------------------


@router.get(
    "/api/reports/timesheet",
    summary="Generate timesheet (JSON)",
    responses={
        200: {"description": "Timesheet grouped by date with daily and grand totals"},
        400: {"description": "Invalid date parameters"},
    },
)
def get_timesheet(
    from_date: str = Query(
        alias="from",
        description="Start date (YYYY-MM-DD, inclusive)",
        examples=["2026-02-10"],
    ),
    to_date: str = Query(
        alias="to",
        description="End date (YYYY-MM-DD, inclusive)",
        examples=["2026-02-17"],
    ),
    project_id: Optional[int] = Query(
        default=None,
        description="Filter to a single project by ID",
    ),
) -> JSONResponse:
    """
    Return a timesheet for the given date range, grouped by calendar date.

    Each entry includes:
    - ``project_name``, ``client_name``, ``hourly_rate``
    - ``hours`` (duration_seconds / 3600, 2 d.p.)
    - ``amount`` (hours × hourly_rate, 2 d.p.)

    Daily subtotals (``daily_hours``, ``daily_amount``) and grand totals
    (``grand_total_hours``, ``grand_total_amount``) are included.

    Only **completed** entries (where end_time is set) are included.
    Running timers are excluded.
    """
    # Validate date format
    try:
        from datetime import date as date_type
        date_type.fromisoformat(from_date)
        date_type.fromisoformat(to_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD.",
        )

    if from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="'from' date must be on or before 'to' date.",
        )

    rows = _fetch_report_rows(from_date, to_date, project_id)
    report = _build_timesheet(rows)

    # Inject the requested range into the response
    report["from"] = from_date
    report["to"] = to_date

    return JSONResponse(content=report)


# ---------------------------------------------------------------------------
# GET /api/reports/timesheet/csv — CSV export
# ---------------------------------------------------------------------------


@router.get(
    "/api/reports/timesheet/csv",
    summary="Export timesheet as CSV",
    responses={
        200: {
            "description": "CSV file download",
            "content": {"text/csv": {}},
        },
        400: {"description": "Invalid date parameters"},
    },
)
def get_timesheet_csv(
    from_date: str = Query(
        alias="from",
        description="Start date (YYYY-MM-DD, inclusive)",
        examples=["2026-02-10"],
    ),
    to_date: str = Query(
        alias="to",
        description="End date (YYYY-MM-DD, inclusive)",
        examples=["2026-02-17"],
    ),
    project_id: Optional[int] = Query(
        default=None,
        description="Filter to a single project by ID",
    ),
) -> StreamingResponse:
    """
    Export a timesheet as a downloadable CSV file.

    **CSV columns:** Date, Project, Client, Description, Hours, Rate, Amount

    Only completed entries (end_time set) are included. Running timers are
    excluded.
    """
    # Validate date format
    try:
        from datetime import date as date_type
        date_type.fromisoformat(from_date)
        date_type.fromisoformat(to_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD.",
        )

    if from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="'from' date must be on or before 'to' date.",
        )

    rows = _fetch_report_rows(from_date, to_date, project_id)

    # Build CSV in-memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow(["Date", "Project", "Client", "Description", "Hours", "Rate", "Amount"])

    # Data rows
    for row in rows:
        hours = _seconds_to_hours(row["duration_seconds"])
        amount = round(hours * row["hourly_rate"], 2)
        writer.writerow(
            [
                row["entry_date"],
                row["project_name"],
                row["client_name"],
                row["description"],
                f"{hours:.2f}",
                f"{row['hourly_rate']:.2f}",
                f"{amount:.2f}",
            ]
        )

    csv_content = output.getvalue()
    output.close()

    filename = f"timesheet_{from_date}_to_{to_date}.csv"

    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8-sig")),  # utf-8-sig for Excel compatibility
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
