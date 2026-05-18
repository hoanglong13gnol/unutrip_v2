"""Contract parity with Node ragContract.js."""

from __future__ import annotations

from domain.contracts.rag_chat_simple import validate_rag_chat_simple
from services.rag_service import RagService


def test_rag_service_output_matches_contract(mock_pipeline) -> None:
    svc = RagService(mock_pipeline)
    out = svc.rag_chat_simple("test", 5, "balanced", None, None)
    parsed, issues = validate_rag_chat_simple(out)
    assert issues == []
    assert parsed is not None
    assert parsed.model_used == "mock"
    assert parsed.fallback_used is False


def test_contract_rejects_invalid_places_type() -> None:
    _, issues = validate_rag_chat_simple({"answer": "x", "places": "not-a-list"})
    assert issues
