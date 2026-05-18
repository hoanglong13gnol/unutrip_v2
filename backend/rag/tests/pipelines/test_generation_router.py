from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from pipelines.policies import generation_router
from pipelines.policies.generation_router import GenerationRouter
from providers.gemini_provider import GeminiProvider
from providers.template_provider import TemplateAnswerProvider


def _patch_runtime(monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    monkeypatch.setattr(
        generation_router,
        "settings",
        generation_router.settings.model_copy(update={"ai_runtime_mode": mode}),
    )

RETRIEVED: dict[str, Any] = {
    "intent": {"intent": "search_place"},
    "results": [
        {
            "place_id": "P1",
            "title": "Điểm A",
            "metadata": {"province": "Hà Giang"},
        }
    ],
}


@pytest.fixture
def template_provider() -> TemplateAnswerProvider:
    return TemplateAnswerProvider()


def test_generation_router_mock_mode(
    monkeypatch: pytest.MonkeyPatch,
    template_provider: TemplateAnswerProvider,
) -> None:
    _patch_runtime(monkeypatch, "mock")

    router = GenerationRouter(
        gemini_provider=None,
        template_provider=template_provider,
        _init_gemini=False,
    )
    out = router.generate(
        prompt="p",
        retrieved=RETRIEVED,
        query="q",
        cache_key="k-mock",
    )
    assert out["model_used"] == "mock"
    assert "mock" in out["answer"].lower()
    assert out["fallback_used"] is False


def test_generation_router_retrieval_only(
    monkeypatch: pytest.MonkeyPatch,
    template_provider: TemplateAnswerProvider,
) -> None:
    _patch_runtime(monkeypatch, "retrieval_only")

    router = GenerationRouter(
        gemini_provider=None,
        template_provider=template_provider,
        _init_gemini=False,
    )
    out = router.generate(
        prompt="p",
        retrieved=RETRIEVED,
        query="q",
        cache_key="k-ro",
    )
    assert out["model_used"] == "retrieval_template"
    assert out["fallback_used"] is True
    assert "Điểm A" in out["answer"]


def test_generation_router_cache_hit(
    monkeypatch: pytest.MonkeyPatch,
    template_provider: TemplateAnswerProvider,
) -> None:
    cache = MagicMock()
    cache.get.return_value = {"answer": "cached answer", "model_used": "gemini_cache"}

    _patch_runtime(monkeypatch, "demo")

    router = GenerationRouter(
        response_cache=cache,
        gemini_provider=None,
        template_provider=template_provider,
        _init_gemini=False,
    )
    out = router.generate(
        prompt="p",
        retrieved=RETRIEVED,
        query="q",
        cache_key="hit-key",
    )

    assert out["cache_hit"] is True
    assert out["answer"] == "cached answer"


def test_generation_router_gemini_success(
    monkeypatch: pytest.MonkeyPatch,
    template_provider: TemplateAnswerProvider,
) -> None:
    gemini = MagicMock(spec=GeminiProvider)
    gemini.generate.return_value = {
        "ok": True,
        "answer": "Gemini trả lời",
        "model_used": "gemini-test",
        "latency_ms": 12.5,
    }
    cache = MagicMock()
    cache.get.return_value = None

    _patch_runtime(monkeypatch, "demo")

    router = GenerationRouter(
        response_cache=cache,
        gemini_provider=gemini,
        template_provider=template_provider,
        _init_gemini=False,
    )
    out = router.generate(
        prompt="p",
        retrieved=RETRIEVED,
        query="q",
        cache_key="gem-ok",
    )

    assert out["answer"] == "Gemini trả lời"
    assert out["model_used"] == "gemini-test"
    cache.set.assert_called_once()


def test_generation_router_gemini_timeout_fallback(
    monkeypatch: pytest.MonkeyPatch,
    template_provider: TemplateAnswerProvider,
) -> None:
    gemini = MagicMock(spec=GeminiProvider)
    gemini.generate.return_value = {
        "ok": False,
        "error": "Gemini timeout after 30s",
        "error_type": "timeout",
        "timeout": True,
        "latency_ms": 30000,
    }
    cache = MagicMock()
    cache.get.return_value = None

    _patch_runtime(monkeypatch, "gemini_only")

    router = GenerationRouter(
        response_cache=cache,
        gemini_provider=gemini,
        template_provider=template_provider,
        _init_gemini=False,
    )
    out = router.generate(
        prompt="p",
        retrieved=RETRIEVED,
        query="q",
        cache_key="gem-err",
    )

    assert out["model_used"] == "template_after_gemini_error"
    assert out["gemini_timeout"] is True
    assert out["fallback_used"] is True
