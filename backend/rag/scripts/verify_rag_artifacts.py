"""
Verify rag_artifacts_manifest.json matches on-disk corpus and BM25 index (CI guard).

Exit 1 on mismatch. Exit 0 if manifest missing (warn) or files missing with --allow-missing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.artifacts import load_manifest, sha256_file

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-missing", action="store_true")
    args = ap.parse_args()

    m = load_manifest()
    if not m:
        print("WARN: no manifest; run scripts/06_build_bm25_index.py")
        sys.exit(0 if args.allow_missing else 1)

    corpus = ROOT / Path(m["corpus_path"])
    bm25 = ROOT / Path(m["bm25_index_path"])

    if not bm25.exists():
        print("ERROR: BM25 index path from manifest does not exist:", bm25)
        sys.exit(0 if args.allow_missing else 1)

    b_sha = sha256_file(bm25)
    if b_sha != m.get("bm25_sha256"):
        print("ERROR: bm25_sha256 mismatch", b_sha, m.get("bm25_sha256"))
        sys.exit(1)

    if not corpus.exists():
        print("WARN: corpus missing (expected at", corpus, ") — BM25 index checksum OK")
        sys.exit(0 if args.allow_missing else 1)

    c_sha = sha256_file(corpus)
    if c_sha != m.get("corpus_sha256"):
        print("ERROR: corpus_sha256 mismatch", c_sha, m.get("corpus_sha256"))
        sys.exit(1)

    print("OK manifest matches corpus + bm25 index")


if __name__ == "__main__":
    main()
