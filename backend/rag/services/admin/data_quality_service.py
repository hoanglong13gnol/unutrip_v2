"""Data quality report readers (issues JSON + autofix CSV)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from core.config import settings
from services.admin.rag_artifacts import file_status


def _issues_path() -> Path:
    return settings.reports_dir / "data_quality_issues.json"


def _autofix_report_path() -> Path:
    return settings.reports_dir / "data_quality_autofix_report.json"


def _autofix_changes_path() -> Path:
    return settings.reports_dir / "data_quality_autofix_changes.csv"


def _reviewed_places_path() -> Path:
    return settings.processed_data_dir / "places_app_reviewed.json"


def _normalize_filter(value: str | None) -> str:
    return (value or "").strip().lower()


def load_issues() -> list[dict[str, Any]]:
    path = _issues_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("issues", []))
    except Exception:
        return []


def status_payload() -> dict[str, Any]:
    issues_file = _issues_path()
    autofix_file = _autofix_report_path()
    reviewed_file = _reviewed_places_path()

    scan_payload: dict[str, Any] = {
        "exists": False,
        "place_count": 0,
        "issue_count": 0,
        "issue_counts": {},
        "severity_counts": {},
    }

    if issues_file.exists():
        try:
            data = json.loads(issues_file.read_text(encoding="utf-8"))
            issues = data.get("issues", [])
            issue_counts: dict[str, int] = {}
            severity_counts: dict[str, int] = {}
            for issue in issues:
                issue_type = issue.get("issue_type") or "unknown"
                severity = issue.get("severity") or "unknown"
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            scan_payload = {
                "exists": True,
                "file": file_status(issues_file),
                "place_count": data.get("place_count", 0),
                "issue_count": data.get("issue_count", len(issues)),
                "issue_counts": issue_counts,
                "severity_counts": severity_counts,
            }
        except Exception as exc:
            scan_payload = {
                "exists": True,
                "file": file_status(issues_file),
                "error": str(exc),
                "place_count": 0,
                "issue_count": 0,
                "issue_counts": {},
                "severity_counts": {},
            }

    autofix_payload: dict[str, Any] = {
        "exists": False,
        "changed_count": 0,
        "output_file": None,
    }

    if autofix_file.exists():
        try:
            data = json.loads(autofix_file.read_text(encoding="utf-8"))
            autofix_payload = {
                "exists": True,
                "file": file_status(autofix_file),
                "input_file": data.get("input_file"),
                "output_file": data.get("output_file"),
                "place_count": data.get("place_count", 0),
                "changed_count": data.get("changed_count", 0),
            }
        except Exception as exc:
            autofix_payload = {
                "exists": True,
                "file": file_status(autofix_file),
                "error": str(exc),
                "changed_count": 0,
                "output_file": None,
            }

    return {
        "service": "UnuTrip RAG v2",
        "scan": scan_payload,
        "autofix": autofix_payload,
        "reviewed": {
            "exists": _reviewed_places_path().exists(),
            "file": file_status(reviewed_file),
        },
    }


def filter_issues(
    issues: list[dict[str, Any]],
    *,
    issue_type: str | None,
    severity: str | None,
    province: str | None,
    q: str | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    issue_type_filter = _normalize_filter(issue_type)
    severity_filter = _normalize_filter(severity)
    province_filter = _normalize_filter(province)
    q_filter = _normalize_filter(q)

    filtered: list[dict[str, Any]] = []
    for issue in issues:
        if issue_type_filter and _normalize_filter(issue.get("issue_type")) != issue_type_filter:
            continue
        if severity_filter and _normalize_filter(issue.get("severity")) != severity_filter:
            continue
        if province_filter and province_filter not in _normalize_filter(issue.get("province")):
            continue
        if q_filter:
            searchable = " ".join(
                [
                    str(issue.get("place_id") or ""),
                    str(issue.get("name") or ""),
                    str(issue.get("province") or ""),
                    str(issue.get("area") or ""),
                    str(issue.get("category_main") or ""),
                    str(issue.get("category_sub") or ""),
                    str(issue.get("message") or ""),
                ]
            ).lower()
            if q_filter not in searchable:
                continue
        filtered.append(issue)

    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    return {
        "total": len(filtered),
        "limit": limit,
        "offset": offset,
        "filters": {
            "issue_type": issue_type,
            "severity": severity,
            "province": province,
            "q": q,
        },
        "items": filtered[offset : offset + limit],
    }


def filter_autofix_changes(
    *,
    province: str | None,
    q: str | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    changes_file = _autofix_changes_path()
    if not changes_file.exists():
        return {
            "total": 0,
            "limit": limit,
            "offset": offset,
            "filters": {"province": province, "q": q},
            "items": [],
        }

    try:
        with changes_file.open("r", encoding="utf-8-sig", newline="") as f:
            records = list(csv.DictReader(f))
    except Exception as exc:
        return {
            "total": 0,
            "limit": limit,
            "offset": offset,
            "error": str(exc),
            "filters": {"province": province, "q": q},
            "items": [],
        }

    province_filter = _normalize_filter(province)
    q_filter = _normalize_filter(q)
    filtered: list[dict[str, Any]] = []

    for record in records:
        if province_filter:
            if province_filter not in _normalize_filter(record.get("province")):
                continue
        if q_filter:
            searchable = " ".join(
                [
                    str(record.get("place_id") or ""),
                    str(record.get("name") or ""),
                    str(record.get("province") or ""),
                    str(record.get("area") or ""),
                    str(record.get("old_category_main") or ""),
                    str(record.get("old_category_sub") or ""),
                    str(record.get("new_category_main") or ""),
                    str(record.get("new_category_sub") or ""),
                    str(record.get("reason") or ""),
                ]
            ).lower()
            if q_filter not in searchable:
                continue
        filtered.append(record)

    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    return {
        "total": len(filtered),
        "limit": limit,
        "offset": offset,
        "filters": {"province": province, "q": q},
        "items": filtered[offset : offset + limit],
    }


def summary_by_province() -> dict[str, Any]:
    issues_file = _issues_path()
    autofix_changes_file = _autofix_changes_path()
    province_map: dict[str, dict[str, Any]] = {}

    def get_row(province: str | None) -> dict[str, Any]:
        province_name = (province or "Unknown").strip() or "Unknown"
        if province_name not in province_map:
            province_map[province_name] = {
                "province": province_name,
                "issue_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "unknown_severity_count": 0,
                "autofix_count": 0,
                "issue_types": {},
            }
        return province_map[province_name]

    if issues_file.exists():
        try:
            issues = load_issues()
            for issue in issues:
                row = get_row(issue.get("province"))
                row["issue_count"] += 1
                severity = (issue.get("severity") or "unknown").strip().lower()
                if severity == "high":
                    row["high_count"] += 1
                elif severity == "medium":
                    row["medium_count"] += 1
                elif severity == "low":
                    row["low_count"] += 1
                else:
                    row["unknown_severity_count"] += 1
                issue_type = issue.get("issue_type") or "unknown"
                row["issue_types"][issue_type] = row["issue_types"].get(issue_type, 0) + 1
        except Exception as exc:
            return {"error": str(exc), "total_provinces": 0, "items": []}

    if autofix_changes_file.exists():
        try:
            with autofix_changes_file.open("r", encoding="utf-8-sig", newline="") as f:
                for record in csv.DictReader(f):
                    get_row(record.get("province"))["autofix_count"] += 1
        except Exception as exc:
            return {"error": str(exc), "total_provinces": 0, "items": []}

    items = sorted(
        province_map.values(),
        key=lambda item: (item["issue_count"], item["high_count"], item["autofix_count"]),
        reverse=True,
    )
    return {"total_provinces": len(items), "items": items}


def compact_quality_summary() -> dict[str, Any]:
    issues_file = _issues_path()
    autofix_file = _autofix_report_path()
    reviewed_file = _reviewed_places_path()

    data_quality: dict[str, Any] = {
        "scan_exists": issues_file.exists(),
        "autofix_exists": autofix_file.exists(),
        "reviewed_exists": reviewed_file.exists(),
        "place_count": 0,
        "issue_count": 0,
        "issue_counts": {},
        "severity_counts": {},
        "autofix_changed_count": 0,
    }

    if issues_file.exists():
        try:
            data = json.loads(issues_file.read_text(encoding="utf-8"))
            issues = data.get("issues", [])
            issue_counts: dict[str, int] = {}
            severity_counts: dict[str, int] = {}
            for issue in issues:
                issue_type = issue.get("issue_type") or "unknown"
                severity = issue.get("severity") or "unknown"
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            data_quality["place_count"] = data.get("place_count", 0)
            data_quality["issue_count"] = data.get("issue_count", len(issues))
            data_quality["issue_counts"] = issue_counts
            data_quality["severity_counts"] = severity_counts
        except Exception as exc:
            data_quality["scan_error"] = str(exc)

    if autofix_file.exists():
        try:
            data = json.loads(autofix_file.read_text(encoding="utf-8"))
            data_quality["autofix_changed_count"] = data.get("changed_count", 0)
        except Exception as exc:
            data_quality["autofix_error"] = str(exc)

    return data_quality
