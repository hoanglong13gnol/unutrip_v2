from __future__ import annotations

import logging
from typing import Any, cast

from core.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider:
    def __init__(self, inner: Any | None = None) -> None:
        self._inner = inner

    def generate(self, prompt: str) -> dict[str, Any]:
        if self._inner is None:
            return {
                "ok": False,
                "error": "Gemini generator is not available",
                "error_type": "gemini_not_available",
            }
        return cast(dict[str, Any], self._inner.generate(prompt))


def create_gemini_provider() -> GeminiProvider | None:
    if not settings.enable_gemini or settings.ai_runtime_mode not in {
        "demo",
        "gemini_only",
        "hybrid",
    }:
        return None

    try:
        from llm.gemini_generator import GeminiGenerator

        return GeminiProvider(GeminiGenerator())
    except Exception as exc:
        logger.warning("Gemini provider init failed: %s", exc)
        return None
