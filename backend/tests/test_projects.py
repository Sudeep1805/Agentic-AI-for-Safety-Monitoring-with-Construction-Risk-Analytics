def project_payload(code="PRJ-001"):
    return {
        "name": "North Campus Build",
        "code": code,
        "description": "Safety monitoring pilot site",
        "construction_type": "Commercial",
        "project_manager": "Asha Rao",
        "site_address": "12 Main Road",
        "city": "Coimbatore",
        "state": "Tamil Nadu",
        "pin_code": "641001",
        "status": "Planning",
        "start_date": "2026-01-10",
        "expected_completion_date": "2026-12-31",
        "budget": 1250000,
        "number_of_workers": 35,
        "safety_officer": "Kiran Das",
        "safety_notes": "Daily PPE checks",
    }


def test_projects_require_authentication(client):
    client.headers.pop("Authorization")
    assert client.get("/api/projects").status_code == 401
    assert client.post("/api/projects", json=project_payload()).status_code == 401


def test_projects_support_crud_and_duplicate_codes(client):
    created = client.post("/api/projects", json=project_payload())
    assert created.status_code == 201
    project = created.json()
    assert project["city"] == "Coimbatore"
    assert client.get("/api/projects").json()["total"] == 1
    assert client.get(f"/api/projects/{project['id']}").json()["id"] == project["id"]

    duplicate = client.post("/api/projects", json=project_payload())
    assert duplicate.status_code == 409

    changed = project_payload("PRJ-002")
    changed["status"] = "Active"
    updated = client.put(f"/api/projects/{project['id']}", json=changed)
    assert updated.status_code == 200
    assert updated.json()["status"] == "Active"

    assert client.delete(f"/api/projects/{project['id']}").status_code == 204
    assert client.get("/api/projects").json() == {"items": [], "total": 0}


def test_projects_validate_dates_and_numbers(client):
    invalid = project_payload()
    invalid["expected_completion_date"] = "2025-01-01"
    assert client.post("/api/projects", json=invalid).status_code == 422
    invalid = project_payload("PRJ-003")
    invalid["number_of_workers"] = -1
    assert client.post("/api/projects", json=invalid).status_code == 422
