"""Phase 4 — artifact verify helper."""

from __future__ import annotations

from scripts.verify_rag_artifacts import verify_manifest


def test_verify_strict_fails_without_manifest(monkeypatch) -> None:
    monkeypatch.setattr("scripts.verify_rag_artifacts.load_manifest", lambda: None)
    assert verify_manifest(allow_missing=False) == 1


def test_verify_allow_missing_without_manifest(monkeypatch) -> None:
    monkeypatch.setattr("scripts.verify_rag_artifacts.load_manifest", lambda: None)
    assert verify_manifest(allow_missing=True) == 0
