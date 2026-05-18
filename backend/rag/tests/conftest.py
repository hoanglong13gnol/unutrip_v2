"""Shared pytest fixtures (HTTP client with mocked RAG pipeline)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.deps import get_pipeline, get_rag_service
from app.main import app
from core.config import settings
from services.rag_service import RagService

RAG_ROOT = Path(__file__).resolve().parents[1]

# CI fixture corpus is small; production local builds use thousands of docs.
_FIXTURE_MAX_DOCUMENT_COUNT = 50


def _fixture_artifacts_stale() -> bool:
    index_path = settings.indexes_dir / "bm25_index.pkl"
    manifest_path = settings.indexes_dir / "rag_artifacts_manifest.json"
    if not index_path.is_file() or not manifest_path.is_file():
        return True
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return True
    return int(manifest.get("document_count", 0)) > _FIXTURE_MAX_DOCUMENT_COUNT


def _build_fixture_artifacts() -> None:
    subprocess.check_call(
        [sys.executable, str(RAG_ROOT / "jobs" / "build_rag_artifacts.py"), "--from-fixture"],
        cwd=str(RAG_ROOT),
    )


def _sample_pipeline_result() -> dict[str, Any]:
    return {
        "answer": "Gợi ý thử nghiệm từ mock pipeline.",
        "places": [
            {
                "place_id": "AG_0001",
                "name": "Bãi biển Mock",
                "province": "Khánh Hòa",
                "city": "Nha Trang",
                "area": None,
                "category_main": "beach",
                "category_sub": None,
                "budget_level": "low",
                "walking_level": "easy",
                "kid_friendly": True,
                "elderly_friendly": True,
                "slot": "morning",
                "quality_score": 4.2,
                "recommended_use": "swim",
                "requires_realtime_check": False,
                "score": 12.5,
            }
        ],
        "warnings": [],
        "latency_ms": {"total": 42.0, "retrieval": 10.0, "generation": 5.0},
        "model_used": "mock",
        "fallback_used": False,
        "runtime_mode": "mock",
        "rag_mode": "balanced",
    }


@pytest.fixture(scope="session")
def fixture_bm25_index() -> Path:
    """BM25 index from tracked fixture corpus (rebuild if a production index is on disk)."""
    if _fixture_artifacts_stale():
        _build_fixture_artifacts()
    index_path = settings.indexes_dir / "bm25_index.pkl"
    assert index_path.is_file()
    return index_path


@pytest.fixture
def mock_pipeline() -> MagicMock:
    pipe = MagicMock()
    result = _sample_pipeline_result()
    pipe.run.return_value = result
    pipe.retriever.retrieve.return_value = {
        "query": "test",
        "intent": {"intent": "search_place", "province_norm": "khanh_hoa"},
        "results": [
            {
                "place_id": "AG_0001",
                "title": "Bãi biển Mock",
                "doc_id": "d1",
                "doc_type": "place",
                "metadata": {"province": "Khánh Hòa"},
                "final_score": 1.0,
                "reasons": [],
            }
        ],
        "debug": {"final_count": 1},
    }
    pipe.place_store.status.return_value = {
        "loaded": True,
        "place_count": 1,
        "using_reviewed": False,
        "source_file": "mock",
    }
    pipe.place_store.get.return_value = {"place_id": "AG_0001", "name": "Mock"}
    pipe.place_store.search.return_value = []
    pipe.response_cache.status.return_value = {"enabled": False, "entries": 0}
    pipe.response_cache.clear.return_value = {"cleared": True}
    return pipe


@pytest.fixture
def api_client(mock_pipeline: MagicMock, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # Root .env often sets RAG_INTERNAL_API_KEY for staging; HTTP tests use mocked pipeline.
    monkeypatch.setenv("RAG_INTERNAL_API_KEY", "")
    monkeypatch.setenv("RAG_ADMIN_API_KEY", "")
    monkeypatch.setattr("app.middleware.get_internal_api_key", lambda: None)
    monkeypatch.setattr("app.middleware.get_admin_api_key", lambda: None)
    monkeypatch.setattr("app.main.RagPipeline", lambda: mock_pipeline)
    monkeypatch.setattr("app.main.init_redis", lambda _url: None)
    monkeypatch.setattr("app.main.close_redis", lambda: None)

    svc = RagService(mock_pipeline)

    def _pipeline_dep() -> MagicMock:
        return mock_pipeline

    def _service_dep() -> RagService:
        return svc

    app.dependency_overrides[get_pipeline] = _pipeline_dep
    app.dependency_overrides[get_rag_service] = _service_dep

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
