from retrieval.intent_parser import ParsedIntent
from retrieval.scoring.dedup import deduplicate_scored_results, is_near_duplicate_name, name_dedup_key
from retrieval.scoring.travel_rules import TravelRuleScorer


def test_name_dedup_key_strips_prefixes() -> None:
    key = name_dedup_key("Khu du lich Bãi biển Doc Let")
    assert "khu du lich" not in key
    assert "doc let" in key


def test_is_near_duplicate_name() -> None:
    assert is_near_duplicate_name("Bãi biển Doc Let", "Doc Let beach")


def test_deduplicate_scored_results_by_place_id() -> None:
    scored = [
        {"place_id": "a", "title": "One", "final_score": 2},
        {"place_id": "a", "title": "One dup", "final_score": 1},
        {"place_id": "b", "title": "Two", "final_score": 1},
    ]
    out = deduplicate_scored_results(scored, top_k=5)
    assert len(out) == 2
    assert {x["place_id"] for x in out} == {"a", "b"}


def test_travel_rule_province_match() -> None:
    intent = ParsedIntent(
        raw_query="ha giang",
        normalized_query="ha giang",
        intent="search_place",
        province_norm="ha_giang",
        preferred_doc_types=["place"],
    )
    item = {
        "doc_type": "place",
        "metadata": {"province_norm": "ha_giang", "budget_level_norm": "free"},
    }
    score, reasons = TravelRuleScorer().score(item, intent)
    assert score > 0
    assert "match_province" in reasons
