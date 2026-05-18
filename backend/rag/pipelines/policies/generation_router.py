from __future__ import annotations

from typing import Any

from core.config import settings
from llm.response_cache import ResponseCache
from providers.gemini_provider import GeminiProvider, create_gemini_provider
from providers.template_provider import TemplateAnswerProvider


def _empty_generation_meta() -> dict[str, Any]:
    return {
        "gemini_latency_ms": 0,
        "gemini_timeout": False,
        "error": None,
        "error_type": None,
        "retry_after_seconds": None,
        "cache_hit": False,
    }


class GenerationRouter:
    def __init__(
        self,
        response_cache: ResponseCache | None = None,
        gemini_provider: GeminiProvider | None = None,
        template_provider: TemplateAnswerProvider | None = None,
        *,
        _init_gemini: bool = True,
    ) -> None:
        self.response_cache = response_cache or ResponseCache()
        self.template_provider = template_provider or TemplateAnswerProvider()

        if _init_gemini and gemini_provider is None:
            self.gemini_provider = create_gemini_provider()
        else:
            self.gemini_provider = gemini_provider

    def generate(
        self,
        *,
        prompt: str,
        retrieved: dict[str, Any],
        query: str,
        cache_key: str,
    ) -> dict[str, Any]:
        runtime_mode = settings.ai_runtime_mode

        if runtime_mode in {"demo", "gemini_only", "hybrid"}:
            return self._generate_with_gemini_or_template(
                prompt=prompt,
                retrieved=retrieved,
                query=query,
                cache_key=cache_key,
            )

        if runtime_mode == "retrieval_only":
            return {
                "answer": self.template_provider.build_template_answer(retrieved),
                "model_used": "retrieval_template",
                "fallback_used": True,
                **_empty_generation_meta(),
            }

        if runtime_mode == "mock":
            return {
                "answer": self.template_provider.build_mock_answer(retrieved),
                "model_used": "mock",
                "fallback_used": False,
                **_empty_generation_meta(),
            }

        return {
            "answer": self.template_provider.build_template_answer(retrieved),
            "model_used": "unknown_runtime_template",
            "fallback_used": True,
            "error": f"Unknown AI_RUNTIME_MODE={runtime_mode}",
            "error_type": "config_error",
            "gemini_latency_ms": 0,
            "gemini_timeout": False,
            "retry_after_seconds": None,
            "cache_hit": False,
        }

    def _generate_with_gemini_or_template(
        self,
        *,
        prompt: str,
        retrieved: dict[str, Any],
        query: str,
        cache_key: str,
    ) -> dict[str, Any]:
        cached = self.response_cache.get(cache_key)
        if cached:
            return {
                "answer": cached.get("answer", ""),
                "model_used": cached.get("model_used", "gemini_cache"),
                "fallback_used": False,
                **_empty_generation_meta(),
                "cache_hit": True,
            }

        if self.gemini_provider is None:
            return {
                "answer": self.template_provider.build_template_answer(retrieved),
                "model_used": "template_no_gemini",
                "fallback_used": True,
                "error": "Gemini generator is not available",
                "error_type": "gemini_not_available",
                "gemini_latency_ms": 0,
                "gemini_timeout": False,
                "retry_after_seconds": None,
                "cache_hit": False,
            }

        result = self.gemini_provider.generate(prompt)

        if result.get("ok") and result.get("answer"):
            answer_text = result["answer"]
            self.response_cache.set(
                cache_key,
                {
                    "query": query,
                    "answer": answer_text,
                    "model_used": result["model_used"],
                    "runtime_mode": settings.ai_runtime_mode,
                },
            )
            return {
                "answer": answer_text,
                "model_used": result["model_used"],
                "fallback_used": False,
                "gemini_latency_ms": result.get("latency_ms", 0),
                "gemini_timeout": False,
                "error": None,
                "error_type": None,
                "retry_after_seconds": None,
                "cache_hit": False,
            }

        error_text = result.get("error")
        error_type = result.get("error_type")
        retry_after_seconds = result.get("retry_after_seconds")
        is_timeout = bool(result.get("timeout", False))

        if error_text and "timeout" in str(error_text).lower():
            is_timeout = True

        return {
            "answer": self.template_provider.build_template_answer(retrieved),
            "model_used": "template_after_gemini_error",
            "fallback_used": True,
            "gemini_latency_ms": result.get("latency_ms", 0),
            "gemini_timeout": is_timeout,
            "error": error_text,
            "error_type": error_type,
            "retry_after_seconds": retry_after_seconds,
            "cache_hit": False,
        }
