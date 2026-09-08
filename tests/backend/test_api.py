import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_filters():
    response = client.get("/filters")
    assert response.status_code == 200
    data = response.json()
    assert "states" in data
    assert "categories" in data
    assert "statuses" in data
    assert "risk_levels" in data
    assert len(data["states"]) > 0

def test_statistics():
    response = client.get("/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "total_works" in data["kpis"]
    assert data["kpis"]["total_works"] > 0
    assert "data_quality" in data

def test_projects_pagination_and_sorting():
    response = client.get("/projects?page=1&page_size=10&sort=risk_score&order=desc")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 10
    assert data["pagination"]["total"] > 0
    
    # Check sorted descending
    scores = [p["risk_score"] for p in data["data"]]
    assert scores == sorted(scores, reverse=True)

def test_projects_filtering():
    response = client.get("/projects?risk_level=High")
    assert response.status_code == 200
    data = response.json()
    for p in data["data"]:
        assert p["risk_category"] == "High"

def test_project_detail_and_notes():
    # Get first project ID
    list_res = client.get("/projects?page=1&page_size=1")
    first_id = list_res.json()["data"][0]["project_id"]
    
    # Post an investigation note
    note_payload = {"note_text": "Auditor reviewed this project on site.", "created_by": "Senior Inspector"}
    post_res = client.post(f"/projects/{first_id}/notes", json=note_payload)
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "success"
    
    # Detail check
    detail_res = client.get(f"/projects/{first_id}")
    assert detail_res.status_code == 200
    p_data = detail_res.json()["data"]
    assert p_data["project_id"] == first_id
    assert "alerts" in p_data
    assert "notes" in p_data
    assert len(p_data["notes"]) > 0
    assert p_data["notes"][0]["note_text"] == "Auditor reviewed this project on site."
    assert "peer_comparison" in p_data
    assert "provenance" in p_data

def test_unknown_project_404():
    unknown_res = client.get("/projects/NON_EXISTENT_ID_99999")
    assert unknown_res.status_code == 404
