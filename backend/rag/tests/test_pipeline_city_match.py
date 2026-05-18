"""RAG pipeline: targetCity filter must not treat missing city metadata as a match."""

from pipelines.policies.location_filter import (
    filter_retrieved_by_city,
    place_matches_city,
)


def test_empty_place_metadata_does_not_match_any_city() -> None:
    place = {"title": "Chợ đêm X", "metadata": {}}
    assert place_matches_city(place, "Hà Giang") is False


def test_place_with_city_matches() -> None:
    place = {"title": "Phố cổ", "metadata": {"city": "Hà Giang"}}
    assert place_matches_city(place, "Hà Giang") is True


def test_filter_retrieved_by_city_keeps_matching_results() -> None:
    retrieved = {
        "results": [
            {"title": "A", "metadata": {"city": "Hà Giang"}},
            {"title": "B", "metadata": {"city": "Lào Cai"}},
        ],
        "debug": {},
    }
    filtered = filter_retrieved_by_city(retrieved, "Hà Giang", top_k=6)
    assert len(filtered["results"]) == 1
    assert filtered["results"][0]["title"] == "A"
    assert filtered["debug"]["city_filter_used"] is True
