"""Intent parser: province aliases and time_slot vs trip duration."""

from retrieval.intent_parser import IntentParser


def test_ha_giang_province_and_itinerary() -> None:
    p = IntentParser()
    out = p.parse("lên lịch trình đi hà giang 2 ngày 1 đêm")
    assert out.intent == "itinerary"
    assert out.province_norm == "ha_giang"
    assert out.days == 2
    assert out.time_slot is None


def test_cao_bang_province_and_itinerary() -> None:
    p = IntentParser()
    out = p.parse("lên lịch trình đi cao bằng 2 ngày 1 đêm")
    assert out.intent == "itinerary"
    assert out.province_norm == "cao_bang"
    assert out.days == 2
    assert out.time_slot is None


def test_ngay_dem_does_not_set_evening_slot() -> None:
    p = IntentParser()
    out = p.parse("goi y di da nang 3 ngay 2 dem")
    assert out.intent == "itinerary"
    assert out.province_norm == "da_nang"
    assert out.time_slot is None


def test_buoi_toi_sets_evening() -> None:
    p = IntentParser()
    out = p.parse("di ha noi buoi toi choi o dau")
    assert out.time_slot == "evening"


def test_toi_muon_is_not_evening_slot() -> None:
    p = IntentParser()
    out = p.parse("toi muon di ha noi")
    assert out.time_slot != "evening" or out.time_slot is None


def test_food_query_hanoi() -> None:
    p = IntentParser()
    out = p.parse("Ăn gì khi đến Hà Nội?")
    assert out.province_norm == "ha_noi"
    assert "food" in out.interests


def test_thai_nguyen_province_and_itinerary() -> None:
    p = IntentParser()
    out = p.parse("lich trinh di thai nguyen 2 ngay 1 dem")
    assert out.intent == "itinerary"
    assert out.province_norm == "thai_nguyen"
    assert out.days == 2


def test_an_giang_not_food_interest() -> None:
    p = IntentParser()
    out = p.parse("goi y di an giang")
    assert out.province_norm == "an_giang"
    assert "food" not in out.interests
