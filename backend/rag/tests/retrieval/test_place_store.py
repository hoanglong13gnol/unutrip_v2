"""Unit tests for PlaceStore (no MySQL)."""

from __future__ import annotations

import json

import pytest

from core.config import settings
from retrieval.place_store import PlaceStore


@pytest.fixture
def places_dir(tmp_path, monkeypatch: pytest.MonkeyPatch) -> pytest.Path:
    monkeypatch.setattr(settings, "processed_data_dir", tmp_path)
    monkeypatch.setattr(settings, "places_app_file", tmp_path / "places_app.json")
    return tmp_path


def test_place_store_loads_list_json(places_dir) -> None:
    path = places_dir / "places_app.json"
    path.write_text(
        json.dumps(
            [
                {
                    "place_id": "P1",
                    "name": "Bãi biển Test",
                    "province": "Khánh Hòa",
                    "province_norm": "khanh_hoa",
                    "category_main": "beach",
                    "search_text": "bien test",
                    "is_active": True,
                    "quality_score": 4.0,
                },
                {
                    "place_id": "P2",
                    "name": "Đền Huế",
                    "province": "Thừa Thiên Huế",
                    "province_norm": "thua_thien_hue",
                    "is_active": False,
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    store = PlaceStore()
    assert store.loaded
    assert store.get("P1")["name"] == "Bãi biển Test"
    assert store.status()["place_count"] == 2


def test_place_store_prefers_reviewed_file(places_dir) -> None:
    (places_dir / "places_app.json").write_text("[]", encoding="utf-8")
    reviewed = places_dir / "places_app_reviewed.json"
    reviewed.write_text(
        json.dumps([{"place_id": "R1", "name": "Reviewed place", "is_active": True}]),
        encoding="utf-8",
    )

    store = PlaceStore()
    assert store.status()["using_reviewed"] is True
    assert store.get("R1") is not None


def test_place_store_search_filters(places_dir) -> None:
    (places_dir / "places_app.json").write_text(
        json.dumps(
            [
                {
                    "place_id": "P1",
                    "name": "Doc Let",
                    "province_norm": "khanh_hoa",
                    "category_main_norm": "beach",
                    "search_text": "doc let bien",
                    "is_active": True,
                },
                {
                    "place_id": "P2",
                    "name": "Other",
                    "province_norm": "ha_giang",
                    "category_main_norm": "mountain",
                    "search_text": "nui",
                    "is_active": True,
                },
            ]
        ),
        encoding="utf-8",
    )
    store = PlaceStore()

    hits = store.search(q="doc let", province="khanh_hoa", limit=5)
    assert len(hits) == 1
    assert hits[0]["place_id"] == "P1"

    by_cat = store.search(category="beach", limit=10)
    assert {h["place_id"] for h in by_cat} == {"P1"}

    assert store.search(q="nui", province="ha_giang", limit=5)[0]["place_id"] == "P2"


def test_place_store_missing_file_not_loaded(places_dir) -> None:
    store = PlaceStore()
    assert store.loaded is False
    assert store.search(q="x") == []
    assert store.status()["place_count"] == 0
