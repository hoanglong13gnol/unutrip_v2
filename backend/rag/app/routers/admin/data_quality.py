"""Admin: data quality reports."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from services.admin import data_quality_service as dq

router = APIRouter()


@router.get("/data-quality/status")
def admin_data_quality_status() -> dict[str, Any]:
    return dq.status_payload()


@router.get("/data-quality/issues")
def admin_data_quality_issues(
    issue_type: str | None = None,
    severity: str | None = None,
    province: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    issues = dq.load_issues()
    return dq.filter_issues(
        issues,
        issue_type=issue_type,
        severity=severity,
        province=province,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get("/data-quality/autofix-changes")
def admin_data_quality_autofix_changes(
    province: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    return dq.filter_autofix_changes(province=province, q=q, limit=limit, offset=offset)


@router.get("/data-quality/summary-by-province")
def admin_data_quality_summary_by_province() -> dict[str, Any]:
    return dq.summary_by_province()
