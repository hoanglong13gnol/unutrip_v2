"""
Fetch or copy production RAG artifacts before startup (Phase D).

Environment:
  RAG_ARTIFACT_SOURCE_DIR   — local directory with data/processed + data/indexes layout
  RAG_ARTIFACT_BUNDLE_URL   — HTTPS URL to a .zip (paths: data/processed/..., data/indexes/...)
  RAG_ARTIFACT_FETCH_FORCE  — re-copy even when index already exists

Usage:
  python scripts/fetch_rag_artifacts.py
  python scripts/fetch_rag_artifacts.py --source-dir /mnt/rag-release
  python scripts/fetch_rag_artifacts.py --url https://releases.example/unutrip-rag-artifacts.zip
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from core.config import settings
from repositories.artifact_store import ensure_runtime_artifacts, index_is_present

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description="Materialize RAG BM25 artifacts on disk")
    ap.add_argument("--source-dir", type=Path, help="Override RAG_ARTIFACT_SOURCE_DIR")
    ap.add_argument("--url", help="Override RAG_ARTIFACT_BUNDLE_URL")
    ap.add_argument("--force", action="store_true", help="Re-fetch even if index exists")
    args = ap.parse_args()

    force = args.force or os.getenv("RAG_ARTIFACT_FETCH_FORCE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    source = args.source_dir
    if source is None and settings.artifact_source_dir is not None:
        source = settings.artifact_source_dir
    url = args.url or settings.artifact_bundle_url

    if not source and not url and not index_is_present():
        print(
            "ERROR: no artifacts on disk and no RAG_ARTIFACT_SOURCE_DIR / RAG_ARTIFACT_BUNDLE_URL",
            file=sys.stderr,
        )
        sys.exit(1)

    ok = ensure_runtime_artifacts(source_dir=source, bundle_url=url, force=force)
    if not ok:
        sys.exit(1)
    print("OK artifacts ready under", settings.root_dir / "data")


if __name__ == "__main__":
    main()
