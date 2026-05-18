from __future__ import annotations

from typing import Any, Protocol


class GenerationProvider(Protocol):
    """LLM or template backend invoked by GenerationRouter."""

    def generate(self, prompt: str) -> dict[str, Any]:
        """Return dict with ok/answer/error fields (Gemini-compatible shape)."""
