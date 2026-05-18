from typing import Any, Literal

from pydantic import BaseModel, Field


class UserIntent(BaseModel):
    intent: Literal["chat", "search_place", "itinerary", "compare", "unknown"] = "chat"
    query: str

    province: str | None = None
    city: str | None = None
    area: str | None = None

    days: int | None = None
    time_slot: Literal["morning", "afternoon", "evening", "night", "full_day"] | None = None

    budget_level: Literal["free", "low", "medium", "high", "luxury"] | None = None

    has_children: bool = False
    has_elderly: bool = False

    walking_preference: Literal["easy", "moderate", "hard"] | None = None
    activity_preference: Literal["light", "moderate", "active"] | None = None

    interests: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)


class RetrievedPlace(BaseModel):
    place_id: str
    name: str
    province: str | None = None
    city: str | None = None
    area: str | None = None

    category_main: str | None = None
    category_sub: str | None = None
    short_description: str | None = None

    quality_score: float | None = None
    final_score: float = 0.0
    reason: str = ""

    requires_realtime_check: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagRequest(BaseModel):
    message: str
    mode: Literal["fast", "balanced", "max_power"] = "balanced"

    province: str | None = None
    city: str | None = None
    days: int | None = None
    budget_level: str | None = None

    has_children: bool = False
    has_elderly: bool = False

    interests: list[str] = Field(default_factory=list)


class RagResponse(BaseModel):
    answer: str
    rag_mode: str
    model_used: str = "none"
    fallback_used: bool = False

    places: list[RetrievedPlace] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    latency_ms: dict[str, float] = Field(default_factory=dict)
    debug: dict[str, Any] = Field(default_factory=dict)