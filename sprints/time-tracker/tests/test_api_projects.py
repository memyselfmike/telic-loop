"""
API tests — Projects CRUD endpoints.

Coverage:
  - POST /api/projects      (create with defaults, all fields, invalid data)
  - GET  /api/projects      (list all, filter active/archived)
  - GET  /api/projects/{id} (get by ID, 404 for missing)
  - PUT  /api/projects/{id} (update partial fields, archive, 404 for missing)
  - DELETE /api/projects/{id} (delete empty project, 409 with entries, 404 for missing)
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_project(client: TestClient, **kwargs) -> dict:
    """Create a project with sensible defaults and return the response JSON."""
    payload = {
        "name": "Test Project",
        "client_name": "Acme Corp",
        "hourly_rate": 100.0,
        "color": "#ff5733",
        **kwargs,
    }
    r = client.post("/api/projects", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def _create_entry(client: TestClient, project_id: int, **kwargs) -> dict:
    """Create a manual time entry and return the response JSON."""
    payload = {
        "project_id": project_id,
        "description": "Some work",
        "start_time": "2026-02-17T09:00:00",
        "end_time": "2026-02-17T10:00:00",
        **kwargs,
    }
    r = client.post("/api/entries", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# POST /api/projects — create
# ---------------------------------------------------------------------------

class TestCreateProject:
    def test_create_with_all_fields(self, client: TestClient):
        """Creating a project with all fields returns 201 and the full project."""
        r = client.post("/api/projects", json={
            "name": "Website Redesign",
            "client_name": "Acme Corp",
            "hourly_rate": 150.0,
            "color": "#58a6ff",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Website Redesign"
        assert data["client_name"] == "Acme Corp"
        assert data["hourly_rate"] == 150.0
        assert data["color"] == "#58a6ff"
        assert data["archived"] is False
        assert "id" in data
        assert data["id"] > 0
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_with_defaults(self, client: TestClient):
        """Creating a project with only the name applies correct defaults."""
        r = client.post("/api/projects", json={"name": "Minimal Project"})
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Minimal Project"
        assert data["client_name"] == ""
        assert data["hourly_rate"] == 0.0
        assert data["color"] == "#58a6ff"
        assert data["archived"] is False

    def test_create_assigns_unique_ids(self, client: TestClient):
        """Each created project gets a distinct auto-incremented ID."""
        p1 = _create_project(client, name="Project Alpha")
        p2 = _create_project(client, name="Project Beta")
        assert p1["id"] != p2["id"]

    def test_create_missing_name_returns_422(self, client: TestClient):
        """Omitting the required `name` field returns 422 Unprocessable Entity."""
        r = client.post("/api/projects", json={"hourly_rate": 50.0})
        assert r.status_code == 422

    def test_create_empty_name_returns_422(self, client: TestClient):
        """An empty string name violates min_length=1 and returns 422."""
        r = client.post("/api/projects", json={"name": ""})
        assert r.status_code == 422

    def test_create_invalid_color_returns_422(self, client: TestClient):
        """A color that doesn't match ^#[0-9a-fA-F]{6}$ returns 422."""
        r = client.post("/api/projects", json={"name": "Bad Color", "color": "red"})
        assert r.status_code == 422

    def test_create_negative_rate_returns_422(self, client: TestClient):
        """A negative hourly_rate violates ge=0.0 and returns 422."""
        r = client.post("/api/projects", json={"name": "Negative Rate", "hourly_rate": -10.0})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/projects — list
# ---------------------------------------------------------------------------

class TestListProjects:
    def test_list_empty_returns_empty_array(self, client: TestClient):
        """With no projects, GET /api/projects returns an empty list."""
        r = client.get("/api/projects")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_returns_all_projects(self, client: TestClient):
        """All created projects appear in the list."""
        _create_project(client, name="Alpha")
        _create_project(client, name="Beta")
        r = client.get("/api/projects")
        assert r.status_code == 200
        names = {p["name"] for p in r.json()}
        assert {"Alpha", "Beta"} == names

    def test_list_active_filter_excludes_archived(self, client: TestClient):
        """?active=true returns only non-archived projects."""
        active_proj = _create_project(client, name="Active Project")
        archived_proj = _create_project(client, name="Archived Project")
        # Archive the second project
        client.put(f"/api/projects/{archived_proj['id']}", json={"archived": True})

        r = client.get("/api/projects?active=true")
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()}
        assert active_proj["id"] in ids
        assert archived_proj["id"] not in ids

    def test_list_active_false_returns_only_archived(self, client: TestClient):
        """?active=false returns only archived projects."""
        _create_project(client, name="Active Project")
        archived_proj = _create_project(client, name="Archived Project")
        client.put(f"/api/projects/{archived_proj['id']}", json={"archived": True})

        r = client.get("/api/projects?active=false")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == archived_proj["id"]
        assert data[0]["archived"] is True

    def test_list_without_filter_returns_all(self, client: TestClient):
        """No filter returns both active and archived projects."""
        p1 = _create_project(client, name="Active")
        p2 = _create_project(client, name="Archived")
        client.put(f"/api/projects/{p2['id']}", json={"archived": True})

        r = client.get("/api/projects")
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()}
        assert p1["id"] in ids
        assert p2["id"] in ids

    def test_list_sorted_alphabetically(self, client: TestClient):
        """Projects are returned in alphabetical order by name."""
        _create_project(client, name="Zebra")
        _create_project(client, name="Apple")
        _create_project(client, name="Mango")

        r = client.get("/api/projects")
        names = [p["name"] for p in r.json()]
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# GET /api/projects/{id} — get by ID
# ---------------------------------------------------------------------------

class TestGetProject:
    def test_get_existing_project(self, client: TestClient):
        """GET /api/projects/{id} returns the project matching the given ID."""
        created = _create_project(client, name="My Project", hourly_rate=75.0)
        r = client.get(f"/api/projects/{created['id']}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == created["id"]
        assert data["name"] == "My Project"
        assert data["hourly_rate"] == 75.0

    def test_get_nonexistent_project_returns_404(self, client: TestClient):
        """GET /api/projects/9999 returns 404 when the project does not exist."""
        r = client.get("/api/projects/9999")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()


# ---------------------------------------------------------------------------
# PUT /api/projects/{id} — update
# ---------------------------------------------------------------------------

class TestUpdateProject:
    def test_update_name(self, client: TestClient):
        """Updating only the name changes the name and leaves other fields intact."""
        proj = _create_project(client, name="Old Name", hourly_rate=100.0)
        r = client.put(f"/api/projects/{proj['id']}", json={"name": "New Name"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "New Name"
        assert data["hourly_rate"] == 100.0  # unchanged

    def test_update_multiple_fields(self, client: TestClient):
        """Multiple fields can be updated in a single request."""
        proj = _create_project(client, name="Proj", client_name="OldClient", hourly_rate=50.0)
        r = client.put(f"/api/projects/{proj['id']}", json={
            "client_name": "NewClient",
            "hourly_rate": 200.0,
            "color": "#aabbcc",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["client_name"] == "NewClient"
        assert data["hourly_rate"] == 200.0
        assert data["color"] == "#aabbcc"

    def test_archive_project(self, client: TestClient):
        """Setting archived=True marks the project as archived."""
        proj = _create_project(client, name="To Archive")
        assert proj["archived"] is False

        r = client.put(f"/api/projects/{proj['id']}", json={"archived": True})
        assert r.status_code == 200
        assert r.json()["archived"] is True

    def test_unarchive_project(self, client: TestClient):
        """Setting archived=False on an archived project reactivates it."""
        proj = _create_project(client, name="Was Archived")
        client.put(f"/api/projects/{proj['id']}", json={"archived": True})

        r = client.put(f"/api/projects/{proj['id']}", json={"archived": False})
        assert r.status_code == 200
        assert r.json()["archived"] is False

    def test_update_nonexistent_project_returns_404(self, client: TestClient):
        """Updating a non-existent project returns 404."""
        r = client.put("/api/projects/9999", json={"name": "Ghost"})
        assert r.status_code == 404

    def test_update_empty_body_returns_current_state(self, client: TestClient):
        """An empty update body returns the project unchanged."""
        proj = _create_project(client, name="Stable Project", hourly_rate=80.0)
        r = client.put(f"/api/projects/{proj['id']}", json={})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Stable Project"
        assert data["hourly_rate"] == 80.0


# ---------------------------------------------------------------------------
# DELETE /api/projects/{id} — delete
# ---------------------------------------------------------------------------

class TestDeleteProject:
    def test_delete_project_without_entries(self, client: TestClient):
        """Deleting a project with no time entries returns 204."""
        proj = _create_project(client, name="Empty Project")
        r = client.delete(f"/api/projects/{proj['id']}")
        assert r.status_code == 204

        # Verify it's gone
        r2 = client.get(f"/api/projects/{proj['id']}")
        assert r2.status_code == 404

    def test_delete_project_with_entries_returns_409(self, client: TestClient):
        """Deleting a project that has time entries returns 409 Conflict."""
        proj = _create_project(client, name="Has Entries")
        _create_entry(client, project_id=proj["id"])

        r = client.delete(f"/api/projects/{proj['id']}")
        assert r.status_code == 409
        assert "delete" in r.json()["detail"].lower() or "entr" in r.json()["detail"].lower()

    def test_delete_nonexistent_project_returns_404(self, client: TestClient):
        """Deleting a project that doesn't exist returns 404."""
        r = client.delete("/api/projects/9999")
        assert r.status_code == 404

    def test_delete_after_entries_removed_succeeds(self, client: TestClient):
        """After removing all entries, deleting the project succeeds with 204."""
        proj = _create_project(client, name="Cleanup Project")
        entry = _create_entry(client, project_id=proj["id"])

        # First delete the entry
        r = client.delete(f"/api/entries/{entry['id']}")
        assert r.status_code == 204

        # Now delete the project — should succeed
        r = client.delete(f"/api/projects/{proj['id']}")
        assert r.status_code == 204
