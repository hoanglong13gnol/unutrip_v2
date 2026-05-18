"""AiRequestLogger JSONL append."""

from __future__ import annotations

import json

import pytest

from core.config import settings
from retrieval.logger import AiRequestLogger


def test_ai_request_logger_writes_jsonl(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "reports_dir", tmp_path)
    logger = AiRequestLogger()
    logger.log({"query": "hello", "model_used": "mock"})
    logger.log({"query": "second"})

    lines = logger.log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["query"] == "hello"
    assert "created_at" in first
