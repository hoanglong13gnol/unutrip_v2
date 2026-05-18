"""Additional rerank branches."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from retrieval import rerank as rerank_mod
from retrieval.rerank import dense_tfidf_rerank, maybe_cross_encoder_rerank, rerank_candidates


def test_dense_tfidf_rerank_empty_or_no_tfidf() -> None:
    retriever = MagicMock()
    retriever.has_tfidf.return_value = False
    items = [{"doc_id": "a", "final_score": 1.0}]
    assert dense_tfidf_rerank("q", items, retriever, top_k=3) == items

    retriever.has_tfidf.return_value = True
    retriever.tfidf_vectorizer = None
    retriever.tfidf_X_norm = None
    assert dense_tfidf_rerank("q", items, retriever, top_k=3) == items


def test_rerank_candidates_lexical_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("retrieval.rerank.settings.enable_rerank", True)
    monkeypatch.setattr("retrieval.rerank.settings.enable_cross_encoder", False)
    retriever = MagicMock()
    retriever.has_tfidf.return_value = False
    items = [{"doc_id": "x", "final_score": 2.0}, {"doc_id": "y", "final_score": 1.0}]
    out, mode = rerank_candidates("q", items, retriever=retriever, top_k=1)
    assert mode == "lexical_only"
    assert len(out) == 1


def test_maybe_cross_encoder_disabled() -> None:
    items = [{"doc_id": "a"}]
    assert maybe_cross_encoder_rerank("q", items, top_k=2, enabled=False) == items[:2]


def test_cross_encoder_skips_when_load_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rerank_mod, "_CROSS_ENCODER_LOAD_FAILED", True)
    items = [{"title": "t", "text": "b", "final_score": 3.0}]
    out = rerank_mod.cross_encoder_rerank("q", items, top_k=2)
    assert out == items[:2]
