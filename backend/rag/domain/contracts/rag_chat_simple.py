"""
`/rag/chat/simple` response contract — mirrors backend/nodejs/src/schemas/ragContract.js.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class RagChatSimplePlace(BaseModel):
    """One place row in rag_chat_simple (extra keys allowed like Node .passthrough())."""

    model_config = ConfigDict(extra="allow")

    place_id: str | int | None = None
    name: str | None = None
    province: str | None = None
    city: str | None = None
    area: str | None = None
    category_main: str | None = None
    category_sub: str | None = None
    budget_level: str | None = None
    walking_level: str | None = None
    kid_friendly: bool | None = None
    elderly_friendly: bool | None = None
    slot: str | None = None
    quality_score: float | str | None = None
    recommended_use: str | None = None
    requires_realtime_check: bool | None = None
    score: float | str | None = None


class RagChatSimpleResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    answer: str | None = None
    places: list[RagChatSimplePlace] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    latency_ms: dict[str, float | str | None] = Field(default_factory=dict)
    model_used: str = "unknown"
    fallback_used: bool = False
    rag_mode: str = "balanced"
    runtime_mode: str | None = None


def validate_rag_chat_simple(payload: dict[str, Any]) -> tuple[RagChatSimpleResponse | None, list[str]]:
    try:
        return RagChatSimpleResponse.model_validate(payload), []
    except ValidationError as exc:
        issues = [f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors()]
        return None, issues
