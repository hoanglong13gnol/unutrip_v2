"""Phase 7 — shared Node/RAG contract fixture under docs/v2/fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from domain.contracts.rag_chat_simple import validate_rag_chat_simple

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE = REPO_ROOT / "docs" / "v2" / "fixtures" / "rag_chat_simple_sample.json"


def test_shared_rag_chat_simple_fixture_validates() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    parsed, issues = validate_rag_chat_simple(payload)
    assert issues == []
    assert parsed is not None
    assert parsed.places[0].place_id == "FIX_KH_BEACH_01"
    assert parsed.fallback_used is False
