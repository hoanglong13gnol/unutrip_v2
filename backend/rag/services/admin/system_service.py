"""Admin system overview + self-test."""

from __future__ import annotations

from typing import Any

from core.artifacts import manifest_status_block
from core.config import settings
from pipelines.rag_pipeline import RagPipeline
from services.admin.data_quality_service import compact_quality_summary
from services.admin.log_store import compute_ai_metrics, load_ai_log_records
from services.admin.rag_artifacts import build_rag_files_status, rag_file_paths


def system_overview(pipeline: RagPipeline) -> dict[str, Any]:
    rag_status = build_rag_files_status()
    records = load_ai_log_records()
    ai_metrics = compute_ai_metrics(records, include_rankings=False)
    ai_metrics.pop("top_queries", None)
    ai_metrics.pop("top_places", None)

    return {
        "service": "UnuTrip RAG v2",
        "runtime": {
            "runtime_mode": settings.ai_runtime_mode,
            "enable_gemini": settings.enable_gemini,
            "gemini_model": settings.gemini_model if settings.enable_gemini else None,
            "gemini_configured": bool(settings.gemini_api_key),
        },
        "rag": {
            "ready": rag_status["ready"],
            "using_reviewed": pipeline.place_store.status().get("using_reviewed"),
            "place_store": pipeline.place_store.status(),
            "files": rag_status["files"],
            "artifacts": manifest_status_block(),
        },
        "cache": pipeline.response_cache.status(),
        "ai_metrics": ai_metrics,
        "data_quality": compact_quality_summary(),
    }


def _retrieve_smoke_check(
    pipeline: RagPipeline,
    query: str,
    expected_province_norm: str,
) -> dict[str, Any]:
    try:
        retrieved = pipeline.retriever.retrieve(query=query, top_k=6)
        results = retrieved.get("results", [])
        intent = retrieved.get("intent", {})
        debug = retrieved.get("debug", {})
        top_places = [
            {
                "place_id": item.get("place_id"),
                "title": item.get("title"),
                "doc_type": item.get("doc_type"),
                "final_score": item.get("final_score"),
            }
            for item in results[:5]
        ]
        province_ok = intent.get("province_norm") == expected_province_norm
        results_ok = len(results) > 0
        return {
            "ok": province_ok and results_ok,
            "query": query,
            "expected_province_norm": expected_province_norm,
            "actual_province_norm": intent.get("province_norm"),
            "result_count": len(results),
            "debug": debug,
            "top_places": top_places,
        }
    except Exception as exc:
        return {"ok": False, "query": query, "error": str(exc)}


def system_self_test(pipeline: RagPipeline) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    paths = rag_file_paths()
    issues_file = settings.reports_dir / "data_quality_issues.json"
    autofix_file = settings.reports_dir / "data_quality_autofix_report.json"
    places_app_reviewed = paths["places_app_reviewed"]

    checks["health_ok"] = {"ok": True, "message": "Service is running."}

    missing_rag_files = [name for name, path in paths.items() if not path.exists()]
    checks["rag_files_ready"] = {
        "ok": len(missing_rag_files) == 0,
        "missing": missing_rag_files,
    }

    place_store_status = pipeline.place_store.status()
    checks["place_store_ready"] = {
        "ok": bool(place_store_status.get("loaded"))
        and int(place_store_status.get("place_count", 0)) > 0,
        "store": place_store_status,
    }
    checks["place_store_using_reviewed"] = {
        "ok": bool(place_store_status.get("using_reviewed")),
        "source_file": place_store_status.get("source_file"),
    }

    try:
        cache_status = pipeline.response_cache.status()
        checks["cache_ok"] = {"ok": bool(cache_status.get("enabled")), "cache": cache_status}
    except Exception as exc:
        checks["cache_ok"] = {"ok": False, "error": str(exc)}

    checks["data_quality_report_ok"] = {
        "ok": issues_file.exists() and autofix_file.exists() and places_app_reviewed.exists(),
        "issues_exists": issues_file.exists(),
        "autofix_exists": autofix_file.exists(),
        "reviewed_exists": places_app_reviewed.exists(),
    }

    checks["retrieve_khanhhoa_ok"] = _retrieve_smoke_check(
        pipeline,
        query="đi biển ở Khánh Hòa",
        expected_province_norm="khanh_hoa",
    )
    checks["retrieve_hue_ok"] = _retrieve_smoke_check(
        pipeline,
        query="đi Huế với bố mẹ lớn tuổi, ít đi bộ",
        expected_province_norm="thua_thien_hue",
    )

    passed = sum(1 for item in checks.values() if item.get("ok") is True)
    failed = sum(1 for item in checks.values() if item.get("ok") is not True)

    return {
        "service": "UnuTrip RAG v2",
        "ready": failed == 0,
        "passed": passed,
        "failed": failed,
        "checks": checks,
    }


def format_retrieve_debug_results(retrieved: dict[str, Any]) -> list[dict[str, Any]]:
    debug_results = []
    for item in retrieved.get("results", []):
        meta = item.get("metadata") or {}
        debug_results.append(
            {
                "doc_id": item.get("doc_id"),
                "doc_type": item.get("doc_type"),
                "place_id": item.get("place_id"),
                "title": item.get("title"),
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
                "bm25_score": item.get("bm25_score"),
                "rule_score": item.get("rule_score"),
                "final_score": item.get("final_score"),
                "reasons": item.get("reasons", []),
            }
        )
    return debug_results
