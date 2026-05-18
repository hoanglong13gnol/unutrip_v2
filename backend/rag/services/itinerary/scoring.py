from __future__ import annotations

from typing import Any

from app.schemas.itinerary import ItineraryPreviewRequest
from core.text_normalization import normalize_text
from services.itinerary.catalog import get_tags_text
from services.itinerary.category import app_category_from_rag


def build_sync_query(request: ItineraryPreviewRequest) -> str:
    explicit = (request.contextQuery or "").strip()
    if explicit:
        return explicit
    parts: list[str] = []
    if request.province and str(request.province).strip():
        parts.append(f"Gợi ý lịch trình du lịch {request.province.strip()}")
    if request.title and str(request.title).strip():
        parts.append(str(request.title).strip())
    if request.description and str(request.description).strip():
        parts.append(str(request.description).strip())
    if request.preferences:
        parts.append("Sở thích: " + ", ".join(str(p) for p in request.preferences if p))
    q = ". ".join(parts)
    return q.strip() if q.strip() else "Gợi ý địa điểm du lịch Việt Nam"


def score_place(place: dict[str, Any], request: ItineraryPreviewRequest) -> int:
    score = 0
    app_category = app_category_from_rag(place)
    province = normalize_text(place.get("province"))
    city = normalize_text(place.get("city"))
    area = normalize_text(place.get("area"))

    searchable = " ".join(
        [
            normalize_text(place.get("name")),
            normalize_text(place.get("description")),
            normalize_text(place.get("short_description")),
            normalize_text(place.get("category_main")),
            normalize_text(place.get("category_sub")),
            normalize_text(place.get("category_main_norm")),
            normalize_text(place.get("category_sub_norm")),
            normalize_text(place.get("province")),
            normalize_text(place.get("city")),
            normalize_text(place.get("area")),
            normalize_text(get_tags_text(place)),
            normalize_text(place.get("search_text")),
            app_category,
        ]
    )

    if request.province:
        requested_province = normalize_text(request.province)
        if requested_province and (
            requested_province in province
            or requested_province in city
            or requested_province in area
            or province in requested_province
            or city in requested_province
        ):
            score += 100

    for pref in request.preferences:
        pref_norm = normalize_text(pref)
        if not pref_norm:
            continue
        if pref_norm == app_category:
            score += 60
        elif pref_norm in searchable:
            score += 30

    description = normalize_text(request.description)
    for word in description.split():
        if len(word) >= 3 and word in searchable:
            score += 4

    quality = place.get("quality_score") or place.get("rating") or place.get("score") or 0
    try:
        score += int(float(quality))
    except Exception:
        pass
    return score


def build_reason(place: dict[str, Any], request: ItineraryPreviewRequest) -> str:
    category = app_category_from_rag(place)
    province = place.get("province") or place.get("city") or ""
    prefs = ", ".join(request.preferences) if request.preferences else "nhu cầu du lịch"
    if province:
        return f"Phù hợp với {prefs}, thuộc nhóm {category}, nằm tại {province}."
    return f"Phù hợp với {prefs}, thuộc nhóm {category}."


def rank_places_for_option(
    places: list[dict[str, Any]],
    request: ItineraryPreviewRequest,
    option_preferences: list[str],
    option_keywords: list[str],
    limit: int,
    retrieval_rank: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    from services.itinerary.catalog import get_raw_place_id

    option_request = ItineraryPreviewRequest(
        title=request.title,
        description=" ".join([request.description or "", " ".join(option_keywords)]).strip(),
        startDate=request.startDate,
        endDate=request.endDate,
        budget=request.budget,
        preferences=option_preferences,
        province=request.province,
    )

    scored: list[tuple[int, dict[str, Any]]] = []
    for place in places:
        raw_place_id = get_raw_place_id(place)
        if not raw_place_id:
            continue
        if str(place.get("is_active", True)).lower() in {"false", "0", "no"}:
            continue

        score = score_place(place, option_request)
        if retrieval_rank:
            ridx = retrieval_rank.get(raw_place_id)
            if ridx is not None:
                score += 450 - min(ridx, 300)

        category = app_category_from_rag(place)
        if category in option_preferences:
            score += 35

        searchable = normalize_text(
            " ".join(
                [
                    str(place.get("name") or ""),
                    str(place.get("description") or ""),
                    str(place.get("short_description") or ""),
                    str(place.get("search_text") or ""),
                    get_tags_text(place),
                ]
            )
        )
        for keyword in option_keywords:
            if normalize_text(keyword) in searchable:
                score += 12

        try:
            score += int(float(place.get("quality_score") or 0))
        except Exception:
            pass

        if score > 0:
            scored.append((score, place))

    if not scored:
        scored = [(0, place) for place in places if get_raw_place_id(place)]

    scored.sort(key=lambda item: item[0], reverse=True)
    selected: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    for _, place in scored:
        raw_place_id = get_raw_place_id(place)
        if not raw_place_id or raw_place_id in used_ids:
            continue
        used_ids.add(raw_place_id)
        selected.append(place)
        if len(selected) >= limit:
            break
    return selected
