"""
API tests — Time Entry endpoints (manual entries, listing, update, delete).

Coverage:
  - POST /api/entries            (create manual entry, validation errors, 404 on bad project)
  - GET  /api/entries            (list all, filter by ?date=, filter by ?from=&to=)
  - PUT  /api/entries/{id}       (update fields, duration recomputed, 404 for missing)
  - DELETE /api/entries/{id}     (204 on success, 404 for missing)
  - EntryResponse includes project_name and project_color from JOIN
"""

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


def _create_entry(
    client: TestClient,
    project_id: int,
    start_time: str = "2026-02-17T09:00:00",
    end_time: str = "2026-02-17T10:30:00",
    description: str = "Work description",
    **kwargs,
) -> dict:
    payload = {
        "project_id": project_id,
        "description": description,
        "start_time": start_time,
        "end_time": end_time,
        **kwargs,
    }
    r = client.post("/api/entries", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# POST /api/entries — create manual entry
# ---------------------------------------------------------------------------

class TestCreateManualEntry:
    def test_create_entry_returns_201(self, client: TestClient):
        """Creating a manual entry with valid data returns 201 and the entry."""
        proj = _create_project(client, name="Dev Project", color="#58a6ff")
        r = client.post("/api/entries", json={
            "project_id": proj["id"],
            "description": "Implement login",
            "start_time": "2026-02-17T09:00:00",
            "end_time": "2026-02-17T12:00:00",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["project_id"] == proj["id"]
        assert data["description"] == "Implement login"
        assert data["start_time"] == "2026-02-17T09:00:00"
        assert data["end_time"] == "2026-02-17T12:00:00"
        assert data["duration_seconds"] == 3 * 3600  # 3 hours = 10800 seconds
        assert "id" in data
        assert data["id"] > 0

    def test_create_entry_includes_project_name_and_color(self, client: TestClient):
        """The entry response includes project_name and project_color from the JOIN."""
        proj = _create_project(client, name="My API Project", color="#aabbcc")
        r = client.post("/api/entries", json={
            "project_id": proj["id"],
            "description": "Bug fix",
            "start_time": "2026-02-17T14:00:00",
            "end_time": "2026-02-17T15:00:00",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["project_name"] == "My API Project"
        assert data["project_color"] == "#aabbcc"

    def test_create_entry_duration_computed_correctly(self, client: TestClient):
        """duration_seconds is computed from end_time minus start_time."""
        proj = _create_project(client)
        # 2.5 hours = 9000 seconds
        entry = _create_entry(
            client, proj["id"],
            start_time="2026-02-17T10:00:00",
            end_time="2026-02-17T12:30:00",
        )
        assert entry["duration_seconds"] == 9000

    def test_create_entry_default_description_is_empty(self, client: TestClient):
        """Omitting description defaults to empty string."""
        proj = _create_project(client)
        r = client.post("/api/entries", json={
            "project_id": proj["id"],
            "start_time": "2026-02-17T09:00:00",
            "end_time": "2026-02-17T10:00:00",
        })
        assert r.status_code == 201
        assert r.json()["description"] == ""

    def test_create_entry_nonexistent_project_returns_404(self, client: TestClient):
        """Creating an entry for a non-existent project returns 404."""
        r = client.post("/api/entries", json={
            "project_id": 9999,
            "start_time": "2026-02-17T09:00:00",
            "end_time": "2026-02-17T10:00:00",
        })
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_create_entry_end_before_start_returns_422(self, client: TestClient):
        """end_time before start_time is rejected with 422."""
        proj = _create_project(client)
        r = client.post("/api/entries", json={
            "project_id": proj["id"],
            "start_time": "2026-02-17T12:00:00",
            "end_time": "2026-02-17T09:00:00",
        })
        assert r.status_code == 422

    def test_create_entry_end_equal_to_start_returns_422(self, client: TestClient):
        """end_time equal to start_time is rejected with 422."""
        proj = _create_project(client)
        r = client.post("/api/entries", json={
            "project_id": proj["id"],
            "start_time": "2026-02-17T10:00:00",
            "end_time": "2026-02-17T10:00:00",
        })
        assert r.status_code == 422

    def test_create_entry_missing_start_time_returns_422(self, client: TestClient):
        """Omitting start_time returns 422 Unprocessable Entity."""
        proj = _create_project(client)
        r = client.post("/api/entries", json={
            "project_id": proj["id"],
            "end_time": "2026-02-17T10:00:00",
        })
        assert r.status_code == 422

    def test_create_entry_missing_end_time_returns_422(self, client: TestClient):
        """Omitting end_time returns 422 Unprocessable Entity."""
        proj = _create_project(client)
        r = client.post("/api/entries", json={
            "project_id": proj["id"],
            "start_time": "2026-02-17T09:00:00",
        })
        assert r.status_code == 422

    def test_create_entry_invalid_datetime_returns_422(self, client: TestClient):
        """Passing a non-ISO datetime string returns 422."""
        proj = _create_project(client)
        r = client.post("/api/entries", json={
            "project_id": proj["id"],
            "start_time": "not-a-date",
            "end_time": "also-not-a-date",
        })
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/entries — list entries
# ---------------------------------------------------------------------------

class TestListEntries:
    def test_list_empty_returns_empty_array(self, client: TestClient):
        """With no entries, GET /api/entries returns an empty list."""
        r = client.get("/api/entries")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_returns_all_entries(self, client: TestClient):
        """All created entries appear in the unfiltered list."""
        proj = _create_project(client)
        e1 = _create_entry(client, proj["id"], start_time="2026-02-17T09:00:00", end_time="2026-02-17T10:00:00")
        e2 = _create_entry(client, proj["id"], start_time="2026-02-17T11:00:00", end_time="2026-02-17T12:00:00")

        r = client.get("/api/entries")
        assert r.status_code == 200
        ids = {e["id"] for e in r.json()}
        assert e1["id"] in ids
        assert e2["id"] in ids

    def test_list_entries_include_project_fields(self, client: TestClient):
        """Each entry in the list includes project_name and project_color."""
        proj = _create_project(client, name="Colored Project", color="#112233")
        _create_entry(client, proj["id"])

        r = client.get("/api/entries")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["project_name"] == "Colored Project"
        assert data[0]["project_color"] == "#112233"

    def test_list_filter_by_date(self, client: TestClient):
        """?date=YYYY-MM-DD returns only entries starting on that calendar date."""
        proj = _create_project(client)
        today_entry = _create_entry(
            client, proj["id"],
            start_time="2026-02-17T09:00:00",
            end_time="2026-02-17T10:00:00",
        )
        yesterday_entry = _create_entry(
            client, proj["id"],
            start_time="2026-02-16T09:00:00",
            end_time="2026-02-16T10:00:00",
        )

        r = client.get("/api/entries?date=2026-02-17")
        assert r.status_code == 200
        data = r.json()
        ids = {e["id"] for e in data}
        assert today_entry["id"] in ids
        assert yesterday_entry["id"] not in ids

    def test_list_filter_by_date_no_match_returns_empty(self, client: TestClient):
        """?date= with a date that has no entries returns an empty list."""
        proj = _create_project(client)
        _create_entry(client, proj["id"], start_time="2026-02-17T09:00:00", end_time="2026-02-17T10:00:00")

        r = client.get("/api/entries?date=2025-01-01")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_filter_by_date_range(self, client: TestClient):
        """?from=&to= returns entries within the date range (both inclusive)."""
        proj = _create_project(client)
        e_mon = _create_entry(client, proj["id"], start_time="2026-02-16T09:00:00", end_time="2026-02-16T10:00:00")
        e_tue = _create_entry(client, proj["id"], start_time="2026-02-17T09:00:00", end_time="2026-02-17T10:00:00")
        e_wed = _create_entry(client, proj["id"], start_time="2026-02-18T09:00:00", end_time="2026-02-18T10:00:00")
        e_thu = _create_entry(client, proj["id"], start_time="2026-02-19T09:00:00", end_time="2026-02-19T10:00:00")

        r = client.get("/api/entries?from=2026-02-17&to=2026-02-18")
        assert r.status_code == 200
        ids = {e["id"] for e in r.json()}
        assert e_mon["id"] not in ids
        assert e_tue["id"] in ids
        assert e_wed["id"] in ids
        assert e_thu["id"] not in ids

    def test_list_entries_sorted_newest_first(self, client: TestClient):
        """Entries are returned newest (latest start_time) first."""
        proj = _create_project(client)
        _create_entry(client, proj["id"], start_time="2026-02-17T08:00:00", end_time="2026-02-17T09:00:00")
        _create_entry(client, proj["id"], start_time="2026-02-17T14:00:00", end_time="2026-02-17T15:00:00")
        _create_entry(client, proj["id"], start_time="2026-02-17T11:00:00", end_time="2026-02-17T12:00:00")

        r = client.get("/api/entries")
        times = [e["start_time"] for e in r.json()]
        assert times == sorted(times, reverse=True)


# ---------------------------------------------------------------------------
# PUT /api/entries/{id} — update entry
# ---------------------------------------------------------------------------

class TestUpdateEntry:
    def test_update_description(self, client: TestClient):
        """Updating only the description changes it and leaves times intact."""
        proj = _create_project(client)
        entry = _create_entry(client, proj["id"], description="Old description")

        r = client.put(f"/api/entries/{entry['id']}", json={"description": "New description"})
        assert r.status_code == 200
        data = r.json()
        assert data["description"] == "New description"
        assert data["start_time"] == entry["start_time"]  # unchanged

    def test_update_end_time_recomputes_duration(self, client: TestClient):
        """Updating end_time causes duration_seconds to be recomputed."""
        proj = _create_project(client)
        # 1 hour initially
        entry = _create_entry(
            client, proj["id"],
            start_time="2026-02-17T09:00:00",
            end_time="2026-02-17T10:00:00",
        )
        assert entry["duration_seconds"] == 3600

        # Extend to 3 hours
        r = client.put(f"/api/entries/{entry['id']}", json={"end_time": "2026-02-17T12:00:00"})
        assert r.status_code == 200
        assert r.json()["duration_seconds"] == 3 * 3600

    def test_update_project_id(self, client: TestClient):
        """Updating project_id re-associates the entry with a different project."""
        proj1 = _create_project(client, name="Project 1")
        proj2 = _create_project(client, name="Project 2")
        entry = _create_entry(client, proj1["id"])

        r = client.put(f"/api/entries/{entry['id']}", json={"project_id": proj2["id"]})
        assert r.status_code == 200
        data = r.json()
        assert data["project_id"] == proj2["id"]
        assert data["project_name"] == "Project 2"

    def test_update_nonexistent_entry_returns_404(self, client: TestClient):
        """Updating an entry that doesn't exist returns 404."""
        r = client.put("/api/entries/9999", json={"description": "Ghost"})
        assert r.status_code == 404

    def test_update_empty_body_returns_current_state(self, client: TestClient):
        """An empty update body returns the entry unchanged."""
        proj = _create_project(client)
        entry = _create_entry(client, proj["id"], description="Stable")

        r = client.put(f"/api/entries/{entry['id']}", json={})
        assert r.status_code == 200
        assert r.json()["description"] == "Stable"


# ---------------------------------------------------------------------------
# DELETE /api/entries/{id} — delete
# ---------------------------------------------------------------------------

class TestDeleteEntry:
    def test_delete_entry_returns_204(self, client: TestClient):
        """Deleting an existing entry returns 204 No Content."""
        proj = _create_project(client)
        entry = _create_entry(client, proj["id"])

        r = client.delete(f"/api/entries/{entry['id']}")
        assert r.status_code == 204

    def test_delete_entry_removes_it_from_list(self, client: TestClient):
        """After deletion, the entry no longer appears in GET /api/entries."""
        proj = _create_project(client)
        entry = _create_entry(client, proj["id"])

        client.delete(f"/api/entries/{entry['id']}")

        r = client.get("/api/entries")
        ids = {e["id"] for e in r.json()}
        assert entry["id"] not in ids

    def test_delete_nonexistent_entry_returns_404(self, client: TestClient):
        """Deleting an entry that doesn't exist returns 404."""
        r = client.delete("/api/entries/9999")
        assert r.status_code == 404

    def test_delete_one_entry_leaves_others(self, client: TestClient):
        """Deleting one entry does not affect other entries."""
        proj = _create_project(client)
        e1 = _create_entry(client, proj["id"], start_time="2026-02-17T09:00:00", end_time="2026-02-17T10:00:00")
        e2 = _create_entry(client, proj["id"], start_time="2026-02-17T11:00:00", end_time="2026-02-17T12:00:00")

        client.delete(f"/api/entries/{e1['id']}")

        r = client.get("/api/entries")
        ids = {e["id"] for e in r.json()}
        assert e1["id"] not in ids
        assert e2["id"] in ids
