#!/usr/bin/env python3
"""
Verification: Pydantic models - structure, validation, serialization
PRD Reference: Section 3 (API Endpoints) - request/response shapes
Vision Goal: Trust the Data - type-safe contracts prevent corrupt entries
Category: unit
"""
import sys
import os
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SPRINT_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, SPRINT_DIR)

print("=== Unit: Pydantic Models ===")

try:
    from backend.models import (
        ProjectCreate, ProjectResponse, ProjectUpdate,
        EntryCreate, EntryResponse,
        TimerStartRequest, TimerResponse
    )
    print("PASS: All models import successfully")
except ImportError as e:
    print(f"FAIL: Cannot import models: {e}")
    sys.exit(1)

# Test 1: ProjectCreate accepts valid data
try:
    p = ProjectCreate(name="Test Project", client_name="Acme Corp", hourly_rate=150.0, color="#58a6ff")
    assert p.name == "Test Project"
    assert p.hourly_rate == 150.0
    print("PASS: ProjectCreate accepts valid data")
except Exception as e:
    print(f"FAIL: ProjectCreate: {e}")
    sys.exit(1)

# Test 2: ProjectCreate rejects missing required name
try:
    p = ProjectCreate(client_name="Acme")
    print("FAIL: ProjectCreate should reject missing name")
    sys.exit(1)
except Exception:
    print("PASS: ProjectCreate rejects missing name")

# Test 3: ProjectResponse has all PRD fields
try:
    r = ProjectResponse(
        id=1, name="Test", client_name="Client", hourly_rate=100.0,
        color="#3fb950", archived=False,
        created_at="2026-02-17T10:00:00", updated_at="2026-02-17T10:00:00"
    )
    assert r.id == 1
    assert r.archived == False
    print("PASS: ProjectResponse has all required fields")
except Exception as e:
    print(f"FAIL: ProjectResponse: {e}")
    sys.exit(1)

# Test 4: EntryCreate requires project_id, start_time, end_time
try:
    e = EntryCreate(project_id=1, start_time="2026-02-17T09:00:00", end_time="2026-02-17T10:30:00")
    assert e.project_id == 1
    print("PASS: EntryCreate accepts valid manual entry")
except Exception as ex:
    print(f"FAIL: EntryCreate: {ex}")
    sys.exit(1)

# Test 5: EntryResponse includes project_name and project_color
try:
    r = EntryResponse(
        id=1, project_id=1, description="Homepage layout",
        start_time="2026-02-17T09:00:00", end_time="2026-02-17T10:30:00",
        duration_seconds=5400,
        project_name="Website Redesign", project_color="#58a6ff",
        created_at="2026-02-17T09:00:00", updated_at="2026-02-17T09:00:00"
    )
    assert r.project_name == "Website Redesign"
    assert r.project_color == "#58a6ff"
    print("PASS: EntryResponse includes project_name and project_color")
except Exception as e:
    print(f"FAIL: EntryResponse: {e}")
    sys.exit(1)

# Test 6: TimerStartRequest requires project_id
try:
    t = TimerStartRequest(project_id=1)
    assert t.project_id == 1
    print("PASS: TimerStartRequest accepts project_id")
except Exception as e:
    print(f"FAIL: TimerStartRequest: {e}")
    sys.exit(1)

# Test 7: TimerResponse includes elapsed_seconds
try:
    t = TimerResponse(
        id=1, project_id=1, description="",
        start_time="2026-02-17T09:00:00",
        elapsed_seconds=3600,
        project_name="Test",
        created_at="2026-02-17T09:00:00", updated_at="2026-02-17T09:00:00"
    )
    assert t.elapsed_seconds == 3600
    print("PASS: TimerResponse includes elapsed_seconds field")
except Exception as e:
    print(f"FAIL: TimerResponse: {e}")
    sys.exit(1)

print("\n=== ALL MODEL UNIT TESTS PASSED ===")
sys.exit(0)
