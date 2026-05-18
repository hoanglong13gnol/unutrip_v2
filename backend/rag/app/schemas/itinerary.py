"""Itinerary preview / options request and option models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ItineraryPreviewRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    startDate: str
    endDate: str
    budget: float | None = None
    preferences: list[str] = Field(default_factory=list)
    province: str | None = None
    contextQuery: str | None = Field(
        default=None,
        validation_alias="contextQuery",
        description="Tùy chọn: câu / ngữ cảnh giống chatbot để retrieve khớp luồng RAG chat.",
    )


class AIItineraryOptionDay(BaseModel):
    dayNumber: int
    items: list[dict[str, Any]] = Field(default_factory=list)


class AIItineraryOption(BaseModel):
    optionId: str
    title: str
    summary: str
    theme: str
    estimatedBudget: float | None = None
    totalDays: int
    highlights: list[str] = Field(default_factory=list)
    days: list[AIItineraryOptionDay] = Field(default_factory=list)
