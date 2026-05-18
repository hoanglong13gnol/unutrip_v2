from __future__ import annotations

import time

import pytest

from llm.gemini_generator import GeminiGenerator


def test_classify_quota_error() -> None:
    gen = GeminiGenerator.__new__(GeminiGenerator)
    assert gen._classify_error("429 RESOURCE_EXHAUSTED quota exceeded") == "quota_exceeded"


def test_classify_auth_error() -> None:
    gen = GeminiGenerator.__new__(GeminiGenerator)
    assert gen._classify_error("API key not valid") == "auth_error"


def test_extract_retry_after_seconds() -> None:
    gen = GeminiGenerator.__new__(GeminiGenerator)
    text = "Please retry in 42.5s."
    assert gen._extract_retry_after_seconds(text) == 42


def test_circuit_open_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    GeminiGenerator._circuit_open_until = time.time() + 60
    GeminiGenerator._quota_streak = 0

    gen = GeminiGenerator.__new__(GeminiGenerator)
    gen.model_name = "test-model"
    gen.timeout_seconds = 5

    result = gen.generate("hello")
    assert result["ok"] is False
    assert result["error_type"] == "circuit_open"
    assert result["retry_after_seconds"] is not None

    GeminiGenerator._circuit_open_until = 0.0
