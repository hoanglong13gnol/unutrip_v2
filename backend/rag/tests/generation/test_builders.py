from generation.context_builder import ContextBuilder
from generation.prompt_builder import PromptBuilder

SAMPLE_RETRIEVED = {
    "query": "đi biển Nha Trang",
    "intent": {
        "intent": "search_place",
        "province_norm": "khanh_hoa",
        "interests": ["beach"],
    },
    "results": [
        {
            "place_id": "NT_001",
            "title": "Bãi biển Trần Phú",
            "text": "Bãi biển trung tâm Nha Trang, phù hợp tắm biển buổi sáng.",
            "reasons": ["match_province", "strong_beach_title_match"],
            "metadata": {
                "province": "Khánh Hòa",
                "area": "Nha Trang",
                "category_main": "beach",
                "budget_level_norm": "low",
                "walking_level_norm": "easy",
                "requires_realtime_check": True,
            },
        }
    ],
}


def test_context_builder_empty_results() -> None:
    assert ContextBuilder().build_context({"results": []}) == ""


def test_context_builder_includes_place_fields() -> None:
    context = ContextBuilder().build_context(SAMPLE_RETRIEVED, max_places=1)
    assert "[PLACE 1]" in context
    assert "NT_001" in context
    assert "Bãi biển Trần Phú" in context
    assert "match_province" in context
    assert "[/PLACE 1]" in context


def test_context_builder_shortens_long_text() -> None:
    long_text = "word " * 200
    payload = {
        "results": [
            {
                "place_id": "X",
                "title": "Long",
                "text": long_text,
                "metadata": {},
                "reasons": [],
            }
        ]
    }
    context = ContextBuilder().build_context(payload)
    assert "..." in context


def test_prompt_builder_search_mode() -> None:
    prompt = PromptBuilder().build_prompt(SAMPLE_RETRIEVED, context="[PLACE 1]\nid: NT_001")
    assert "USER_QUERY" in prompt
    assert "đi biển Nha Trang" in prompt
    assert "Gợi ý 3-5 địa điểm" in prompt
    assert "khanh_hoa" in prompt


def test_prompt_builder_itinerary_mode() -> None:
    itinerary_payload = {
        **SAMPLE_RETRIEVED,
        "intent": {**SAMPLE_RETRIEVED["intent"], "intent": "itinerary", "days": 2},
    }
    prompt = PromptBuilder().build_prompt(itinerary_payload, context="ctx")
    assert "Sáng / Trưa / Chiều / Tối" in prompt
    assert '"days": 2' in prompt or "'days': 2" in prompt
