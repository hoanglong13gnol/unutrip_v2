"""
Build dense embedding index aligned with bm25_index.pkl document order.

Requires: pip install -e ".[embeddings]"
Run after: scripts/06_build_bm25_index.py
"""

from __future__ import annotations

import json
import pickle
import warnings

import numpy as np

from core.artifacts import load_manifest, sha256_file, write_manifest
from core.config import settings
from retrieval.embedding_encoder import encode_texts
from retrieval.index_text import doc_full_text
from retrieval.vector_retriever import EMBEDDING_INDEX_FILE

BM25_INDEX_FILE = settings.indexes_dir / "bm25_index.pkl"


def _load_docs_from_bm25() -> tuple[list[dict], list[str]]:
    with BM25_INDEX_FILE.open("rb") as f:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            payload = pickle.load(f)
    docs = payload["docs"]
    texts = [doc_full_text(doc)[1] for doc in docs]
    return docs, texts


def main() -> None:
    if not BM25_INDEX_FILE.is_file():
        raise FileNotFoundError(f"BM25 index missing: {BM25_INDEX_FILE}. Run 06_build_bm25_index.py first.")

    model_name = settings.embedding_model
    docs, texts = _load_docs_from_bm25()
    print(f"Encoding {len(texts)} documents with {model_name!r}...")

    embeddings = encode_texts(texts, model_name, show_progress=len(texts) > 200)
    settings.indexes_dir.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        EMBEDDING_INDEX_FILE,
        embeddings=embeddings,
        model_name=np.array(model_name),
    )

    emb_sha = sha256_file(EMBEDDING_INDEX_FILE)
    manifest = load_manifest() or {}
    corpus_path = settings.rag_documents_file
    corpus_sha = str(manifest.get("corpus_sha256") or sha256_file(corpus_path))
    bm25_sha = str(manifest.get("bm25_sha256") or sha256_file(BM25_INDEX_FILE))

    from core.artifacts import artifact_path_for_manifest

    extra: dict = {
        "tfidf_enabled": manifest.get("tfidf_enabled", True),
        "embedding_enabled": True,
        "embedding_model": model_name,
        "embedding_dim": int(embeddings.shape[1]),
        "embedding_index_path": artifact_path_for_manifest(EMBEDDING_INDEX_FILE),
        "embedding_sha256": emb_sha,
    }
    if manifest.get("tfidf_min_df") is not None:
        extra["tfidf_min_df"] = manifest["tfidf_min_df"]

    write_manifest(
        corpus_path=corpus_path,
        corpus_sha256=corpus_sha,
        bm25_index_path=BM25_INDEX_FILE,
        bm25_sha256=bm25_sha,
        document_count=len(docs),
        extra=extra,
    )

    report = {
        "embedding_file": str(EMBEDDING_INDEX_FILE),
        "document_count": len(docs),
        "embedding_dim": int(embeddings.shape[1]),
        "model_name": model_name,
        "embedding_sha256": emb_sha,
    }
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.reports_dir / "build_embedding_index_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved embeddings: {EMBEDDING_INDEX_FILE} ({embeddings.shape[1]}d)")
    print(f"Updated manifest: {settings.indexes_dir / 'rag_artifacts_manifest.json'}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
