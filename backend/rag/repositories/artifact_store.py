"""Resolve BM25 corpus/index on disk — local dir, bundle URL, or pre-built paths."""

from __future__ import annotations

import logging
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from core.config import settings

logger = logging.getLogger(__name__)

_ARTIFACT_REL_PATHS = (
    "processed/places_rag_documents.jsonl",
    "indexes/bm25_index.pkl",
    "indexes/rag_artifacts_manifest.json",
    "processed/places_app.json",
)


def index_is_present() -> bool:
    manifest = settings.indexes_dir / "rag_artifacts_manifest.json"
    index = settings.indexes_dir / "bm25_index.pkl"
    return bool(manifest.is_file() and index.is_file())


def _data_root() -> Path:
    root: Path = settings.root_dir
    return root / "data"


def _copy_tree_file(src_root: Path, rel: str, *, required: bool) -> None:
    src = src_root / rel
    dst = _data_root() / rel
    if not src.is_file():
        if required:
            raise FileNotFoundError(f"Missing required artifact file: {src}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    logger.info("Copied artifact %s -> %s", src, dst)


def materialize_from_directory(source_dir: Path) -> None:
    """Copy known artifact paths from a release directory or volume mount."""
    root = source_dir.expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    for rel in _ARTIFACT_REL_PATHS:
        _copy_tree_file(root, rel, required=rel.endswith(("bm25_index.pkl", "rag_artifacts_manifest.json")))


def materialize_from_zip(zip_path: Path) -> None:
    """Extract a release zip whose paths are rooted at `data/` (or repo-relative)."""
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        prefix = ""
        if any(n.startswith("data/") for n in names):
            prefix = "data/"
        elif any(n.startswith("backend/rag/data/") for n in names):
            prefix = "backend/rag/data/"

        extract_root = _data_root()
        extract_root.mkdir(parents=True, exist_ok=True)
        for rel in _ARTIFACT_REL_PATHS:
            member = prefix + rel
            if member not in names:
                if rel.endswith(("bm25_index.pkl", "rag_artifacts_manifest.json")):
                    raise FileNotFoundError(f"Bundle missing {member}")
                continue
            target = extract_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            logger.info("Extracted %s", target)


def download_bundle(url: str, *, timeout_s: int = 120) -> Path:
    suffix = ".zip" if url.lower().endswith(".zip") else ".bundle"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = Path(tmp.name)
    tmp.close()
    logger.info("Downloading artifact bundle from %s", url)
    req = urllib.request.Request(url, headers={"User-Agent": "unutrip-rag/0.3"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp, tmp_path.open("wb") as out:
        shutil.copyfileobj(resp, out)
    return tmp_path


def verify_or_raise() -> None:
    from scripts.verify_rag_artifacts import verify_manifest

    code = verify_manifest(allow_missing=False)
    if code != 0:
        raise RuntimeError("Artifact manifest verification failed after materialize")


def ensure_runtime_artifacts(
    *,
    source_dir: Path | None = None,
    bundle_url: str | None = None,
    force: bool = False,
) -> bool:
    """
    Ensure BM25 index + manifest exist under data/.

    Returns True when index was already present or successfully materialized.
    """
    if index_is_present() and not force:
        return True

    src = source_dir or settings.artifact_source_dir
    url = bundle_url or settings.artifact_bundle_url

    if src is not None:
        materialize_from_directory(src)
    elif url:
        bundle_path = download_bundle(url)
        try:
            if str(bundle_path).lower().endswith(".zip"):
                materialize_from_zip(bundle_path)
            else:
                raise ValueError("RAG_ARTIFACT_BUNDLE_URL must point to a .zip file")
        finally:
            bundle_path.unlink(missing_ok=True)
    else:
        logger.warning(
            "BM25 index not on disk; set RAG_ARTIFACT_SOURCE_DIR or RAG_ARTIFACT_BUNDLE_URL, "
            "or run: python jobs/build_rag_artifacts.py --from-db"
        )
        return False

    verify_or_raise()
    return index_is_present()
