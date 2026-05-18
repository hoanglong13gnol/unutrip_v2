"""
Second-stage reranking for hybrid retrieval (Phase 5).

Default: dense TF-IDF cosine rescore on lexical candidates (no extra deps).
Optional: cross-encoder via sentence-transformers (`RAG_ENABLE_CROSS_ENCODER=true`).
"""

from __future__ import annotations

from typing import Any

from core.config import settings
from retrieval.bm25_retriever import BM25Retriever

_CROSS_ENCODER = None
_CROSS_ENCODER_LOAD_FAILED = False


def _candidate_text(item: dict[str, Any]) -> str:
    title = str(item.get("title") or "")
    body = str(item.get("text") or "")
    meta = item.get("metadata") or {}
    meta_bits = " ".join(
        str(meta.get(k) or "")
        for k in ("province", "city", "category_main", "category_sub")
    )
    return f"{title}\n{body}\n{meta_bits}".strip()


def dense_tfidf_rerank(
    query: str,
    items: list[dict[str, Any]],
    retriever: BM25Retriever,
    *,
    top_k: int,
    blend_weight: float = 50.0,
) -> list[dict[str, Any]]:
    """Rescore candidates with in-index char TF-IDF cosine similarity."""
    if not items or not retriever.has_tfidf():
        return items[:top_k]

    from sklearn.preprocessing import normalize

    if retriever.tfidf_vectorizer is None or retriever.tfidf_X_norm is None:
        return items[:top_k]

    q = normalize(retriever.tfidf_vectorizer.transform([query]))
    doc_id_to_idx = {
        str(doc.get("doc_id")): i
        for i, doc in enumerate(retriever.docs)
        if doc.get("doc_id")
    }

    rescored: list[dict[str, Any]] = []
    for item in items:
        enriched = dict(item)
        idx = doc_id_to_idx.get(str(item.get("doc_id") or ""))
        sim = 0.0
        if idx is not None:
            sim = float((retriever.tfidf_X_norm[idx] @ q.T).toarray()[0, 0])
        base = float(enriched.get("final_score", enriched.get("score", 0.0)))
        enriched["dense_score"] = round(sim, 6)
        enriched["final_score"] = round(base + sim * blend_weight, 4)
        enriched.setdefault("reasons", [])
        if sim > 0.05 and "dense_tfidf" not in enriched["reasons"]:
            enriched["reasons"] = list(enriched["reasons"]) + ["dense_tfidf"]
        rescored.append(enriched)

    rescored.sort(key=lambda x: float(x.get("final_score", 0.0)), reverse=True)
    return rescored[:top_k]


def cross_encoder_rerank(
    query: str,
    items: list[dict[str, Any]],
    *,
    top_k: int,
    model_name: str | None = None,
) -> list[dict[str, Any]]:
    """Optional cross-encoder rescore (requires sentence-transformers)."""
    global _CROSS_ENCODER, _CROSS_ENCODER_LOAD_FAILED

    if not items:
        return []

    if _CROSS_ENCODER_LOAD_FAILED:
        return items[:top_k]

    if _CROSS_ENCODER is None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            _CROSS_ENCODER_LOAD_FAILED = True
            raise RuntimeError(
                "Install optional rerank deps: pip install -r requirements-rerank.txt"
            ) from exc
        name = model_name or settings.cross_encoder_model
        _CROSS_ENCODER = CrossEncoder(name)

    pairs = [(query, _candidate_text(item)) for item in items]
    scores = _CROSS_ENCODER.predict(pairs)

    rescored: list[dict[str, Any]] = []
    for item, ce_score in zip(items, scores, strict=True):
        enriched = dict(item)
        ce = float(ce_score)
        base = float(enriched.get("final_score", enriched.get("score", 0.0)))
        enriched["cross_encoder_score"] = round(ce, 6)
        enriched["final_score"] = round(base + ce * 8.0, 4)
        enriched.setdefault("reasons", [])
        if "cross_encoder" not in enriched["reasons"]:
            enriched["reasons"] = list(enriched["reasons"]) + ["cross_encoder"]
        rescored.append(enriched)

    rescored.sort(key=lambda x: float(x.get("final_score", 0.0)), reverse=True)
    return rescored[:top_k]


def rerank_candidates(
    query: str,
    items: list[dict[str, Any]],
    *,
    retriever: BM25Retriever,
    top_k: int,
) -> tuple[list[dict[str, Any]], str]:
    """
    Apply configured reranker to pre-rule-scored candidates.
    Returns (items, mode_label).
    """
    if not settings.enable_rerank or not items:
        return items[:top_k], "disabled"

    pool = items[: max(top_k * 4, settings.rerank_candidate_pool)]

    if settings.enable_cross_encoder:
        try:
            return cross_encoder_rerank(query, pool, top_k=top_k), "cross_encoder"
        except RuntimeError:
            pass

    if retriever.has_tfidf():
        return dense_tfidf_rerank(query, pool, retriever, top_k=top_k), "dense_tfidf"

    return pool[:top_k], "lexical_only"


def maybe_cross_encoder_rerank(
    query: str,
    items: list[dict[str, Any]],
    *,
    top_k: int,
    enabled: bool = False,
) -> list[dict[str, Any]]:
    """Backward-compatible stub API; prefer `rerank_candidates`."""
    if not enabled or not items:
        return items[:top_k]
    try:
        return cross_encoder_rerank(query, items, top_k=top_k)
    except RuntimeError:
        return items[:top_k]
