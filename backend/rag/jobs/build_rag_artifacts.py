"""
One-shot RAG artifact build: optional DB corpus export + BM25/TF-IDF index + manifest.

Usage (from backend/rag with .env DB_* if using --from-db):
  python jobs/build_rag_artifacts.py
  python jobs/build_rag_artifacts.py --from-db
  python jobs/build_rag_artifacts.py --from-fixture
  python jobs/build_rag_artifacts.py --skip-export
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_module(relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(f"unutrip_build_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script(relative_path: str, runner: Callable[..., None] | None = None) -> None:
    """Load a build script in-process (avoids subprocess PYTHONPATH issues in Docker)."""
    path = ROOT / relative_path
    print("+", path)
    module = _load_module(relative_path)
    if runner is not None:
        runner(module)
        return
    main = getattr(module, "main", None)
    if not callable(main):
        raise RuntimeError(f"Script has no main(): {path}")
    argv_backup = sys.argv[:]
    sys.argv = [str(path)]
    try:
        main()
    finally:
        sys.argv = argv_backup


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-db", action="store_true", help="Export rag_knowledge_base → JSONL, then build index")
    ap.add_argument(
        "--from-fixture",
        action="store_true",
        help="Copy tests/fixtures/* into data/processed, then build index (CI / offline)",
    )
    ap.add_argument(
        "--export-places",
        action="store_true",
        help="With --from-db, also export app_places to places_app.json",
    )
    ap.add_argument("--skip-export", action="store_true", help="Skip corpus export (use existing JSONL)")
    ap.add_argument(
        "--with-embeddings",
        action="store_true",
        help="Build dense embedding index (requires pip install -e \".[embeddings]\")",
    )
    ap.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip embedding build even if RAG_BUILD_EMBEDDINGS=true",
    )
    args = ap.parse_args()

    if args.from_db and args.from_fixture:
        ap.error("Use only one of --from-db or --from-fixture")

    if args.from_fixture and not args.skip_export:
        run_script("scripts/sync_fixture_data.py", lambda mod: mod.sync_fixture_data())

    if args.from_db and not args.skip_export:
        run_script("scripts/export_rag_knowledge_base_to_corpus.py")
        if args.export_places:
            run_script("scripts/export_app_places_to_json.py")

    run_script("scripts/06_build_bm25_index.py")

    build_embeddings = args.with_embeddings
    if not args.skip_embeddings:
        build_embeddings = build_embeddings or os.getenv("RAG_BUILD_EMBEDDINGS", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
    if build_embeddings and not args.skip_embeddings:
        run_script("scripts/07_build_embedding_index.py")


if __name__ == "__main__":
    main()
