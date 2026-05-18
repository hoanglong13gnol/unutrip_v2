"""Paths for tracked CI fixture corpora (Phase 4 reproducible data)."""

from __future__ import annotations

from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
FIXTURE_CORPUS = FIXTURES_DIR / "rag_corpus_sample.jsonl"
FIXTURE_PLACES_APP = FIXTURES_DIR / "places_app_sample.json"
