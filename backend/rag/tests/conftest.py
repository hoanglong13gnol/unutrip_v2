"""Shared pytest fixtures (HTTP client with mocked RAG pipeline)."""

from __future__ import annotations

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
    """BM25 index from tracked fixture corpus (build once per test session)."""
    index_path = settings.indexes_dir / "bm25_index.pkl"
    corpus_path = settings.rag_documents_file

    if not (index_path.is_file() and corpus_path.is_file()):
        subprocess.check_call(
            [sys.executable, str(RAG_ROOT / "jobs" / "build_rag_artifacts.py"), "--from-fixture"],
            cwd=str(RAG_ROOT),
        )
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
