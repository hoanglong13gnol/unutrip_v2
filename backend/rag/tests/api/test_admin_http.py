"""HTTP tests for admin routes (mocked pipeline)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_admin_ai_logs_empty(api_client: TestClient) -> None:
    r = api_client.get("/admin/ai/logs", params={"limit": 5})
    assert r.status_code == 200
    body = r.json()
    assert "logs" in body
    assert isinstance(body["logs"], list)


def test_admin_rag_status(api_client: TestClient) -> None:
    r = api_client.get("/admin/rag/status")
    assert r.status_code == 200
    assert "files" in r.json()


def test_admin_retrieve_debug(api_client: TestClient) -> None:
    r = api_client.post(
        "/admin/rag/retrieve-debug",
        json={"message": "Khánh Hòa", "top_k": 5},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "Khánh Hòa"
    assert len(body["results"]) >= 1
