"""Backward-compatible re-exports; prefer `domain.models`."""

from domain.models import RagRequest, RagResponse, RetrievedPlace, UserIntent

__all__ = ["RagRequest", "RagResponse", "RetrievedPlace", "UserIntent"]
