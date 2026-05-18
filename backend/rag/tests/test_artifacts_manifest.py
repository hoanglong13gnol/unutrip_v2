"""P0 — portable manifest paths and resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from core import artifacts
from core.artifacts import artifact_path_for_manifest, manifest_path_issues, resolve_artifact_path, write_manifest


def test_artifact_path_for_manifest_relative_posix(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(artifacts.settings, "root_dir", tmp_path)
    corpus = tmp_path / "data" / "processed" / "places_rag_documents.jsonl"
    corpus.parent.mkdir(parents=True)
    corpus.write_text("{}", encoding="utf-8")
    assert artifact_path_for_manifest(corpus) == "data/processed/places_rag_documents.jsonl"


def test_artifact_path_for_manifest_rejects_outside_root(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(artifacts.settings, "root_dir", tmp_path)
    outside = tmp_path.parent / "outside.jsonl"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="outside RAG root"):
        artifact_path_for_manifest(outside)


def test_resolve_artifact_path_relative_and_absolute(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(artifacts.settings, "root_dir", tmp_path)
    rel_file = tmp_path / "data" / "indexes" / "bm25_index.pkl"
    rel_file.parent.mkdir(parents=True)
    rel_file.write_bytes(b"x")

    assert resolve_artifact_path("data/indexes/bm25_index.pkl") == rel_file.resolve()
    assert resolve_artifact_path(str(rel_file.resolve())) == rel_file.resolve()


def test_manifest_path_issues_rejects_absolute() -> None:
    issues = manifest_path_issues(
        {
            "corpus_path": "E:/bad/places_rag_documents.jsonl",
            "bm25_index_path": "data/indexes/bm25_index.pkl",
        }
    )
    assert any("corpus_path" in msg and "absolute" in msg for msg in issues)


def test_write_manifest_stores_relative_paths(tmp_path, monkeypatch) -> None:
    indexes = tmp_path / "data" / "indexes"
    processed = tmp_path / "data" / "processed"
    indexes.mkdir(parents=True)
    processed.mkdir(parents=True)
    corpus = processed / "places_rag_documents.jsonl"
    index = indexes / "bm25_index.pkl"
    corpus.write_text("{}\n", encoding="utf-8")
    index.write_bytes(b"idx")

    monkeypatch.setattr(artifacts.settings, "root_dir", tmp_path)
    monkeypatch.setattr(artifacts.settings, "indexes_dir", indexes)
    monkeypatch.setattr(artifacts, "manifest_path", lambda: indexes / "rag_artifacts_manifest.json")

    payload = write_manifest(
        corpus_path=corpus,
        corpus_sha256="a" * 64,
        bm25_index_path=index,
        bm25_sha256="b" * 64,
        document_count=1,
    )
    assert payload["corpus_path"] == "data/processed/places_rag_documents.jsonl"
    assert payload["bm25_index_path"] == "data/indexes/bm25_index.pkl"
    assert not Path(payload["corpus_path"]).is_absolute()


def test_verify_strict_rejects_absolute_manifest(monkeypatch, tmp_path) -> None:
    from scripts.verify_rag_artifacts import verify_manifest

    monkeypatch.setattr(
        "scripts.verify_rag_artifacts.load_manifest",
        lambda: {
            "corpus_path": str(tmp_path / "data" / "processed" / "places_rag_documents.jsonl"),
            "bm25_index_path": "data/indexes/bm25_index.pkl",
            "corpus_sha256": "a",
            "bm25_sha256": "b",
        },
    )
    assert verify_manifest(allow_missing=False, require_portable_paths=True) == 1
