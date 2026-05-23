"""P3 — RagPipeline.run with mocked retrieval/generation (no BM25/Gemini)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from pipelines.rag_pipeline import RagPipeline
from retrieval.intent_parser import ParsedIntent


def _parsed(*, intent: str = "search_place", days: int | None = None) -> ParsedIntent:
    return ParsedIntent(
        raw_query="q",
        normalized_query="q",
        intent=intent,
        days=days,
        preferred_doc_types=["place"] if intent != "itinerary" else ["itinerary", "place"],
    )


def _retrieved() -> dict[str, Any]:
    return {
        "intent": "search_place",
        "results": [
            {
                "place_id": "P1",
                "title": "Điểm A",
                "metadata": {"province": "Hà Giang"},
            }
        ],
        "debug": {},
    }


@pytest.fixture
def pipeline_parts(monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
    mock_retriever = MagicMock()
    mock_retriever.intent_parser.parse.return_value = _parsed()
    mock_retriever.retrieve.return_value = _retrieved()

    mock_filter = MagicMock()
    mock_filter.apply.side_effect = lambda retrieved, **_kw: retrieved

    mock_router = MagicMock()
    mock_router.generate.return_value = {
        "answer": "Trả lời test",
        "model_used": "template",
        "fallback_used": False,
        "gemini_latency_ms": 0,
    }

    mock_ai_logger = MagicMock()
    mock_cache = MagicMock()
    mock_cache.make_key.return_value = "cache-key"

    mock_context = MagicMock()
    mock_context.build_context.return_value = "CONTEXT"
    mock_prompt = MagicMock()
    mock_prompt.build_prompt.return_value = "PROMPT"

    monkeypatch.setattr("pipelines.rag_pipeline.HybridRetriever", lambda: mock_retriever)
    monkeypatch.setattr("pipelines.rag_pipeline.PlaceStore", lambda: MagicMock())
    monkeypatch.setattr("pipelines.rag_pipeline.LocationFilter", lambda _ps: mock_filter)
    monkeypatch.setattr("pipelines.rag_pipeline.GenerationRouter", lambda **_kw: mock_router)
    monkeypatch.setattr("pipelines.rag_pipeline.AiRequestLogger", lambda: mock_ai_logger)
    monkeypatch.setattr("pipelines.rag_pipeline.ContextBuilder", lambda: mock_context)
    monkeypatch.setattr("pipelines.rag_pipeline.PromptBuilder", lambda: mock_prompt)
    monkeypatch.setattr("pipelines.rag_pipeline.ResponseCache", lambda: mock_cache)

    return {
        "retriever": mock_retriever,
        "filter": mock_filter,
        "router": mock_router,
        "ai_logger": mock_ai_logger,
        "cache": mock_cache,
    }


def test_rag_pipeline_run_happy_path(pipeline_parts: dict[str, MagicMock]) -> None:
    pipe = RagPipeline()
    out = pipe.run("điểm tham quan hà giang", top_k=6, include_prompt=True)

    assert out["answer"] == "Trả lời test"
    assert out["model_used"] == "template"
    assert len(out["places"]) == 1
    assert out["prompt"] == "PROMPT"
    assert out["context"] == "CONTEXT"
    assert out["debug"]["cache_hit"] is False
    assert out["latency_ms"]["total"] >= 0

    pipeline_parts["retriever"].retrieve.assert_called_once_with(
        "điểm tham quan hà giang", top_k=6, province_norm_override=None
    )
    pipeline_parts["router"].generate.assert_called_once()
    pipeline_parts["ai_logger"].log.assert_called_once()


def test_rag_pipeline_omits_prompt_when_disabled(pipeline_parts: dict[str, MagicMock]) -> None:
    pipe = RagPipeline()
    out = pipe.run("q", include_prompt=False)
    assert "prompt" not in out
    assert "context" not in out


def test_rag_pipeline_itinerary_raises_top_k(pipeline_parts: dict[str, MagicMock]) -> None:
    pipeline_parts["retriever"].intent_parser.parse.return_value = _parsed(intent="itinerary", days=3)
    pipe = RagPipeline()
    pipe.run("lịch trình 3 ngày", top_k=6)
    pipeline_parts["retriever"].retrieve.assert_called_once_with(
        "lịch trình 3 ngày", top_k=9, province_norm_override=None
    )
