"""Domain models (retrieval / RAG contracts, not HTTP)."""

from domain.models import RagRequest, RagResponse, RetrievedPlace, UserIntent

__all__ = ["RagRequest", "RagResponse", "RetrievedPlace", "UserIntent"]
