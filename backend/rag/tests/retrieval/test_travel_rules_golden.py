"""Golden-style unit tests for TravelRuleScorer (Phase F seed)."""

from retrieval.intent_parser import ParsedIntent
from retrieval.scoring.travel_rules import TravelRuleScorer


def _intent(**kwargs) -> ParsedIntent:
    base = dict(
        raw_query="q",
        normalized_query="q",
        intent="search_place",
        preferred_doc_types=["place"],
    )
    base.update(kwargs)
    return ParsedIntent(**base)


def test_beach_interest_boosts_doc_let() -> None:
    intent = _intent(interests=["beach"], province_norm="khanh_hoa")
    item = {
        "title": "Bãi biển Doc Let",
        "text": "bien dep",
        "doc_type": "place",
        "metadata": {"province_norm": "khanh_hoa"},
    }
    score, reasons = TravelRuleScorer().score(item, intent)
    assert score > 20
    assert "exact_beach_title_match" in reasons


def test_beach_interest_penalizes_waterfall() -> None:
    intent = _intent(interests=["beach"])
    item = {
        "title": "Thác Datanla",
        "text": "thac nuoc",
        "doc_type": "place",
        "metadata": {},
    }
    score, reasons = TravelRuleScorer().score(item, intent)
    assert score < 0
    assert "non_beach_title_penalty" in reasons


def test_kid_friendly_boost() -> None:
    intent = _intent(has_children=True)
    item = {
        "doc_type": "place",
        "metadata": {"kid_friendly_norm": True},
    }
    score, reasons = TravelRuleScorer().score(item, intent)
    assert "kid_friendly" in reasons
    assert score >= 10


def test_itinerary_doc_type_bonus() -> None:
    intent = _intent(intent="itinerary", preferred_doc_types=["itinerary"])
    item = {"doc_type": "itinerary", "metadata": {}}
    score, reasons = TravelRuleScorer().score(item, intent)
    assert "itinerary_doc" in reasons
    assert score >= 8
