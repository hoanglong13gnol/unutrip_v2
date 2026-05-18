"""Admin: system overview and self-test."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.deps import PipelineDep
from services.admin.system_service import system_overview, system_self_test

router = APIRouter()


@router.get("/system/overview")
def admin_system_overview(pipeline: PipelineDep) -> dict[str, Any]:
    return system_overview(pipeline)


@router.get("/system/self-test")
def admin_system_self_test(pipeline: PipelineDep) -> dict[str, Any]:
    return system_self_test(pipeline)
