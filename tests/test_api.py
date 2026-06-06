"""Tests for the FastAPI report server."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import REPORTS_DIR, app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_LOGS = PROJECT_ROOT / "tests" / "sample_logs"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_reports(tmp_path, monkeypatch):
    monkeypatch.setattr("api.main.REPORTS_DIR", tmp_path / "reports")
    yield


def test_list_incidents_empty(client):
    response = client.get("/api/incidents")
    assert response.status_code == 200
    assert response.json() == []


def test_run_analysis_and_fetch_report(client):
    response = client.post(
        "/api/run",
        json={
            "log_paths": [
                "tests/sample_logs/orders.log",
                "tests/sample_logs/payment.log",
            ],
            "metrics_path": "tests/sample_logs/prom.json",
            "since": "2024-01-01T02:11:00",
            "explain": False,
        },
    )
    assert response.status_code == 200
    report = response.json()
    assert "id" in report
    assert report["root_causes"]
    assert report["graph"]["nodes"]

    incident_id = report["id"]

    list_response = client.get("/api/incidents")
    assert list_response.status_code == 200
    summaries = list_response.json()
    assert len(summaries) == 1
    assert summaries[0]["id"] == incident_id

    detail_response = client.get(f"/api/incidents/{incident_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == incident_id

    graph_response = client.get(f"/api/incidents/{incident_id}/graph")
    assert graph_response.status_code == 200
    graph = graph_response.json()
    assert "nodes" in graph
    assert "links" in graph
    assert "edges" in graph
    assert graph["edges"] == graph["links"]


def test_get_missing_incident_returns_404(client):
    response = client.get("/api/incidents/does-not-exist")
    assert response.status_code == 404


def test_run_rejects_missing_log_path(client):
    response = client.post(
        "/api/run",
        json={"log_paths": ["tests/sample_logs/missing.log"]},
    )
    assert response.status_code == 400
