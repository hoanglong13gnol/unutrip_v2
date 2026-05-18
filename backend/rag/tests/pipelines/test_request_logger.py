"""P3 — request_logger resilience."""

from __future__ import annotations

from unittest.mock import MagicMock

from pipelines.request_logger import log_rag_request


def test_log_rag_request_records_summary() -> None:
    ai_logger = MagicMock()
    response = {
        "runtime_mode": "mock",
        "rag_mode": "balanced",
        "model_used": "template",
        "fallback_used": False,
        "places": [{"place_id": "P1", "name": "A"}],
        "warnings": [],
        "latency_ms": {"total": 12.5},
        "debug": {
            "intent": "search_place",
            "generation_error": None,
            "generation_error_type": None,
            "retry_after_seconds": None,
            "gemini_timeout": False,
            "cache_hit": True,
            "target_province": "Hà Giang",
            "target_city": None,
        },
    }
    log_rag_request(ai_logger, query="hello", response=response)
    ai_logger.log.assert_called_once()
    record = ai_logger.log.call_args[0][0]
    assert record["query"] == "hello"
    assert record["top_place_ids"] == ["P1"]
    assert record["cache_hit"] is True


def test_log_rag_request_swallows_logger_failure() -> None:
    ai_logger = MagicMock()
    ai_logger.log.side_effect = RuntimeError("disk full")
    log_rag_request(ai_logger, query="q", response={"places": [], "debug": {}, "latency_ms": {}})
