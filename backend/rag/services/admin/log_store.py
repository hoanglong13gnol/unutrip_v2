"""AI request log JSONL read + aggregate metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.config import settings


def log_file_path() -> Path:
    return settings.reports_dir / "ai_request_logs.jsonl"


def load_ai_log_records() -> list[dict[str, Any]]:
    log_file = log_file_path()
    if not log_file.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in log_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            continue
    return records


def empty_ai_metrics() -> dict[str, Any]:
    return {
        "total_requests": 0,
        "fallback_count": 0,
        "fallback_rate": 0,
        "timeout_count": 0,
        "quota_exceeded_count": 0,
        "cache_hit_count": 0,
        "cache_hit_rate": 0,
        "avg_total_latency": 0,
        "avg_gemini_latency": 0,
        "model_usage": {},
        "top_queries": [],
        "top_places": [],
    }


def compute_ai_metrics(
    records: list[dict[str, Any]],
    *,
    include_rankings: bool = True,
) -> dict[str, Any]:
    if not records:
        return empty_ai_metrics()

    total = len(records)
    fallback_count = 0
    timeout_count = 0
    quota_exceeded_count = 0
    cache_hit_count = 0
    total_latency_sum = 0.0
    total_latency_count = 0
    gemini_latency_sum = 0.0
    gemini_latency_count = 0
    model_usage: dict[str, int] = {}
    query_count: dict[str, int] = {}
    place_count: dict[str, int] = {}

    for record in records:
        if record.get("fallback_used") is True:
            fallback_count += 1
        if record.get("gemini_timeout") is True:
            timeout_count += 1
        if record.get("generation_error_type") == "quota_exceeded":
            quota_exceeded_count += 1
        if record.get("cache_hit") is True:
            cache_hit_count += 1

        model = record.get("model_used") or "unknown"
        model_usage[model] = model_usage.get(model, 0) + 1

        if include_rankings:
            query = record.get("query")
            if query:
                query_count[query] = query_count.get(query, 0) + 1
            for place_name in record.get("top_place_names", [])[:10]:
                if place_name:
                    place_count[place_name] = place_count.get(place_name, 0) + 1

        latency = record.get("latency_ms", {})
        total_latency = latency.get("total")
        if isinstance(total_latency, (int, float)):
            total_latency_sum += float(total_latency)
            total_latency_count += 1
        gemini_latency = latency.get("gemini")
        if isinstance(gemini_latency, (int, float)):
            gemini_latency_sum += float(gemini_latency)
            gemini_latency_count += 1

    payload: dict[str, Any] = {
        "total_requests": total,
        "fallback_count": fallback_count,
        "fallback_rate": round(fallback_count / total, 4),
        "timeout_count": timeout_count,
        "quota_exceeded_count": quota_exceeded_count,
        "cache_hit_count": cache_hit_count,
        "cache_hit_rate": round(cache_hit_count / total, 4),
        "avg_total_latency": round(total_latency_sum / total_latency_count, 2)
        if total_latency_count
        else 0,
        "avg_gemini_latency": round(gemini_latency_sum / gemini_latency_count, 2)
        if gemini_latency_count
        else 0,
        "model_usage": model_usage,
    }

    if include_rankings:
        payload["top_queries"] = [
            {"query": query, "count": count}
            for query, count in sorted(query_count.items(), key=lambda item: item[1], reverse=True)[:10]
        ]
        payload["top_places"] = [
            {"place": place, "count": count}
            for place, count in sorted(place_count.items(), key=lambda item: item[1], reverse=True)[:10]
        ]
    else:
        payload["top_queries"] = []
        payload["top_places"] = []

    return payload


def tail_logs(limit: int = 20) -> dict[str, Any]:
    records = load_ai_log_records()
    limit = max(1, min(limit, 100))
    selected = records[-limit:]
    selected.reverse()
    return {"total": len(records), "limit": limit, "logs": selected}
