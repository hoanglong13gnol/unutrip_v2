"""Unit tests for RRF recall fusion."""

from __future__ import annotations

from retrieval.recall_fusion import fuse_ranked_hit_lists


def _hit(doc_id: str, score: float = 1.0) -> dict:
    return {"doc_id": doc_id, "score": score, "title": doc_id}


def test_fuse_single_list_passthrough() -> None:
    hits = [_hit("a"), _hit("b")]
    fused, debug = fuse_ranked_hit_lists([("bm25", hits)], limit=10)
    assert fused == hits
    assert debug["mode"] == "bm25"


def test_fuse_rrf_merges_unique_docs() -> None:
    bm25 = [_hit("a", 10), _hit("b", 9)]
    vector = [_hit("c", 8), _hit("a", 7)]
    fused, debug = fuse_ranked_hit_lists([("bm25", bm25), ("vector", vector)], limit=10)
    ids = [h["doc_id"] for h in fused]
    assert "a" in ids and "b" in ids and "c" in ids
    assert debug["mode"] == "rrf_bm25_vector"
    assert fused[0].get("rrf_score") is not None
