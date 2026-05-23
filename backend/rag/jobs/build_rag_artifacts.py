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
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    env = os.environ.copy()
    root = str(ROOT)
    existing = env.get("PYTHONPATH", "")
    if root not in existing.split(os.pathsep):
        env["PYTHONPATH"] = root if not existing else f"{root}{os.pathsep}{existing}"
    subprocess.check_call(cmd, cwd=root, env=env)


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

    py = sys.executable

    if args.from_fixture and not args.skip_export:
        run([py, str(ROOT / "scripts" / "sync_fixture_data.py")])

    if args.from_db and not args.skip_export:
        run([py, str(ROOT / "scripts" / "export_rag_knowledge_base_to_corpus.py")])
        if args.export_places:
            run([py, str(ROOT / "scripts" / "export_app_places_to_json.py")])

    run([py, str(ROOT / "scripts" / "06_build_bm25_index.py")])

    build_embeddings = args.with_embeddings
    if not args.skip_embeddings:
        import os

        build_embeddings = build_embeddings or os.getenv("RAG_BUILD_EMBEDDINGS", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
    if build_embeddings and not args.skip_embeddings:
        run([py, str(ROOT / "scripts" / "07_build_embedding_index.py")])


if __name__ == "__main__":
    main()
