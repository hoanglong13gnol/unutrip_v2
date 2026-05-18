from unittest.mock import MagicMock

from pipelines.policies.location_filter import LocationFilter


def test_province_fallback_from_place_store() -> None:
    store = MagicMock()
    store.search.return_value = [
        {
            "place_id": "HG_01",
            "name": "Đồng Văn",
            "province": "Hà Giang",
            "search_score": 2.0,
        }
    ]

    filt = LocationFilter(store)
    retrieved = {
        "results": [{"title": "Không khớp", "metadata": {"province": "Lào Cai"}}],
        "debug": {},
    }

    out = filt.apply(
        retrieved,
        query="điểm tham quan",
        target_province="Hà Giang",
        target_city=None,
        top_k=3,
    )

    assert len(out["results"]) == 1
    assert out["results"][0]["place_id"] == "HG_01"
    assert out["debug"]["province_filter_source"] == "place_store_fallback"
