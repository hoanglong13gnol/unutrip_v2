from __future__ import annotations

from typing import Any

from app.schemas.itinerary import AIItineraryOption, AIItineraryOptionDay, ItineraryPreviewRequest
from services.itinerary.catalog import (
    estimate_trip_days,
    get_first_image,
    get_numeric_destination_id,
    get_raw_place_id,
)
from services.itinerary.category import app_category_from_rag
from services.itinerary.scoring import build_reason, rank_places_for_option


def build_suggestion_item(place: dict[str, Any], recommended_day: int) -> dict[str, Any]:
    return {
        "destinationId": get_numeric_destination_id(place),
        "rawPlaceId": get_raw_place_id(place),
        "name": place.get("name"),
        "province": place.get("province"),
        "city": place.get("city"),
        "area": place.get("area"),
        "category": app_category_from_rag(place),
        "imageUrl": get_first_image(place),
        "reason": build_reason(
            place,
            ItineraryPreviewRequest(
                title="",
                description="",
                startDate="2026-01-01",
                endDate="2026-01-01",
                budget=None,
                preferences=[],
                province=place.get("province"),
            ),
        ),
        "estimatedVisitDurationMinutes": int(place.get("duration_minutes") or 120),
        "recommendedDay": recommended_day,
        "qualityScore": place.get("quality_score"),
    }


def distribute_places_to_days(
    places: list[dict[str, Any]],
    total_days: int,
    max_items_per_day: int = 3,
) -> list[AIItineraryOptionDay]:
    d = max(1, int(total_days))
    max_total_items = d * max_items_per_day
    selected_places = places[:max_total_items]
    n = len(selected_places)

    if n == 0:
        return [AIItineraryOptionDay(dayNumber=day_number, items=[]) for day_number in range(1, d + 1)]

    if n < d:
        days_out: list[AIItineraryOptionDay] = []
        for index, place in enumerate(selected_places):
            day_num = index + 1
            days_out.append(
                AIItineraryOptionDay(
                    dayNumber=day_num,
                    items=[build_suggestion_item(place, day_num)],
                )
            )
        have = {x.dayNumber for x in days_out}
        for dn in range(1, d + 1):
            if dn not in have:
                days_out.append(AIItineraryOptionDay(dayNumber=dn, items=[]))
        days_out.sort(key=lambda x: x.dayNumber)
        return days_out

    base = n // d
    remainder = n % d
    sizes = [base + (1 if idx < remainder else 0) for idx in range(d)]
    days_out = []
    offset = 0
    for day in range(1, d + 1):
        sz = sizes[day - 1]
        if sz <= 0:
            days_out.append(AIItineraryOptionDay(dayNumber=day, items=[]))
            continue
        slice_places = selected_places[offset : offset + sz]
        days_out.append(
            AIItineraryOptionDay(
                dayNumber=day,
                items=[build_suggestion_item(p, day) for p in slice_places],
            )
        )
        offset += sz
    return days_out


def build_option_summary(theme: str, province: str | None) -> str:
    location = province or "khu vực bạn chọn"
    if theme == "balanced":
        return (
            f"Lịch trình cân bằng cho {location}, "
            "kết hợp check-in, văn hóa và trải nghiệm địa phương."
        )
    if theme == "checkin":
        return (
            f"Tập trung các điểm nổi bật, dễ chụp ảnh và phù hợp cho chuyến đi check-in tại {location}."
        )
    if theme == "food_culture":
        return f"Ưu tiên ẩm thực, văn hóa, làng nghề và trải nghiệm đời sống địa phương tại {location}."
    if theme == "relax_nature":
        return f"Lịch trình nhẹ nhàng hơn, ưu tiên thiên nhiên, cảnh quan và ít áp lực di chuyển tại {location}."
    return f"Phương án tour gợi ý cho {location}."


def build_itinerary_option(
    request: ItineraryPreviewRequest,
    places: list[dict[str, Any]],
    option_id: str,
    title: str,
    theme: str,
    option_preferences: list[str],
    option_keywords: list[str],
    max_items_per_day: int,
    retrieval_rank: dict[str, int] | None = None,
) -> AIItineraryOption:
    total_days = estimate_trip_days(request.startDate, request.endDate)
    ranked_places = rank_places_for_option(
        places=places,
        request=request,
        option_preferences=option_preferences,
        option_keywords=option_keywords,
        limit=max(12, total_days * max_items_per_day + 4),
        retrieval_rank=retrieval_rank,
    )
    days = distribute_places_to_days(
        places=ranked_places,
        total_days=total_days,
        max_items_per_day=max_items_per_day,
    )

    highlights: list[str] = []
    for day in days:
        for item in day.items:
            name = item.get("name")
            if name and name not in highlights:
                highlights.append(str(name))
            if len(highlights) >= 5:
                break
        if len(highlights) >= 5:
            break

    return AIItineraryOption(
        optionId=option_id,
        title=title,
        summary=build_option_summary(theme, request.province),
        theme=theme,
        estimatedBudget=request.budget,
        totalDays=total_days,
        highlights=highlights,
        days=days,
    )
