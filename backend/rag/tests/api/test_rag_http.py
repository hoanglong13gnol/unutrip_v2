"""HTTP tests for public RAG routes (mocked pipeline)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from domain.contracts.rag_chat_simple import validate_rag_chat_simple


def test_rag_chat_simple_returns_contract_shape(api_client: TestClient) -> None:
    r = api_client.post(
        "/rag/chat/simple",
        json={"message": "đi biển Khánh Hòa", "top_k": 5, "mode": "balanced"},
    )
    assert r.status_code == 200
    parsed, issues = validate_rag_chat_simple(r.json())
    assert issues == []
    assert parsed is not None
    assert isinstance(parsed.answer, str)
    assert len(parsed.places) >= 1
    assert parsed.places[0].place_id == "AG_0001"


def test_rag_chat_simple_v1_prefix(api_client: TestClient) -> None:
    r = api_client.post("/v1/rag/chat/simple", json={"message": "hello"})
    assert r.status_code == 200
    assert "answer" in r.json()


def test_rag_retrieve(api_client: TestClient) -> None:
    r = api_client.post("/rag/retrieve", json={"message": "Huế", "top_k": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "Huế"
    assert "results" in body
    assert len(body["results"]) >= 1


def test_legacy_chat_post(api_client: TestClient) -> None:
    r = api_client.post("/chat", json={"message": "xin chào"})
    assert r.status_code == 200
    assert "answer" in r.json()


def test_validation_error_envelope(api_client: TestClient) -> None:
    r = api_client.post("/rag/chat/simple", json={})
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "validation_error"
    assert "request_id" in body
