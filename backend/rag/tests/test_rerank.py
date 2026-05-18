"""Phase 5 — rerank helpers (no index file)."""

from __future__ import annotations

from unittest.mock import MagicMock

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from retrieval.rerank import dense_tfidf_rerank, rerank_candidates


def _mock_retriever_with_tfidf(docs: list[dict]) -> MagicMock:
    texts = [f"{d.get('title')} {d.get('text')}" for d in docs]
    vec = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
    x = vec.fit_transform(texts)
    x_norm = normalize(x)
    retriever = MagicMock()
    retriever.has_tfidf.return_value = True
    retriever.tfidf_vectorizer = vec
    retriever.tfidf_X_norm = x_norm
    retriever.docs = docs
    return retriever


def test_dense_tfidf_rerank_promotes_matching_doc() -> None:
    docs = [
        {"doc_id": "a", "title": "Bai bien Nha Trang", "text": "tam bien khanh hoa"},
        {"doc_id": "b", "title": "Dinh Hue", "text": "van hoa"},
    ]
    retriever = _mock_retriever_with_tfidf(docs)
    items = [
        {"doc_id": "b", "title": "Dinh Hue", "text": "van hoa", "score": 10.0, "final_score": 10.0},
        {"doc_id": "a", "title": "Bai bien Nha Trang", "text": "tam bien", "score": 5.0, "final_score": 5.0},
    ]
    out = dense_tfidf_rerank("bien nha trang", items, retriever, top_k=2)
    assert out[0]["doc_id"] == "a"
    assert out[0].get("dense_score", 0) > 0


def test_rerank_candidates_disabled(monkeypatch) -> None:
    monkeypatch.setattr("retrieval.rerank.settings.enable_rerank", False)
    items = [{"doc_id": "x", "final_score": 1.0}]
    out, mode = rerank_candidates("q", items, retriever=MagicMock(), top_k=1)
    assert mode == "disabled"
    assert len(out) == 1
