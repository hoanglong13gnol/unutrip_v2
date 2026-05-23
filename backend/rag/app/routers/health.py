"""Health and runtime metadata routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.artifacts import manifest_status_block
from core.config import settings
from core.readiness import evaluate_readiness

router = APIRouter(tags=["Health"])


@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": settings.project_name,
        "version": settings.api_version,
    }


@router.get("/health/ready")
def health_ready(request: Request) -> JSONResponse:
    pipeline = getattr(request.app.state, "pipeline", None)
    ok, checks = evaluate_readiness(pipeline_loaded=pipeline is not None)

    body: dict[str, Any] = {
        "status": "ready" if ok else "not_ready",
        "service": settings.project_name,
        "version": settings.api_version,
        **checks,
    }
    if ok:
        return JSONResponse(body)
    return JSONResponse(body, status_code=503)


@router.get("/runtime/status")
def runtime_status() -> dict[str, Any]:
    places_app_reviewed_file = settings.processed_data_dir / "places_app_reviewed.json"

    return {
        "service": "UnuTrip RAG v2",
        "runtime_mode": settings.ai_runtime_mode,
        "rag_env": settings.rag_env,
        "enable_gemini": settings.enable_gemini,
        "gemini_model": settings.gemini_model if settings.enable_gemini else None,
        "gemini_configured": bool(settings.gemini_api_key),
        "metrics_enabled": settings.enable_metrics,
        "places_master_ready": settings.places_master_file.exists(),
        "places_app_ready": settings.places_app_file.exists(),
        "places_app_reviewed_ready": places_app_reviewed_file.exists(),
        "places_itinerary_ready": settings.places_itinerary_file.exists(),
        "rag_documents_ready": settings.rag_documents_file.exists(),
        "bm25_index_ready": (settings.indexes_dir / "bm25_index.pkl").exists(),
        "artifacts": manifest_status_block(),
    }
