"""HTTP tests for health routes."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok(api_client: TestClient) -> None:
    r = api_client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_health_ready_without_pipeline_returns_503(api_client: TestClient) -> None:
    api_client.app.state.pipeline = None
    r = api_client.get("/health/ready")
    assert r.status_code == 503
    assert r.json()["pipeline_loaded"] is False


def test_health_ready_with_mock_pipeline(api_client: TestClient) -> None:
    r = api_client.get("/health/ready")
    body = r.json()
    assert body["pipeline_loaded"] is True
