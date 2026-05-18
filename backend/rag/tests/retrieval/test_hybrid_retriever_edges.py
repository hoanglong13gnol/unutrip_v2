"""HybridRetriever branches (fixture index)."""

from __future__ import annotations

import pytest

from core.config import settings
from retrieval.hybrid_retriever import HybridRetriever


@pytest.mark.usefixtures("fixture_bm25_index")
def test_hybrid_backward_compat_helpers() -> None:
    r = HybridRetriever()
    assert r._name_dedup_key("Bãi biển Doc Let")
    assert isinstance(r._is_near_duplicate_name("Doc Let", "Bai bien Doc Let"), bool)
    item = {"title": "X", "doc_type": "place", "metadata": {"province_norm": "ha_giang"}}
    intent = r.intent_parser.parse("ha giang")
    score, reasons = r._travel_rule_score(item, intent)
    assert isinstance(score, float)
    assert isinstance(reasons, list)


@pytest.mark.usefixtures("fixture_bm25_index")
def test_hybrid_bm25_only_when_rrf_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        settings,
        "enable_rrf_fusion",
        False,
    )
    r = HybridRetriever()
    out = r.retrieve("bien", top_k=3)
    assert out["debug"]["fusion"]["mode"] == "bm25_only"
    assert out["results"]


@pytest.mark.usefixtures("fixture_bm25_index")
def test_hybrid_itinerary_intent_in_response() -> None:
    r = HybridRetriever()
    out = r.retrieve("lịch trình đi hà giang 2 ngày", top_k=6)
    assert out["intent"]["intent"] == "itinerary"
    assert out["intent"]["province_norm"] == "ha_giang"
