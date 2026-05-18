"""Phase D — artifact materialize from directory / zip."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from core.artifacts import sha256_file, write_manifest
from repositories import artifact_store
from repositories.artifact_store import ensure_runtime_artifacts, materialize_from_directory, materialize_from_zip


def _patch_data_root(monkeypatch, rag_root: Path) -> Path:
    rag_data = rag_root / "data"
    monkeypatch.setattr(artifact_store.settings, "root_dir", rag_root)
    return rag_data


def test_materialize_from_directory(tmp_path, monkeypatch) -> None:
    release = tmp_path / "release"
    corpus = release / "processed" / "places_rag_documents.jsonl"
    index = release / "indexes" / "bm25_index.pkl"
    corpus.parent.mkdir(parents=True)
    index.parent.mkdir(parents=True)
    corpus.write_text('{"place_id":"p1","title":"Test"}\n', encoding="utf-8")
    index.write_bytes(b"fake-index")

    monkeypatch.setattr(artifact_store.settings, "root_dir", release)
    monkeypatch.setattr("core.artifacts.settings.root_dir", release)
    monkeypatch.setattr("core.artifacts.settings.indexes_dir", release / "indexes")
    write_manifest(
        corpus_path=corpus,
        corpus_sha256=sha256_file(corpus),
        bm25_index_path=index,
        bm25_sha256=sha256_file(index),
        document_count=1,
    )

    rag_root = tmp_path / "svc"
    rag_data = _patch_data_root(monkeypatch, rag_root)
    materialize_from_directory(release)

    assert (rag_data / "processed" / "places_rag_documents.jsonl").is_file()
    assert (rag_data / "indexes" / "bm25_index.pkl").read_bytes() == b"fake-index"


def test_ensure_skips_when_present(monkeypatch) -> None:
    monkeypatch.setattr(artifact_store, "index_is_present", lambda: True)

    def _fail(*_a, **_k):
        raise AssertionError("should not materialize")

    monkeypatch.setattr(artifact_store, "materialize_from_directory", _fail)
    assert ensure_runtime_artifacts(source_dir=Path("/unused")) is True


def test_materialize_from_zip(tmp_path, monkeypatch) -> None:
    bundle = tmp_path / "bundle.zip"
    with zipfile.ZipFile(bundle, "w") as zf:
        zf.writestr("data/processed/places_rag_documents.jsonl", '{"place_id":"z"}\n')
        zf.writestr("data/indexes/bm25_index.pkl", b"idx")
        zf.writestr("data/indexes/rag_artifacts_manifest.json", json.dumps({"document_count": 1}))

    rag_data = _patch_data_root(monkeypatch, tmp_path / "svc")
    materialize_from_zip(bundle)
    assert (rag_data / "indexes" / "bm25_index.pkl").read_bytes() == b"idx"
