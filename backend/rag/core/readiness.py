"""Readiness evaluation for /health/ready (Phase 6)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.artifacts import load_manifest
from core.config import settings
from core.production import validate_production_config


def evaluate_readiness(*, pipeline_loaded: bool) -> tuple[bool, dict[str, Any]]:
    bm25_path: Path = settings.indexes_dir / "bm25_index.pkl"
    manifest = load_manifest()

    checks: dict[str, Any] = {
        "pipeline_loaded": pipeline_loaded,
        "bm25_index_exists": bm25_path.is_file(),
        "manifest_present": manifest is not None,
        "ready_requires_index": settings.ready_requires_index,
        "rag_env": settings.rag_env,
    }

    if settings.ready_requires_index:
        retrieval_ok = pipeline_loaded and checks["bm25_index_exists"]
    else:
        retrieval_ok = pipeline_loaded

    prod_errors = validate_production_config()
    checks["production_config_ok"] = not prod_errors
    if prod_errors:
        checks["production_errors"] = prod_errors

    ok = retrieval_ok and checks["production_config_ok"]
    return ok, checks
