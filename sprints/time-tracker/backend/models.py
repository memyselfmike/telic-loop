"""
Freelancer Time Tracker — Pydantic Request/Response Models

All datetime fields use ISO 8601 format: 2026-02-17T14:30:00
The API operates in local time (no timezone handling needed for a single-user tool).

Model hierarchy:
  Projects:    ProjectCreate → ProjectResponse, ProjectUpdate
  Entries:     EntryCreate   → EntryResponse
  Timer:       TimerStartRequest → TimerResponse
  Errors:      ErrorDetail
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _validate_iso_datetime(value: str | datetime) -> str:
    """
    Accept either a datetime object or an ISO 8601 string and always return
    a normalized ISO 8601 string (without timezone suffix, local time).

    Raises ValueError for strings that cannot be parsed as ISO 8601.
    """
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat()

    # Try to parse the string; raise a friendly error on failure.
    try:
        dt = datetime.fromisoformat(value)
        return dt.replace(microsecond=0).isoformat()
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid ISO 8601 datetime string: {value!r}. "
            "Expected format: 2026-02-17T14:30:00"
        ) from exc


# ---------------------------------------------------------------------------
# Project models
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    """Request body for POST /api/projects."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Project name (required)",
        examples=["Website Redesign"],
    )
    client_name: str = Field(
        default="",
        max_length=200,
        description="Client or company name",
        examples=["Acme Corp"],
    )
    hourly_rate: float = Field(
        default=0.0,
        ge=0.0,
        description="Billing rate in currency per hour (≥ 0)",
        examples=[150.0],
    )
    color: str = Field(
        default="#58a6ff",
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Hex color code for the project (e.g. #58a6ff)",
        examples=["#58a6ff"],
    )


class ProjectUpdate(BaseModel):
    """
    Request body for PUT /api/projects/{id}.

    All fields are optional — only supplied fields are updated.
    """

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Project name",
    )
    client_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Client or company name",
    )
    hourly_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Billing rate in currency per hour (≥ 0)",
    )
    color: Optional[str] = Field(
        default=None,
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Hex color code for the project",
    )
    archived: Optional[bool] = Field(
        default=None,
        description="Whether the project is archived (hidden from active timer dropdown)",
    )


class ProjectResponse(BaseModel):
    """Response body for project endpoints."""

    id: int = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    client_name: str = Field(..., description="Client or company name")
    hourly_rate: float = Field(..., description="Billing rate per hour")
    color: str = Field(..., description="Hex color code")
    archived: bool = Field(..., description="True if the project is archived")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 last-update timestamp")

    model_config = {"from_attributes": True}

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def normalise_datetime(cls, v: str | datetime) -> str:
        """Normalise DB text or datetime objects to ISO 8601 strings."""
        return _validate_iso_datetime(v)

    @field_validator("archived", mode="before")
    @classmethod
    def coerce_archived(cls, v: int | bool) -> bool:
        """SQLite stores archived as INTEGER (0/1); coerce to bool."""
        return bool(v)

    @classmethod
    def from_row(cls, row: object) -> "ProjectResponse":
        """
        Construct from a sqlite3.Row (or any mapping).

        Converts archived INTEGER → bool and validates datetime strings.
        """
        return cls.model_validate(dict(row))


# ---------------------------------------------------------------------------
# Time entry models
# ---------------------------------------------------------------------------

class EntryCreate(BaseModel):
    """Request body for POST /api/entries (manual time entry creation)."""

    project_id: int = Field(
        ...,
        gt=0,
        description="ID of the project this entry belongs to",
        examples=[1],
    )
    description: str = Field(
        default="",
        max_length=1000,
        description="What was worked on during this period",
        examples=["Homepage layout"],
    )
    start_time: str = Field(
        ...,
        description="Entry start time in ISO 8601 format (2026-02-17T09:00:00)",
        examples=["2026-02-17T09:00:00"],
    )
    end_time: str = Field(
        ...,
        description="Entry end time in ISO 8601 format (2026-02-17T12:30:00)",
        examples=["2026-02-17T12:30:00"],
    )

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def normalise_datetime(cls, v: str | datetime) -> str:
        return _validate_iso_datetime(v)

    @model_validator(mode="after")
    def end_after_start(self) -> "EntryCreate":
        """Ensure end_time is strictly after start_time."""
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        if end <= start:
            raise ValueError("end_time must be after start_time")
        return self


class EntryUpdate(BaseModel):
    """
    Request body for PUT /api/entries/{id}.

    All fields are optional — only supplied fields are updated.
    """

    project_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="ID of the project this entry belongs to",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="What was worked on during this period",
    )
    start_time: Optional[str] = Field(
        default=None,
        description="Entry start time in ISO 8601 format",
    )
    end_time: Optional[str] = Field(
        default=None,
        description="Entry end time in ISO 8601 format",
    )

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def normalise_datetime(cls, v: Optional[str | datetime]) -> Optional[str]:
        if v is None:
            return None
        return _validate_iso_datetime(v)


class EntryResponse(BaseModel):
    """
    Response body for time entry endpoints.

    Includes computed fields project_name and project_color, which are
    joined from the projects table when fetching entries.
    """

    id: int = Field(..., description="Unique entry identifier")
    project_id: int = Field(..., description="ID of the associated project")
    description: str = Field(..., description="Work description")
    start_time: str = Field(..., description="ISO 8601 start timestamp")
    end_time: Optional[str] = Field(
        default=None,
        description="ISO 8601 end timestamp (null if timer is still running)",
    )
    duration_seconds: Optional[int] = Field(
        default=None,
        description="Duration in seconds (null while timer is running)",
    )
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 last-update timestamp")

    # Computed/joined fields from the projects table
    project_name: str = Field(..., description="Name of the associated project")
    project_color: str = Field(
        ...,
        description="Hex color code of the associated project",
    )

    model_config = {"from_attributes": True}

    @field_validator("start_time", "created_at", "updated_at", mode="before")
    @classmethod
    def normalise_required_datetime(cls, v: str | datetime) -> str:
        return _validate_iso_datetime(v)

    @field_validator("end_time", mode="before")
    @classmethod
    def normalise_optional_end_time(cls, v: Optional[str | datetime]) -> Optional[str]:
        if v is None:
            return None
        return _validate_iso_datetime(v)

    @classmethod
    def from_row(cls, row: object) -> "EntryResponse":
        """
        Construct from a sqlite3.Row that includes a JOIN with the projects table
        (i.e. SELECT te.*, p.name AS project_name, p.color AS project_color
               FROM time_entries te JOIN projects p ON p.id = te.project_id).
        """
        return cls.model_validate(dict(row))


# ---------------------------------------------------------------------------
# Timer models
# ---------------------------------------------------------------------------

class TimerStartRequest(BaseModel):
    """Request body for POST /api/timer/start."""

    project_id: int = Field(
        ...,
        gt=0,
        description="ID of the project to bill this time against",
        examples=[1],
    )
    description: str = Field(
        default="",
        max_length=1000,
        description="What you are working on (shown in the running timer display)",
        examples=["Client call prep"],
    )


class TimerResponse(BaseModel):
    """
    Response body for GET /api/timer and POST /api/timer/start.

    elapsed_seconds is computed server-side as (now - start_time) in seconds,
    ensuring the browser always has an accurate baseline regardless of when
    the timer was started.
    """

    id: int = Field(..., description="Unique entry identifier for the running timer")
    project_id: int = Field(..., description="ID of the associated project")
    project_name: str = Field(..., description="Name of the associated project")
    project_color: str = Field(
        ...,
        description="Hex color code of the associated project",
    )
    description: str = Field(..., description="Work description")
    start_time: str = Field(..., description="ISO 8601 timestamp when the timer started")
    elapsed_seconds: int = Field(
        ...,
        ge=0,
        description="Seconds elapsed since the timer started (computed server-side at response time)",
    )

    model_config = {"from_attributes": True}

    @field_validator("start_time", mode="before")
    @classmethod
    def normalise_datetime(cls, v: str | datetime) -> str:
        return _validate_iso_datetime(v)

    @field_validator("elapsed_seconds", mode="before")
    @classmethod
    def coerce_elapsed(cls, v: int | float) -> int:
        """Ensure elapsed_seconds is a non-negative integer."""
        return max(0, int(v))

    @classmethod
    def from_row(cls, row: object, now: Optional[datetime] = None) -> "TimerResponse":
        """
        Construct from a sqlite3.Row that includes a JOIN with the projects table.

        Args:
            row:  A row with columns: id, project_id, description, start_time,
                  project_name, project_color  (end_time must be NULL/missing).
            now:  The reference "now" used for computing elapsed_seconds.
                  Defaults to datetime.now() — injectable for testing.
        """
        data = dict(row)
        if now is None:
            now = datetime.now()

        # Parse the stored ISO 8601 string from SQLite
        start = datetime.fromisoformat(data["start_time"])
        data["elapsed_seconds"] = max(0, int((now - start).total_seconds()))

        return cls.model_validate(data)


# ---------------------------------------------------------------------------
# Error model
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """
    Standard error response body.

    FastAPI raises HTTPException with a `detail` field automatically for
    422 validation errors. This model is used for 400, 404, and 409 responses
    raised explicitly in route handlers.

    Example:
        raise HTTPException(status_code=404, detail="Project not found")
    """

    detail: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Project not found"],
    )
