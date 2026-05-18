"""Admin routes composed from focused sub-routers."""

from fastapi import APIRouter

from app.routers.admin import ai_monitoring, data_quality, rag_ops, system

router = APIRouter(prefix="/admin", tags=["Admin"])
router.include_router(ai_monitoring.router)
router.include_router(rag_ops.router)
router.include_router(data_quality.router)
router.include_router(system.router)
