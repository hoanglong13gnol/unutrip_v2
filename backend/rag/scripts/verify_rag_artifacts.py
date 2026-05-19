"""
Verify rag_artifacts_manifest.json matches on-disk corpus and BM25 index (CI guard).

Exit 1 on mismatch. Default (strict): corpus + index + manifest must all match.
Use --allow-missing for local dev when only the tracked manifest exists without large files.
"""

from __future__ import annotations

import argparse
import sys

from core.artifacts import load_manifest, manifest_path_issues, resolve_artifact_path, sha256_file


def verify_manifest(*, allow_missing: bool = False, require_portable_paths: bool = True) -> int:
    m = load_manifest()
    if not m:
        print("ERROR: no manifest; run jobs/build_rag_artifacts.py or scripts/06_build_bm25_index.py")
        return 0 if allow_missing else 1

    if require_portable_paths and not allow_missing:
        issues = manifest_path_issues(m)
        if issues:
            for msg in issues:
                print("ERROR:", msg)
            return 1

    corpus = resolve_artifact_path(str(m["corpus_path"]))
    bm25 = resolve_artifact_path(str(m["bm25_index_path"]))

    if not bm25.exists():
        print("ERROR: BM25 index missing:", bm25)
        return 0 if allow_missing else 1

    b_sha = sha256_file(bm25)
    if b_sha != m.get("bm25_sha256"):
        print("ERROR: bm25_sha256 mismatch", b_sha, "!=", m.get("bm25_sha256"))
        return 1

    if not corpus.exists():
        print("ERROR: corpus missing:", corpus)
        return 0 if allow_missing else 1

    c_sha = sha256_file(corpus)
    if c_sha != m.get("corpus_sha256"):
        print("ERROR: corpus_sha256 mismatch", c_sha, "!=", m.get("corpus_sha256"))
        return 1

    if m.get("embedding_enabled"):
        emb_rel = m.get("embedding_index_path")
        if not isinstance(emb_rel, str) or not emb_rel.strip():
            print("ERROR: embedding_enabled but embedding_index_path missing")
            return 1
        emb_path = resolve_artifact_path(emb_rel)
        if not emb_path.exists():
            print("ERROR: embedding index missing:", emb_path)
            return 0 if allow_missing else 1
        emb_sha = sha256_file(emb_path)
        if emb_sha != m.get("embedding_sha256"):
            print("ERROR: embedding_sha256 mismatch", emb_sha, "!=", m.get("embedding_sha256"))
            return 1

    doc_count = m.get("document_count")
    emb_note = " + embeddings" if m.get("embedding_enabled") else ""
    print(
        "OK manifest matches corpus + bm25 index"
        + emb_note
        + (f" ({doc_count} docs)" if doc_count is not None else "")
    )
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--allow-missing",
        action="store_true",
        help="Pass when corpus/index absent (local dev with manifest-only checkout)",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Alias for default CI mode (corpus + index required)",
    )
    args = ap.parse_args()
    allow_missing = args.allow_missing and not args.strict
    sys.exit(verify_manifest(allow_missing=allow_missing))


if __name__ == "__main__":
    main()
