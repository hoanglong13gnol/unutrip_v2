"""Province/city filtering and place-store fallback for retrieved results."""

from __future__ import annotations

from typing import Any

from core.text_normalization import normalize_text
from retrieval.place_store import PlaceStore


def place_matches_province(place: dict[str, Any], target_province) -> bool:
    target = normalize_text(target_province)
    if not target:
        return True

    meta = place.get("metadata") or {}
    province = normalize_text(place.get("province") or meta.get("province"))
    city = normalize_text(place.get("city") or meta.get("city"))
    area = normalize_text(place.get("area") or meta.get("area"))

    # Python: "" in "ha giang" is True — metadata thiếu tỉnh không được coi là khớp.
    if not province and not city and not area:
        return False

    return (
        province == target
        or (bool(province) and target in province)
        or (bool(province) and province in target)
        or city == target
        or area == target
    )


def place_matches_city(place: dict[str, Any], target_city) -> bool:
    target = normalize_text(target_city)
    if not target:
        return True

    meta = place.get("metadata") or {}
    city = normalize_text(place.get("city") or meta.get("city"))
    area = normalize_text(place.get("area") or meta.get("area"))

    if not city and not area:
        return False

    return (
        city == target
        or (bool(city) and target in city)
        or (bool(city) and city in target)
        or area == target
        or (bool(area) and target in area)
        or (bool(area) and area in target)
    )


def _merge_debug(retrieved: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    new_retrieved = dict(retrieved)
    debug = dict(new_retrieved.get("debug") or {})
    debug.update(updates)
    new_retrieved["debug"] = debug
    return new_retrieved


def filter_retrieved_by_province(
    retrieved: dict[str, Any],
    target_province,
    top_k: int,
) -> dict[str, Any]:
    if not target_province:
        return retrieved

    results = retrieved.get("results", []) or []
    filtered = [item for item in results if place_matches_province(item, target_province)]

    if filtered:
        new_retrieved = dict(retrieved)
        new_retrieved["results"] = filtered[:top_k]
        return _merge_debug(
            new_retrieved,
            {
                "province_filter": target_province,
                "province_filter_used": True,
                "province_filter_source": "retrieved",
                "province_filter_count": len(filtered),
            },
        )

    new_retrieved = dict(retrieved)
    new_retrieved["results"] = []
    return _merge_debug(
        new_retrieved,
        {
            "province_filter": target_province,
            "province_filter_used": True,
            "province_filter_source": "retrieved_empty",
            "province_filter_count": 0,
        },
    )


def filter_retrieved_by_city(
    retrieved: dict[str, Any],
    target_city,
    top_k: int,
) -> dict[str, Any]:
    if not target_city:
        return retrieved

    results = retrieved.get("results", []) or []
    filtered = [item for item in results if place_matches_city(item, target_city)]

    new_retrieved = dict(retrieved)
    new_retrieved["results"] = filtered[:top_k]
    return _merge_debug(
        new_retrieved,
        {
            "city_filter": target_city,
            "city_filter_used": True,
            "city_filter_count": len(filtered),
        },
    )


class LocationFilter:
    def __init__(self, place_store: PlaceStore) -> None:
        self.place_store = place_store

    def apply(
        self,
        retrieved: dict[str, Any],
        *,
        query: str,
        target_province,
        target_city,
        top_k: int,
    ) -> dict[str, Any]:
        if target_province:
            retrieved = filter_retrieved_by_province(
                retrieved=retrieved,
                target_province=target_province,
                top_k=top_k,
            )

            filtered_results = retrieved.get("results", []) or []
            has_target_result = any(
                place_matches_province(item, target_province)
                for item in filtered_results
            )

            if not has_target_result:
                retrieved = self._province_fallback_retrieved(
                    query=query,
                    retrieved=retrieved,
                    target_province=target_province,
                    top_k=top_k,
                )

        if target_city:
            retrieved = filter_retrieved_by_city(
                retrieved=retrieved,
                target_city=target_city,
                top_k=top_k,
            )

        return retrieved

    def _province_fallback_retrieved(
        self,
        query: str,
        retrieved: dict[str, Any],
        target_province,
        top_k: int,
    ) -> dict[str, Any]:
        del query  # reserved for future query-aware fallback
        if not target_province:
            return retrieved

        try:
            places = self.place_store.search(
                q=None,
                province=target_province,
                active_only=True,
                limit=top_k,
            )
        except TypeError:
            places = self.place_store.search(
                province=target_province,
                limit=top_k,
            )

        if not places:
            new_retrieved = dict(retrieved)
            new_retrieved["results"] = []
            return _merge_debug(
                new_retrieved,
                {
                    "province_filter": target_province,
                    "province_filter_used": True,
                    "province_filter_source": "place_store_fallback_empty",
                    "province_fallback_count": 0,
                },
            )

        fallback_results = []
        for place in places:
            metadata = dict(place)
            place_id = (
                place.get("place_id")
                or place.get("raw_place_id")
                or place.get("id")
            )
            name = place.get("name") or place.get("title") or "Địa điểm"
            fallback_results.append({
                "place_id": place_id,
                "title": name,
                "metadata": metadata,
                "score": place.get("search_score", 1.0),
                "final_score": place.get("search_score", 1.0),
                "reasons": ["province_fallback"],
            })

        new_retrieved = dict(retrieved)
        new_retrieved["results"] = fallback_results[:top_k]
        return _merge_debug(
            new_retrieved,
            {
                "province_filter": target_province,
                "province_filter_used": True,
                "province_filter_source": "place_store_fallback",
                "province_fallback_count": len(fallback_results),
            },
        )
