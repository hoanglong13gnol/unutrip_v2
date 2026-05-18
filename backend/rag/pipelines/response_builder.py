from __future__ import annotations

from typing import Any


def extract_places(retrieved: dict[str, Any]) -> list[dict[str, Any]]:
    places = []

    for item in retrieved.get("results", []):
        meta = item.get("metadata") or {}
        places.append({
            "place_id": item.get("place_id"),
            "name": item.get("title"),
            "province": meta.get("province"),
            "city": meta.get("city"),
            "area": meta.get("area"),
            "category_main": meta.get("category_main"),
            "category_sub": meta.get("category_sub"),
            "budget_level": meta.get("budget_level_norm"),
            "walking_level": meta.get("walking_level_norm"),
            "kid_friendly": meta.get("kid_friendly_norm"),
            "elderly_friendly": meta.get("elderly_friendly_norm"),
            "slot": meta.get("slot_norm"),
            "quality_score": meta.get("quality_score"),
            "recommended_use": meta.get("recommended_use_norm"),
            "requires_realtime_check": meta.get("requires_realtime_check"),
            "score": item.get("final_score"),
            "reasons": item.get("reasons", []),
        })

    return places


def extract_warnings(retrieved: dict[str, Any]) -> list[str]:
    warnings = []
    seen = set()

    for item in retrieved.get("results", []):
        meta = item.get("metadata") or {}
        name = item.get("title")

        if meta.get("requires_realtime_check") is True and name not in seen:
            warnings.append(
                f"Nên kiểm tra thông tin thực tế trước khi đi {name}, "
                "đặc biệt là giờ mở cửa, giá vé hoặc điều kiện vận hành."
            )
            seen.add(name)

    return warnings
