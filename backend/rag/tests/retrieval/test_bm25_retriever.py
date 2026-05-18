"""BM25Retriever on session fixture index."""

from __future__ import annotations

from pathlib import Path

import pytest

from retrieval.bm25_retriever import BM25Retriever


@pytest.mark.usefixtures("fixture_bm25_index")
def test_bm25_load_and_search() -> None:
    retriever = BM25Retriever()
    retriever.load()
    assert retriever.docs
    assert retriever.has_tfidf()

    hits = retriever.search("bien nha trang", top_k=5)
    assert hits
    assert all(h.get("score", 0) > 0 for h in hits)
    assert hits[0].get("doc_id")


@pytest.mark.usefixtures("fixture_bm25_index")
def test_bm25_search_province_filter() -> None:
    retriever = BM25Retriever()
    hits = retriever.search("diem tham quan", top_k=20, province_norm="ha_giang")
    for h in hits:
        meta = h.get("metadata") or {}
        assert meta.get("province_norm") == "ha_giang"


@pytest.mark.usefixtures("fixture_bm25_index")
def test_bm25_search_tfidf() -> None:
    retriever = BM25Retriever()
    retriever.load()
    hits = retriever.search_tfidf("ha giang", top_k=5, doc_types=["place"])
    assert hits
    assert hits[0]["score"] > 0


@pytest.mark.usefixtures("fixture_bm25_index")
def test_bm25_search_doc_types_filter() -> None:
    retriever = BM25Retriever()
    hits = retriever.search("lich trinh", top_k=10, doc_types=["itinerary"])
    assert all(h.get("doc_type") == "itinerary" for h in hits)


def test_bm25_missing_index_raises(tmp_path: Path) -> None:
    retriever = BM25Retriever(index_file=tmp_path / "no_index.pkl")
    with pytest.raises(FileNotFoundError, match="BM25 index not found"):
        retriever.load()
