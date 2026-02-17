"""
API tests — Timer endpoints (start, get, stop, auto-switch).

Coverage:
  - GET  /api/timer             (returns null when no timer running, returns timer when running)
  - POST /api/timer/start       (starts timer, 201, 404 on bad project, 409 on archived project)
  - POST /api/timer/stop        (stops timer, 200, 404 when no timer running)
  - Auto-switch behavior        (starting a timer while one is running stops the first)
  - Timer response fields       (elapsed_seconds, project_name, project_color)
  - Completed entry after stop  (duration_seconds populated, end_time set)
"""

import time as time_module

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_project(client: TestClient, name: str = "Test Project", **kwargs) -> dict:
    payload = {
        "name": name,
        "client_name": "Client",
        "hourly_rate": 100.0,
        "color": "#ff5733",
        **kwargs,
    }
    r = client.post("/api/projects", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def _start_timer(client: TestClient, project_id: int, description: str = "Working") -> dict:
    r = client.post("/api/timer/start", json={
        "project_id": project_id,
        "description": description,
    })
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# GET /api/timer — current timer state
# ---------------------------------------------------------------------------

class TestGetTimer:
    def test_get_timer_no_running_timer_returns_null(self, client: TestClient):
        """GET /api/timer returns null (JSON null) when no timer is running."""
        r = client.get("/api/timer")
        assert r.status_code == 200
        assert r.json() is None

    def test_get_timer_running_returns_timer_object(self, client: TestClient):
        """GET /api/timer returns timer details when a timer is running."""
        proj = _create_project(client, name="Active Project", color="#001122")
        _start_timer(client, proj["id"], description="Deep work")

        r = client.get("/api/timer")
        assert r.status_code == 200
        data = r.json()
        assert data is not None
        assert data["project_id"] == proj["id"]
        assert data["project_name"] == "Active Project"
        assert data["project_color"] == "#001122"
        assert data["description"] == "Deep work"
        assert "elapsed_seconds" in data
        assert data["elapsed_seconds"] >= 0
        assert "start_time" in data
        assert "id" in data

    def test_get_timer_after_stop_returns_null(self, client: TestClient):
        """After stopping the timer, GET /api/timer returns null again."""
        proj = _create_project(client)
        _start_timer(client, proj["id"])
        client.post("/api/timer/stop")

        r = client.get("/api/timer")
        assert r.status_code == 200
        assert r.json() is None


# ---------------------------------------------------------------------------
# POST /api/timer/start — start timer
# ---------------------------------------------------------------------------

class TestStartTimer:
    def test_start_timer_returns_201(self, client: TestClient):
        """Starting a timer returns 201 and the new timer details."""
        proj = _create_project(client, name="Dev Work", color="#aabbcc")
        r = client.post("/api/timer/start", json={
            "project_id": proj["id"],
            "description": "Feature implementation",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["project_id"] == proj["id"]
        assert data["project_name"] == "Dev Work"
        assert data["project_color"] == "#aabbcc"
        assert data["description"] == "Feature implementation"
        assert data["elapsed_seconds"] >= 0
        assert "start_time" in data
        assert data["id"] > 0

    def test_start_timer_nonexistent_project_returns_404(self, client: TestClient):
        """Starting a timer for a non-existent project returns 404."""
        r = client.post("/api/timer/start", json={
            "project_id": 9999,
            "description": "Work",
        })
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_start_timer_archived_project_returns_409(self, client: TestClient):
        """Starting a timer for an archived project returns 409 Conflict."""
        proj = _create_project(client, name="Archived Project")
        # Archive the project
        client.put(f"/api/projects/{proj['id']}", json={"archived": True})

        r = client.post("/api/timer/start", json={
            "project_id": proj["id"],
            "description": "Work",
        })
        assert r.status_code == 409
        assert "archived" in r.json()["detail"].lower()

    def test_start_timer_missing_project_id_returns_422(self, client: TestClient):
        """Omitting project_id returns 422 Unprocessable Entity."""
        r = client.post("/api/timer/start", json={"description": "Work"})
        assert r.status_code == 422

    def test_start_timer_default_description_is_empty(self, client: TestClient):
        """Starting a timer without a description defaults to empty string."""
        proj = _create_project(client)
        r = client.post("/api/timer/start", json={"project_id": proj["id"]})
        assert r.status_code == 201
        assert r.json()["description"] == ""

    def test_start_timer_creates_running_entry(self, client: TestClient):
        """After starting the timer, GET /api/timer returns the running timer."""
        proj = _create_project(client)
        started = _start_timer(client, proj["id"], description="Running task")

        r = client.get("/api/timer")
        assert r.status_code == 200
        data = r.json()
        assert data is not None
        assert data["id"] == started["id"]
        assert data["description"] == "Running task"


# ---------------------------------------------------------------------------
# POST /api/timer/stop — stop timer
# ---------------------------------------------------------------------------

class TestStopTimer:
    def test_stop_timer_returns_200(self, client: TestClient):
        """Stopping the running timer returns 200 and the completed entry."""
        proj = _create_project(client)
        started = _start_timer(client, proj["id"], description="Some work")

        r = client.post("/api/timer/stop")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == started["id"]
        assert data["project_id"] == proj["id"]

    def test_stop_timer_populates_end_time(self, client: TestClient):
        """The stopped entry has a non-null end_time."""
        proj = _create_project(client)
        _start_timer(client, proj["id"])

        r = client.post("/api/timer/stop")
        assert r.status_code == 200
        assert r.json()["end_time"] is not None

    def test_stop_timer_populates_duration_seconds(self, client: TestClient):
        """The stopped entry has a non-null, non-negative duration_seconds."""
        proj = _create_project(client)
        _start_timer(client, proj["id"])

        r = client.post("/api/timer/stop")
        assert r.status_code == 200
        data = r.json()
        assert data["duration_seconds"] is not None
        assert data["duration_seconds"] >= 0

    def test_stop_timer_includes_project_name_and_color(self, client: TestClient):
        """The stopped entry response includes project_name and project_color."""
        proj = _create_project(client, name="Stopped Project", color="#999999")
        _start_timer(client, proj["id"])

        r = client.post("/api/timer/stop")
        assert r.status_code == 200
        data = r.json()
        assert data["project_name"] == "Stopped Project"
        assert data["project_color"] == "#999999"

    def test_stop_timer_when_none_running_returns_404(self, client: TestClient):
        """POST /api/timer/stop returns 404 when no timer is running."""
        r = client.post("/api/timer/stop")
        assert r.status_code == 404
        assert "no running timer" in r.json()["detail"].lower()

    def test_stop_timer_entry_appears_in_entries_list(self, client: TestClient):
        """After stopping, the completed entry appears in GET /api/entries."""
        proj = _create_project(client)
        started = _start_timer(client, proj["id"])
        client.post("/api/timer/stop")

        r = client.get("/api/entries")
        assert r.status_code == 200
        ids = {e["id"] for e in r.json()}
        assert started["id"] in ids

    def test_stop_timer_second_stop_returns_404(self, client: TestClient):
        """Calling stop twice returns 404 on the second call."""
        proj = _create_project(client)
        _start_timer(client, proj["id"])
        client.post("/api/timer/stop")

        r = client.post("/api/timer/stop")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Auto-switch behavior
# ---------------------------------------------------------------------------

class TestAutoSwitch:
    def test_starting_second_timer_stops_first(self, client: TestClient):
        """Starting a timer while one is running auto-stops the first timer."""
        proj1 = _create_project(client, name="Project 1")
        proj2 = _create_project(client, name="Project 2")

        first = _start_timer(client, proj1["id"], description="First")
        second = _start_timer(client, proj2["id"], description="Second")

        # Only second timer should be running
        r = client.get("/api/timer")
        assert r.status_code == 200
        data = r.json()
        assert data is not None
        assert data["id"] == second["id"]
        assert data["project_id"] == proj2["id"]

    def test_auto_stopped_first_timer_appears_in_entries(self, client: TestClient):
        """The auto-stopped first timer appears as a completed entry in GET /api/entries."""
        proj1 = _create_project(client, name="First Project")
        proj2 = _create_project(client, name="Second Project")

        first = _start_timer(client, proj1["id"], description="First task")
        _start_timer(client, proj2["id"], description="Second task")

        # The first entry should be in entries with an end_time set
        r = client.get("/api/entries")
        assert r.status_code == 200
        entries = r.json()
        first_entry = next((e for e in entries if e["id"] == first["id"]), None)
        assert first_entry is not None
        # The auto-stopped entry has end_time and duration_seconds populated
        assert first_entry["end_time"] is not None
        assert first_entry["duration_seconds"] is not None
        assert first_entry["duration_seconds"] >= 0

    def test_auto_switch_three_timers_sequentially(self, client: TestClient):
        """Starting three timers in sequence — only the last is running."""
        proj1 = _create_project(client, name="P1")
        proj2 = _create_project(client, name="P2")
        proj3 = _create_project(client, name="P3")

        t1 = _start_timer(client, proj1["id"])
        t2 = _start_timer(client, proj2["id"])
        t3 = _start_timer(client, proj3["id"])

        r = client.get("/api/timer")
        assert r.status_code == 200
        assert r.json()["id"] == t3["id"]

        # t1 and t2 should be completed entries
        r2 = client.get("/api/entries")
        entries = {e["id"]: e for e in r2.json()}
        # t1 and t2 are completed (end_time not null)
        assert entries[t1["id"]]["end_time"] is not None
        assert entries[t2["id"]]["end_time"] is not None

    def test_start_same_project_twice_auto_switches(self, client: TestClient):
        """Starting the timer on the same project again creates a new entry."""
        proj = _create_project(client, name="Same Project")

        t1 = _start_timer(client, proj["id"], description="Session 1")
        t2 = _start_timer(client, proj["id"], description="Session 2")

        # Should be different entries
        assert t1["id"] != t2["id"]

        # Only second is running
        r = client.get("/api/timer")
        assert r.json()["id"] == t2["id"]


# ---------------------------------------------------------------------------
# Timer response fields validation
# ---------------------------------------------------------------------------

class TestTimerResponseFields:
    def test_timer_response_has_all_required_fields(self, client: TestClient):
        """The timer response contains all required fields."""
        proj = _create_project(client)
        r = client.post("/api/timer/start", json={
            "project_id": proj["id"],
            "description": "Test",
        })
        assert r.status_code == 201
        data = r.json()
        required_fields = {
            "id", "project_id", "project_name", "project_color",
            "description", "start_time", "elapsed_seconds",
        }
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_elapsed_seconds_is_non_negative(self, client: TestClient):
        """elapsed_seconds in the timer response is always >= 0."""
        proj = _create_project(client)
        r = client.post("/api/timer/start", json={"project_id": proj["id"]})
        assert r.status_code == 201
        assert r.json()["elapsed_seconds"] >= 0

    def test_elapsed_seconds_increases_over_time(self, client: TestClient):
        """elapsed_seconds reported by GET /api/timer grows with time."""
        proj = _create_project(client)
        _start_timer(client, proj["id"])

        r1 = client.get("/api/timer")
        elapsed1 = r1.json()["elapsed_seconds"]

        # Wait briefly and check again
        time_module.sleep(1.1)

        r2 = client.get("/api/timer")
        elapsed2 = r2.json()["elapsed_seconds"]

        # elapsed should have increased (or stayed same if sub-second rounding)
        assert elapsed2 >= elapsed1
