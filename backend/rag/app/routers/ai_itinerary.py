"""AI itinerary preview and multi-option routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.deps import PipelineDep
from app.schemas.itinerary import ItineraryPreviewRequest
from services.itinerary import ItineraryService

router = APIRouter(prefix="/ai", tags=["AI Itinerary"])
_itinerary = ItineraryService()


@router.post("/itinerary-preview")
def itinerary_preview(request: ItineraryPreviewRequest) -> dict[str, Any]:
    return _itinerary.preview(request)


@router.post("/itinerary-options")
def itinerary_options(request: ItineraryPreviewRequest, pipeline: PipelineDep) -> dict[str, Any]:
    return _itinerary.options(request, pipeline)
