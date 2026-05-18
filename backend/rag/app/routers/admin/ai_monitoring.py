"""Admin: AI logs, metrics, debug query."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from app.deps import PipelineDep
from app.schemas import AdminAiDebugQueryRequest
from services.admin.log_store import compute_ai_metrics, load_ai_log_records, tail_logs

router = APIRouter()


@router.get("/ai/logs")
def admin_ai_logs(limit: int = 20) -> dict[str, Any]:
    return tail_logs(limit)


@router.get("/ai/metrics")
def admin_ai_metrics() -> dict[str, Any]:
    return compute_ai_metrics(load_ai_log_records(), include_rankings=True)


@router.post("/ai/debug-query")
async def admin_ai_debug_query(
    pipeline: PipelineDep,
    request: AdminAiDebugQueryRequest,
) -> dict[str, Any]:
    result = await run_in_threadpool(
        pipeline.run,
        request.message,
        request.top_k,
        request.mode,
        request.include_prompt,
    )
    return {
        "query": request.message,
        "answer": result.get("answer"),
        "places": result.get("places", []),
        "warnings": result.get("warnings", []),
        "latency_ms": result.get("latency_ms", {}),
        "model_used": result.get("model_used"),
        "fallback_used": result.get("fallback_used"),
        "runtime_mode": result.get("runtime_mode"),
        "rag_mode": result.get("rag_mode"),
        "debug": result.get("debug", {}),
        "prompt": result.get("prompt") if request.include_prompt else None,
        "context": result.get("context") if request.include_prompt else None,
    }
