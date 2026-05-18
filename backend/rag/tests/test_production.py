"""Phase 6 — production config validation."""

from __future__ import annotations

import pytest

from core.production import assert_production_config, validate_production_config


def test_non_production_skips_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAG_ENV", raising=False)
    monkeypatch.setenv("NODE_ENV", "development")
    assert validate_production_config() == []
    assert_production_config()


def test_production_requires_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_ENV", "production")
    monkeypatch.delenv("RAG_INTERNAL_API_KEY", raising=False)
    monkeypatch.delenv("RAG_ADMIN_API_KEY", raising=False)
    monkeypatch.setenv("RAG_DEBUG", "false")

    errors = validate_production_config()
    assert any("RAG_INTERNAL_API_KEY" in e for e in errors)
    assert any("RAG_ADMIN_API_KEY" in e for e in errors)


def test_production_rejects_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_ENV", "production")
    monkeypatch.setenv("RAG_INTERNAL_API_KEY", "a" * 32)
    monkeypatch.setenv("RAG_ADMIN_API_KEY", "b" * 32)
    monkeypatch.setenv("RAG_DEBUG", "true")

    errors = validate_production_config()
    assert any("RAG_DEBUG" in e for e in errors)
