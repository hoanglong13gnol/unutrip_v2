from __future__ import annotations

from typing import Any

from retrieval.text_utils import normalize_text


def name_dedup_key(title: str | None) -> str:
    name = normalize_text(str(title or ""))

    remove_phrases = [
        "khu du lich",
        "diem du lich",
        "dia diem",
        "bai bien",
        "bai tam",
        "khu bao ton",
        "quan the di tich",
        "di tich",
        "chua",
        "den",
        "dinh",
        "nha tho",
    ]

    for phrase in remove_phrases:
        name = name.replace(phrase, " ")

    tokens = [
        token
        for token in name.split()
        if token not in {
            "tai",
            "o",
            "tp",
            "thanh",
            "pho",
            "nha",
            "trang",
            "ha",
            "noi",
            "hue",
        }
    ]

    if not tokens:
        return normalize_text(str(title or ""))

    return " ".join(tokens)


def is_near_duplicate_name(a: str | None, b: str | None) -> bool:
    key_a = name_dedup_key(a)
    key_b = name_dedup_key(b)

    if not key_a or not key_b:
        return False

    if key_a == key_b:
        return True

    tokens_a = set(key_a.split())
    tokens_b = set(key_b.split())

    if not tokens_a or not tokens_b:
        return False

    overlap = len(tokens_a & tokens_b)
    smaller = min(len(tokens_a), len(tokens_b))

    return overlap / smaller >= 0.8


def deduplicate_scored_results(
    scored: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen_place_ids: set[str] = set()
    seen_name_keys: set[str] = set()

    for item in scored:
        place_id = item.get("place_id")
        if not place_id or place_id in seen_place_ids:
            continue

        name_key = name_dedup_key(item.get("title"))

        if name_key and name_key in seen_name_keys:
            continue

        seen_place_ids.add(place_id)

        if name_key:
            seen_name_keys.add(name_key)

        deduped.append(item)

        if len(deduped) >= top_k:
            break

    return deduped
