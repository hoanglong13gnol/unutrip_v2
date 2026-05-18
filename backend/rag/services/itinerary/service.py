from __future__ import annotations

from typing import Any

from app.schemas.itinerary import ItineraryPreviewRequest
from pipelines.rag_pipeline import RagPipeline
from services.itinerary.builder import build_itinerary_option
from services.itinerary.catalog import (
    estimate_trip_days,
    get_first_image,
    get_numeric_destination_id,
    get_raw_place_id,
    load_places,
    retrieval_seed_rank,
)
from services.itinerary.category import app_category_from_rag
from services.itinerary.scoring import build_reason, build_sync_query, score_place


class ItineraryService:
    def preview(self, request: ItineraryPreviewRequest) -> dict[str, Any]:
        places = load_places()
        if not places:
            return {
                "success": False,
                "message": "Không tìm thấy dữ liệu địa điểm cho RAG preview.",
                "data": {
                    "title": request.title or "Lịch trình AI gợi ý",
                    "summary": "Không có dữ liệu địa điểm.",
                    "suggestedDestinations": [],
                },
            }

        scored: list[tuple[int, dict[str, Any]]] = []
        for place in places:
            raw_place_id = get_raw_place_id(place)
            if not raw_place_id:
                continue
            score = score_place(place, request)
            if score > 0:
                scored.append((score, place))

        if not scored:
            scored = [(0, place) for place in places if get_raw_place_id(place)]

        scored.sort(key=lambda item: item[0], reverse=True)
        trip_days = estimate_trip_days(request.startDate, request.endDate)
        suggestions: list[dict[str, Any]] = []
        used_raw_place_ids: set[str] = set()

        for index, (_, place) in enumerate(scored):
            if len(suggestions) >= 20:
                break
            raw_place_id = get_raw_place_id(place)
            if not raw_place_id or raw_place_id in used_raw_place_ids:
                continue
            used_raw_place_ids.add(raw_place_id)
            suggestions.append(
                {
                    "destinationId": get_numeric_destination_id(place),
                    "rawPlaceId": raw_place_id,
                    "name": place.get("name"),
                    "province": place.get("province"),
                    "city": place.get("city"),
                    "area": place.get("area"),
                    "category": app_category_from_rag(place),
                    "imageUrl": get_first_image(place),
                    "reason": build_reason(place, request),
                    "estimatedVisitDurationMinutes": int(place.get("duration_minutes") or 120),
                    "recommendedDay": (index % trip_days) + 1,
                    "qualityScore": place.get("quality_score"),
                }
            )

        return {
            "success": True,
            "data": {
                "title": request.title or "Lịch trình AI gợi ý",
                "summary": (
                    "AI/RAG đã gợi ý danh sách địa điểm. "
                    "Bạn có thể chọn/bỏ chọn trước khi tạo lịch trình."
                ),
                "suggestedDestinations": suggestions,
            },
        }

    def options(self, request: ItineraryPreviewRequest, pipeline: RagPipeline) -> dict[str, Any]:
        places = load_places()
        if not places:
            return {
                "success": False,
                "message": "Không tìm thấy dữ liệu địa điểm cho RAG itinerary options.",
                "data": {
                    "title": request.title or "Lịch trình AI gợi ý",
                    "summary": "Không có dữ liệu địa điểm.",
                    "options": [],
                },
            }

        sync_q = build_sync_query(request)
        retrieval_rank = retrieval_seed_rank(pipeline, places, sync_q)
        province_label = request.province or "điểm đến"

        option_specs = [
            {
                "option_id": "balanced",
                "title": f"{province_label} cân bằng",
                "theme": "balanced",
                "preferences": list(dict.fromkeys(request.preferences + ["checkin", "culture", "food"])),
                "keywords": ["checkin", "van hoa", "am thuc", "trai nghiem"],
                "max_items_per_day": 3,
            },
            {
                "option_id": "checkin",
                "title": f"{province_label} check-in nổi bật",
                "theme": "checkin",
                "preferences": list(dict.fromkeys(["checkin", "city", "nature"] + request.preferences)),
                "keywords": ["checkin", "canh dep", "noi bat", "song ao", "quang truong"],
                "max_items_per_day": 3,
            },
            {
                "option_id": "food_culture",
                "title": f"{province_label} ẩm thực và văn hóa",
                "theme": "food_culture",
                "preferences": list(dict.fromkeys(["food", "culture", "heritage"] + request.preferences)),
                "keywords": ["am thuc", "dac san", "van hoa", "lang nghe", "cho", "pho"],
                "max_items_per_day": 3,
            },
            {
                "option_id": "relax_nature",
                "title": f"{province_label} nhẹ nhàng thiên nhiên",
                "theme": "relax_nature",
                "preferences": list(dict.fromkeys(["nature", "mountain", "checkin"] + request.preferences)),
                "keywords": ["thien nhien", "ho", "nui", "vuon", "suoi", "thu gian"],
                "max_items_per_day": 2,
            },
        ]

        options = [
            build_itinerary_option(
                request=request,
                places=places,
                option_id=spec["option_id"],
                title=spec["title"],
                theme=spec["theme"],
                option_preferences=spec["preferences"],
                option_keywords=spec["keywords"],
                max_items_per_day=spec["max_items_per_day"],
                retrieval_rank=retrieval_rank,
            )
            for spec in option_specs
        ]

        return {
            "success": True,
            "data": {
                "title": request.title or "Lịch trình AI gợi ý",
                "summary": (
                    "Các phương án ưu tiên địa điểm cùng cụm retrieve RAG với form của bạn; "
                    "chia ngày giữ đúng thứ tự gợi ý (giống bước tạo lịch từ chatbot)."
                ),
                "options": [option.model_dump() for option in options],
            },
        }
