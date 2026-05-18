from providers.template_provider import TemplateAnswerProvider

EMPTY = {"results": [], "intent": {}}
WITH_RESULTS = {
    "intent": {"intent": "search_place"},
    "results": [{"title": "A"}, {"title": "B"}],
}


def test_template_answer_empty() -> None:
    assert "chưa tìm thấy" in TemplateAnswerProvider().build_template_answer(EMPTY).lower()


def test_mock_answer_lists_places() -> None:
    text = TemplateAnswerProvider().build_mock_answer(WITH_RESULTS)
    assert "A" in text and "B" in text


def test_mock_itinerary_intent() -> None:
    payload = {**WITH_RESULTS, "intent": {"intent": "itinerary"}}
    text = TemplateAnswerProvider().build_mock_answer(payload)
    assert "lịch trình" in text.lower()
