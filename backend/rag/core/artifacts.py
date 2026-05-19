"""Versioned RAG artifact manifest (corpus + index checksums)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from core.config import settings

MANIFEST_NAME = "rag_artifacts_manifest.json"
_MANIFEST_PATH_KEYS = ("corpus_path", "bm25_index_path", "embedding_index_path")


def manifest_path() -> Path:
    return settings.indexes_dir / MANIFEST_NAME


def artifact_path_for_manifest(path: Path) -> str:
    """Store paths relative to RAG root (POSIX) for portable manifests."""
    resolved = path.expanduser().resolve()
    root = settings.root_dir.resolve()
    try:
        rel = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Artifact path {path} is outside RAG root {root}") from exc
    return rel.as_posix()


def resolve_artifact_path(stored: str) -> Path:
    """Resolve manifest path (repo-relative or legacy absolute)."""
    raw = stored.strip()
    p = Path(raw)
    if p.is_absolute():
        return p.resolve()
    return (settings.root_dir / p).resolve()


def manifest_path_issues(m: dict[str, Any]) -> list[str]:
    """Return portability violations (absolute paths, traversal, etc.)."""
    issues: list[str] = []
    for key in _MANIFEST_PATH_KEYS:
        val = m.get(key)
        if key == "embedding_index_path" and val is None:
            continue
        if not isinstance(val, str) or not val.strip():
            issues.append(f"{key} missing or empty")
            continue
        if Path(val).is_absolute():
            issues.append(f"{key} must be repo-relative, not absolute: {val!r}")
        if ".." in Path(val).parts:
            issues.append(f"{key} must not contain '..': {val!r}")
        if val.startswith("\\\\"):
            issues.append(f"{key} must not be a UNC path: {val!r}")
    return issues


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict[str, Any] | None:
    path = manifest_path()
    if not path.exists():
        return None
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def write_manifest(
    *,
    corpus_path: Path,
    corpus_sha256: str,
    bm25_index_path: Path,
    bm25_sha256: str,
    document_count: int,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings.indexes_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "built_at_utc": datetime.now(UTC).isoformat(),
        "api_version": settings.api_version,
        "corpus_path": artifact_path_for_manifest(corpus_path),
        "corpus_sha256": corpus_sha256,
        "bm25_index_path": artifact_path_for_manifest(bm25_index_path),
        "bm25_sha256": bm25_sha256,
        "document_count": document_count,
        "tfidf_enabled": bool(extra and extra.get("tfidf_enabled")),
    }
    if extra:
        for key, value in extra.items():
            if key not in payload:
                payload[key] = value
    manifest_path().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def manifest_status_block() -> dict[str, Any]:
    m = load_manifest()
    if not m:
        return {"present": False}
    return {
        "present": True,
        "built_at_utc": m.get("built_at_utc"),
        "api_version": m.get("api_version"),
        "corpus_sha256": m.get("corpus_sha256"),
        "bm25_sha256": m.get("bm25_sha256"),
        "document_count": m.get("document_count"),
        "tfidf_enabled": m.get("tfidf_enabled"),
        "embedding_enabled": m.get("embedding_enabled"),
        "embedding_model": m.get("embedding_model"),
        "corpus_path": m.get("corpus_path"),
    }
