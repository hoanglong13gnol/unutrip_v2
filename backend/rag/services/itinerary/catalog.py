from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from core.config import settings


def parse_json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return []
    return []


def load_places() -> list[dict[str, Any]]:
    reviewed_file = settings.processed_data_dir / "places_app_reviewed.json"
    path = reviewed_file if reviewed_file.exists() else settings.places_app_file
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("data"), list):
            return data["data"]
        if isinstance(data.get("places"), list):
            return data["places"]
    return []


def get_raw_place_id(place: dict[str, Any]) -> str | None:
    raw_id = (
        place.get("place_id")
        or place.get("placeId")
        or place.get("rawPlaceId")
        or place.get("raw_place_id")
        or place.get("id")
    )
    if raw_id is None:
        return None
    return str(raw_id).strip()


def get_numeric_destination_id(place: dict[str, Any]) -> int | None:
    for key in (
        "destination_id",
        "destinationId",
        "destination_db_id",
        "app_place_id",
        "appPlaceId",
    ):
        raw_id = place.get(key)
        if raw_id is not None:
            try:
                n = int(raw_id)
                if n > 0:
                    return n
            except Exception:
                continue
    pk = place.get("id")
    if pk is not None:
        pk_s = str(pk).strip()
        if pk_s.isdigit():
            try:
                n = int(pk_s)
                if n > 0:
                    return n
            except Exception:
                pass
    return None


def get_first_image(place: dict[str, Any]) -> str | None:
    images = place.get("images") or place.get("images_json") or place.get("image_urls") or []
    parsed = parse_json_list(images)
    if parsed:
        first = parsed[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return (
                first.get("image_url")
                or first.get("imageUrl")
                or first.get("url")
                or first.get("src")
            )
    image_url = place.get("image_url") or place.get("imageUrl")
    if isinstance(image_url, str) and image_url.strip():
        return image_url.strip()
    return None


def get_tags_text(place: dict[str, Any]) -> str:
    tags = (
        place.get("tags")
        or place.get("tags_json")
        or place.get("interest_tags_json")
        or place.get("keywords")
        or []
    )
    parsed = parse_json_list(tags)
    if parsed:
        return " ".join(str(item) for item in parsed)
    if isinstance(tags, str):
        return tags
    return ""


def estimate_trip_days(start_date: str, end_date: str) -> int:
    try:
        start = datetime.fromisoformat(start_date[:10])
        end = datetime.fromisoformat(end_date[:10])
        return max(1, (end - start).days + 1)
    except Exception:
        return 1


def catalog_index_by_place_id(places: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for place in places:
        rid = get_raw_place_id(place)
        if rid:
            out[str(rid)] = place
    return out


def retrieval_seed_rank(
    pipeline: Any,
    catalog: list[dict[str, Any]],
    query: str,
    top_k: int = 40,
) -> dict[str, int]:
    try:
        retrieved = pipeline.retriever.retrieve(query, top_k=top_k)
        results = retrieved.get("results") or []
    except Exception:
        return {}
    by_id = catalog_index_by_place_id(catalog)
    rank: dict[str, int] = {}
    for i, item in enumerate(results):
        pid = str(item.get("place_id") or "").strip()
        if pid and pid in by_id and pid not in rank:
            rank[pid] = i
    return rank
