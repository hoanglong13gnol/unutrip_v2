from __future__ import annotations

import logging
from typing import Any

from retrieval.logger import AiRequestLogger

logger = logging.getLogger(__name__)


def log_rag_request(ai_logger: AiRequestLogger, query: str, response: dict[str, Any]) -> None:
    try:
        places = response.get("places", [])
        debug = response.get("debug", {})

        record = {
            "query": query,
            "runtime_mode": response.get("runtime_mode"),
            "rag_mode": response.get("rag_mode"),
            "model_used": response.get("model_used"),
            "fallback_used": response.get("fallback_used"),
            "latency_ms": response.get("latency_ms", {}),
            "top_place_ids": [place.get("place_id") for place in places[:10]],
            "top_place_names": [place.get("name") for place in places[:10]],
            "warnings_count": len(response.get("warnings", [])),
            "generation_error": debug.get("generation_error"),
            "generation_error_type": debug.get("generation_error_type"),
            "retry_after_seconds": debug.get("retry_after_seconds"),
            "gemini_timeout": debug.get("gemini_timeout", False),
            "cache_hit": debug.get("cache_hit", False),
            "intent": debug.get("intent"),
            "target_province": debug.get("target_province"),
            "target_city": debug.get("target_city"),
        }

        ai_logger.log(record)
    except Exception as exc:
        logger.warning("Failed to write AI request log: %s", exc)
