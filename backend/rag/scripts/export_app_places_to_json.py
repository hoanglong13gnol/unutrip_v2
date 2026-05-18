"""
Export active `app_places` rows to `places_app.json` for PlaceStore / itinerary preview.

Requires: pip install pymysql
Env: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME (same as Node .env)
"""

from __future__ import annotations

import json
import os

from core.config import settings
from retrieval.text_utils import normalize_text


def norm_key(value) -> str | None:
    text = normalize_text(str(value or "")).strip()
    if not text:
        return None
    return text.replace(" ", "_")


def row_to_place(row: dict) -> dict:
    place_key = str(row.get("place_key") or "").strip()
    name = (row.get("name") or "").strip()
    desc = (row.get("description") or row.get("short_description") or "").strip()
    search_bits = [name, row.get("city"), row.get("province"), row.get("area"), desc]
    search_text = " ".join(str(p).strip() for p in search_bits if p)

    category = (row.get("category") or "other").strip()

    return {
        "place_id": place_key,
        "id": row.get("id"),
        "app_place_id": row.get("id"),
        "name": name,
        "description": desc,
        "address": row.get("address"),
        "province": row.get("province"),
        "province_norm": norm_key(row.get("province")),
        "city": row.get("city"),
        "city_norm": norm_key(row.get("city")),
        "area": row.get("area"),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "category_main": category,
        "category_sub": None,
        "category_main_norm": category,
        "budget_level_norm": row.get("budget_level"),
        "walking_level_norm": row.get("walking_level"),
        "kid_friendly_norm": bool(row.get("kid_friendly")),
        "elderly_friendly_norm": bool(row.get("elderly_friendly")),
        "recommended_use_norm": row.get("recommended_use"),
        "rating": float(row["rating"]) if row.get("rating") is not None else None,
        "review_count": row.get("review_count"),
        "primary_image_url": row.get("primary_image_url"),
        "search_text": search_text,
        "is_active": bool(row.get("is_active", 1)),
    }


def main() -> None:
    try:
        import pymysql
    except ImportError as exc:
        raise SystemExit("Install pymysql: pip install pymysql") from exc

    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "unudata")

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

    sql = """
    SELECT
      id, place_key, name, description, short_description, address,
      city, province, area, latitude, longitude, category,
      budget_level, walking_level, kid_friendly, elderly_friendly,
      recommended_use, rating, review_count, primary_image_url, is_active
    FROM app_places
    WHERE is_active = 1
    ORDER BY id
    """

    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    conn.close()

    places = [row_to_place(row) for row in rows]
    out_path = settings.places_app_file
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {"output_file": str(out_path), "place_count": len(places)}
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    (settings.reports_dir / "export_app_places_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exported {len(places)} places to {out_path}")


if __name__ == "__main__":
    main()
