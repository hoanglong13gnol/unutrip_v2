"""Phase 5 — retrieval integration on tracked fixture index (hit@5 + province)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from retrieval.hybrid_retriever import HybridRetriever

EVAL_DIR = Path(__file__).resolve().parents[1] / "eval"
GOLDEN_CI = EVAL_DIR / "golden_queries_ci.json"


def _hit_at_k(relevant: set[str], ranked: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    return 1.0 if any(r in relevant for r in ranked[:k]) else 0.0


@pytest.mark.usefixtures("fixture_bm25_index")
def test_golden_ci_hit_at5_and_province() -> None:
    cases = json.loads(GOLDEN_CI.read_text(encoding="utf-8"))
    retriever = HybridRetriever()

    hits: list[float] = []
    prov_ok = 0
    prov_total = 0

    for row in cases:
        q = row["query"]
        rel = {str(x) for x in (row.get("relevant_place_ids") or []) if x}
        out = retriever.retrieve(q, top_k=int(row.get("top_k", 8)))
        ranked = [str(x.get("place_id")) for x in out.get("results", []) if x.get("place_id")]

        if rel:
            hits.append(_hit_at_k(rel, ranked, 5))

        exp = row.get("expect_province_norm")
        if exp:
            prov_total += 1
            intent = (out.get("intent") or {}).get("province_norm")
            if intent == exp:
                prov_ok += 1

        assert out.get("debug", {}).get("rerank_mode") in {
            "dense_tfidf",
            "cross_encoder",
            "lexical_only",
            "disabled",
        }

    assert hits, "golden_queries_ci must include relevant_place_ids"
    assert sum(hits) / len(hits) >= 0.5
    if prov_total:
        assert prov_ok / prov_total >= 1.0


@pytest.mark.usefixtures("fixture_bm25_index")
def test_rrf_fusion_active_on_fixture_index() -> None:
    retriever = HybridRetriever()
    out = retriever.retrieve("bien nha trang khanh hoa", top_k=5)
    fusion = out.get("debug", {}).get("fusion") or {}
    assert fusion.get("mode") == "rrf_bm25_tfidf"
