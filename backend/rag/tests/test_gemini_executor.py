"""Phase 6 — shared Gemini executor."""

from __future__ import annotations

from llm.gemini_executor import get_gemini_executor, shutdown_gemini_executor


def test_executor_is_singleton() -> None:
    shutdown_gemini_executor(wait=False)
    first = get_gemini_executor()
    second = get_gemini_executor()
    assert first is second
    shutdown_gemini_executor(wait=False)
