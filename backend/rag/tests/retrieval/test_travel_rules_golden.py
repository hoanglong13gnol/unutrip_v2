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


def test_province_match_boost() -> None:
    intent = _intent(province_norm="thua_thien_hue")
    item = {"doc_type": "place", "metadata": {"province_norm": "thua_thien_hue"}}
    score, reasons = TravelRuleScorer().score(item, intent)
    assert "match_province" in reasons
    assert score >= 15


def test_free_budget_match_and_penalty() -> None:
    intent = _intent(budget_level="free")
    free_item = {"doc_type": "place", "metadata": {"budget_level_norm": "free"}}
    luxury_item = {"doc_type": "place", "metadata": {"budget_level_norm": "luxury"}}
    scorer = TravelRuleScorer()
    _, free_reasons = scorer.score(free_item, intent)
    luxury_score, luxury_reasons = scorer.score(luxury_item, intent)
    assert "match_free_budget" in free_reasons
    assert "not_free" in luxury_reasons
    assert luxury_score < 0


def test_elderly_and_hard_walking_penalty() -> None:
    intent = _intent(has_elderly=True)
    item = {
        "doc_type": "place",
        "metadata": {"elderly_friendly_norm": False, "walking_level_norm": "hard"},
    }
    score, reasons = TravelRuleScorer().score(item, intent)
    assert "not_elderly_friendly" in reasons
    assert "hard_walking_penalty" in reasons
    assert score < 0


def test_time_slot_match_and_mismatch() -> None:
    intent = _intent(time_slot="morning")
    match_item = {"doc_type": "place", "metadata": {"slot_norm": "morning"}}
    mismatch_item = {"doc_type": "place", "metadata": {"slot_norm": "evening"}}
    scorer = TravelRuleScorer()
    _, match_reasons = scorer.score(match_item, intent)
    _, mismatch_reasons = scorer.score(mismatch_item, intent)
    assert "match_time_slot" in match_reasons
    assert "slot_mismatch" in mismatch_reasons


def test_spiritual_interest_match() -> None:
    intent = _intent(interests=["spiritual"])
    item = {
        "title": "Chùa Linh Ứng",
        "text": "den chua tam linh",
        "doc_type": "place",
        "metadata": {},
    }
    _, reasons = TravelRuleScorer().score(item, intent)
    assert "match_spiritual" in reasons


def test_quality_and_recommended_use() -> None:
    intent = _intent()
    item = {
        "doc_type": "place",
        "metadata": {"quality_score": 8, "recommended_use_norm": "main"},
    }
    score, reasons = TravelRuleScorer().score(item, intent)
    assert "quality_score" in reasons
    assert "recommended_main" in reasons
    assert score > 0


def test_itinerary_must_not_schedule_penalty() -> None:
    intent = _intent(intent="itinerary", preferred_doc_types=["itinerary"])
    item = {"doc_type": "place", "metadata": {"must_not_schedule_as_main": True}}
    score, reasons = TravelRuleScorer().score(item, intent)
    assert "must_not_schedule_as_main_penalty" in reasons
    assert score <= -20


def test_constraint_doc_bonuses_by_intent() -> None:
    scorer = TravelRuleScorer()
    itinerary_intent = _intent(intent="itinerary", preferred_doc_types=["itinerary", "constraint"])
    search_intent = _intent()
    itinerary_item = {"doc_type": "constraint", "metadata": {}}
    search_item = {"doc_type": "constraint", "metadata": {}}
    _, itinerary_reasons = scorer.score(itinerary_item, itinerary_intent)
    _, search_reasons = scorer.score(search_item, search_intent)
    assert "constraint_doc" in itinerary_reasons
    assert "constraint_doc" in search_reasons


def test_low_budget_match_and_too_high() -> None:
    intent = _intent(budget_level="low")
    match_item = {"doc_type": "place", "metadata": {"budget_level_norm": "low_medium"}}
    high_item = {"doc_type": "place", "metadata": {"budget_level_norm": "high"}}
    scorer = TravelRuleScorer()
    _, match_reasons = scorer.score(match_item, intent)
    _, high_reasons = scorer.score(high_item, intent)
    assert "match_low_budget" in match_reasons
    assert "budget_too_high" in high_reasons


def test_not_kid_friendly_penalty() -> None:
    intent = _intent(has_children=True)
    item = {"doc_type": "place", "metadata": {"kid_friendly_norm": False}}
    _, reasons = TravelRuleScorer().score(item, intent)
    assert "not_kid_friendly" in reasons


def test_elderly_friendly_and_moderate_walking() -> None:
    intent = _intent(has_elderly=True)
    item = {
        "doc_type": "place",
        "metadata": {"elderly_friendly_norm": True, "walking_level_norm": "moderate"},
    }
    score, reasons = TravelRuleScorer().score(item, intent)
    assert "elderly_friendly" in reasons
    assert "moderate_walking" in reasons
    assert score > 0


def test_elderly_easy_walking_boost() -> None:
    intent = _intent(has_elderly=True)
    item = {"doc_type": "place", "metadata": {"walking_level_norm": "easy"}}
    _, reasons = TravelRuleScorer().score(item, intent)
    assert "easy_walking" in reasons


def test_full_day_flexible_slot() -> None:
    intent = _intent(time_slot="evening")
    item = {"doc_type": "place", "metadata": {"slot_norm": "full_day"}}
    _, reasons = TravelRuleScorer().score(item, intent)
    assert "flexible_slot" in reasons


def test_walking_preference_easy_and_avoid_hard() -> None:
    intent = _intent(walking_preference="easy")
    easy_item = {"doc_type": "place", "metadata": {"walking_level_norm": "easy"}}
    hard_item = {"doc_type": "place", "metadata": {"walking_level_norm": "hard"}}
    scorer = TravelRuleScorer()
    _, easy_reasons = scorer.score(easy_item, intent)
    _, hard_reasons = scorer.score(hard_item, intent)
    assert "match_easy_walking" in easy_reasons
    assert "avoid_hard_walking" in hard_reasons


def test_flexible_time_slot() -> None:
    intent = _intent(time_slot="afternoon")
    item = {"doc_type": "place", "metadata": {"slot_norm": "any"}}
    _, reasons = TravelRuleScorer().score(item, intent)
    assert "flexible_slot" in reasons


def test_recommended_supporting_and_optional() -> None:
    scorer = TravelRuleScorer()
    intent = _intent()
    _, supporting = scorer.score(
        {"doc_type": "place", "metadata": {"recommended_use_norm": "supporting"}},
        intent,
    )
    _, optional = scorer.score(
        {"doc_type": "place", "metadata": {"recommended_use_norm": "optional"}},
        intent,
    )
    assert "recommended_supporting" in supporting
    assert "optional_penalty" in optional


def test_requires_realtime_check_penalty() -> None:
    intent = _intent()
    item = {"doc_type": "place", "metadata": {"requires_realtime_check": True}}
    _, reasons = TravelRuleScorer().score(item, intent)
    assert "requires_realtime_check" in reasons


def test_invalid_quality_score_is_ignored() -> None:
    intent = _intent()
    item = {"doc_type": "place", "metadata": {"quality_score": "not-a-number"}}
    score, reasons = TravelRuleScorer().score(item, intent)
    assert "quality_score" not in reasons
    assert score == 4  # place_doc only


def test_culture_food_checkin_nature_interests() -> None:
    scorer = TravelRuleScorer()
    cases = [
        ("culture", "Bảo tàng Lịch sử", "lich su van hoa", "match_culture"),
        ("food", "Quán ăn địa phương", "am thuc mon ngon", "match_food"),
        ("checkin", "View đẹp", "checkin chup anh canh dep", "match_checkin"),
        ("nature", "Vườn quốc gia", "thien nhien sinh thai park", "match_nature"),
    ]
    for interest, title, text, expected_reason in cases:
        intent = _intent(interests=[interest])
        item = {"title": title, "text": text, "doc_type": "place", "metadata": {}}
        _, reasons = scorer.score(item, intent)
        assert expected_reason in reasons, interest


def test_beach_strong_title_and_weak_context() -> None:
    scorer = TravelRuleScorer()
    strong_intent = _intent(interests=["beach"])
    strong_item = {
        "title": "Vịnh Cam Ranh",
        "text": "canh bien",
        "doc_type": "place",
        "metadata": {},
    }
    _, strong_reasons = scorer.score(strong_item, strong_intent)

    weak_intent = _intent(interests=["beach"])
    weak_item = {
        "title": "Resort ABC",
        "text": "nghi duong hai san beach coast",
        "doc_type": "place",
        "metadata": {},
    }
    _, weak_reasons = scorer.score(weak_item, weak_intent)

    assert "strong_beach_title_match" in strong_reasons
    assert "weak_beach_context_match" in weak_reasons
