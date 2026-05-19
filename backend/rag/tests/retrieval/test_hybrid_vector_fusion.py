"""HybridRetriever with mocked vector channel."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from core.config import settings
from retrieval.hybrid_retriever import HybridRetriever


@pytest.mark.usefixtures("fixture_bm25_index")
def test_hybrid_fuses_vector_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "enable_vector_retrieval", True)
    monkeypatch.setattr(
        "retrieval.hybrid_retriever.vector_retrieval_active",
        lambda: True,
    )

    r = HybridRetriever()
    r._vector_active = True
    r.vector.search = MagicMock(
        return_value=[
            {
                "doc_id": "vec_only",
                "score": 0.9,
                "doc_type": "place",
                "title": "Vector Only",
                "text": "",
                "metadata": {},
            }
        ]
    )

    out = r.retrieve("du lịch biển", top_k=5)
    fusion = out["debug"]["fusion"]
    assert fusion.get("vector_active") is True
    assert "vector" in fusion.get("mode", "") or fusion.get("lists", {}).get("vector")
    r.vector.search.assert_called_once()
