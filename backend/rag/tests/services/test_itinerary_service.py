"""Itinerary service unit tests (no HTTP, no BM25)."""

from __future__ import annotations

from app.schemas.itinerary import ItineraryPreviewRequest
from services.itinerary.service import ItineraryService


def test_preview_no_places(monkeypatch) -> None:
    monkeypatch.setattr("services.itinerary.service.load_places", lambda: [])
    svc = ItineraryService()
    out = svc.preview(
        ItineraryPreviewRequest(
            startDate="2026-06-01",
            endDate="2026-06-03",
            province="Khánh Hòa",
        )
    )
    assert out["success"] is False


def test_preview_with_scored_place(monkeypatch) -> None:
    places = [
        {
            "place_id": "AG_100",
            "name": "Bãi Trường",
            "province": "Khánh Hòa",
            "category_main": "beach",
            "quality_score": 5,
            "is_active": True,
        }
    ]
    monkeypatch.setattr("services.itinerary.service.load_places", lambda: places)
    svc = ItineraryService()
    out = svc.preview(
        ItineraryPreviewRequest(
            startDate="2026-06-01",
            endDate="2026-06-02",
            province="Khánh Hòa",
            preferences=["beach"],
        )
    )
    assert out["success"] is True
    dest = out["data"]["suggestedDestinations"]
    assert len(dest) == 1
    assert dest[0]["rawPlaceId"] == "AG_100"
