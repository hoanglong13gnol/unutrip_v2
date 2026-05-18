"""RAG pipeline: province matching must not treat missing metadata as a match."""

from pipelines.policies.location_filter import place_matches_province


def test_empty_place_metadata_does_not_match_any_province() -> None:
    place = {"title": "Chợ đêm X", "metadata": {}}
    assert place_matches_province(place, "Hà Giang") is False


def test_place_with_province_matches() -> None:
    place = {"title": "Đèo Mã Pí Lèng", "metadata": {"province": "Hà Giang"}}
    assert place_matches_province(place, "Hà Giang") is True
