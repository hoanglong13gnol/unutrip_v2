"""Admin: RAG status, place store, retrieval debug, cache."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.deps import PipelineDep
from app.schemas import AdminRagRetrieveDebugRequest
from services.admin.rag_artifacts import rag_status_payload
from services.admin.system_service import format_retrieve_debug_results

router = APIRouter()


@router.post("/rag/retrieve-debug")
def admin_rag_retrieve_debug(
    pipeline: PipelineDep,
    request: AdminRagRetrieveDebugRequest,
) -> dict[str, Any]:
    retrieved = pipeline.retriever.retrieve(query=request.message, top_k=request.top_k)
    return {
        "query": request.message,
        "intent": retrieved.get("intent"),
        "debug": retrieved.get("debug"),
        "results": format_retrieve_debug_results(retrieved),
    }


@router.get("/rag/status")
def admin_rag_status() -> dict[str, Any]:
    return rag_status_payload()


@router.get("/rag/place/{place_id}")
def admin_rag_place_detail(pipeline: PipelineDep, place_id: str) -> dict[str, Any]:
    place = pipeline.place_store.get(place_id)
    if place is None:
        return {
            "found": False,
            "place_id": place_id,
            "message": "Place not found",
            "store": pipeline.place_store.status(),
        }
    return {"found": True, "place": place}


@router.post("/rag/place-store/reload")
def admin_rag_place_store_reload(pipeline: PipelineDep) -> dict[str, Any]:
    pipeline.place_store.load()
    return {"reloaded": True, "store": pipeline.place_store.status()}


@router.get("/rag/places/search")
def admin_rag_places_search(
    pipeline: PipelineDep,
    q: str | None = None,
    province: str | None = None,
    category: str | None = None,
    active_only: bool = True,
    limit: int = 20,
    min_score: float | None = None,
) -> dict[str, Any]:
    results = pipeline.place_store.search(
        q=q,
        province=province,
        category=category,
        active_only=active_only,
        limit=limit,
        min_score=min_score,
    )
    return {
        "query": q,
        "province": province,
        "category": category,
        "active_only": active_only,
        "limit": limit,
        "min_score": min_score,
        "count": len(results),
        "results": results,
        "store": pipeline.place_store.status(),
    }


@router.get("/cache/status")
def admin_cache_status(pipeline: PipelineDep) -> dict[str, Any]:
    return pipeline.response_cache.status()


@router.post("/cache/clear")
def admin_cache_clear(pipeline: PipelineDep) -> dict[str, Any]:
    return pipeline.response_cache.clear()
