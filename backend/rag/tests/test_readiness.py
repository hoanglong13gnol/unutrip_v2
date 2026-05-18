"""Phase 6 — readiness policy."""

from __future__ import annotations

import pytest

from core.readiness import evaluate_readiness


def test_ready_when_pipeline_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("core.readiness.settings.ready_requires_index", False)
    ok, checks = evaluate_readiness(pipeline_loaded=True)
    assert ok is True
    assert checks["pipeline_loaded"] is True


def test_not_ready_without_index_when_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("core.readiness.settings.ready_requires_index", True)
    ok, checks = evaluate_readiness(pipeline_loaded=True)
    if checks["bm25_index_exists"]:
        assert ok is True
    else:
        assert ok is False
