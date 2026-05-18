from pipelines.response_builder import extract_places, extract_warnings

RETRIEVED = {
    "results": [
        {
            "place_id": "P1",
            "title": "Chợ đêm",
            "final_score": 9.5,
            "reasons": ["match_province"],
            "metadata": {
                "province": "Hà Giang",
                "city": "Hà Giang",
                "requires_realtime_check": True,
            },
        },
        {
            "place_id": "P2",
            "title": "Cafe view",
            "final_score": 5.0,
            "reasons": [],
            "metadata": {"requires_realtime_check": False},
        },
    ]
}


def test_extract_places_shape() -> None:
    places = extract_places(RETRIEVED)
    assert len(places) == 2
    assert places[0]["place_id"] == "P1"
    assert places[0]["name"] == "Chợ đêm"
    assert places[0]["province"] == "Hà Giang"
    assert places[0]["score"] == 9.5


def test_extract_warnings_realtime_only_once() -> None:
    warnings = extract_warnings(RETRIEVED)
    assert len(warnings) == 1
    assert "Chợ đêm" in warnings[0]
