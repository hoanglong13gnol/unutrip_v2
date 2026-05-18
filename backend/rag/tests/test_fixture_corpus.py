"""Phase 4 — tracked fixture corpus integrity."""

from __future__ import annotations

import json

from core.fixture_paths import FIXTURE_CORPUS, FIXTURE_PLACES_APP


def _load_jsonl(path) -> list[dict]:
    docs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            docs.append(json.loads(line))
    return docs


def test_fixture_corpus_has_place_docs_for_golden_queries() -> None:
    docs = _load_jsonl(FIXTURE_CORPUS)
    place_ids = {d.get("place_id") for d in docs if d.get("doc_type") == "place"}
    assert "FIX_KH_BEACH_01" in place_ids
    assert "FIX_HUE_TEMPLE_01" in place_ids
    provinces = {
        (d.get("metadata") or {}).get("province_norm")
        for d in docs
        if d.get("doc_type") == "place"
    }
    assert "khanh_hoa" in provinces
    assert "thua_thien_hue" in provinces


def test_fixture_places_app_sample_loads() -> None:
    data = json.loads(FIXTURE_PLACES_APP.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 2
    assert all(p.get("place_id") for p in data)
