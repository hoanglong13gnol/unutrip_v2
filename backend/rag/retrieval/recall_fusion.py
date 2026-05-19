"""Fuse multiple ranked retrieval lists (RRF + score blend)."""

from __future__ import annotations

from typing import Any

from retrieval.fusion import reciprocal_rank_fusion


def fuse_ranked_hit_lists(
    ranked_lists: list[tuple[str, list[dict[str, Any]]]],
    *,
    k: float = 60.0,
    score_scale: float = 400.0,
    lexical_blend: float = 0.01,
    limit: int = 120,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Merge named ranked lists with reciprocal rank fusion.

    Each hit dict must include ``doc_id``. Lexical ``score`` is blended after RRF.
    """
    non_empty = [(name, hits) for name, hits in ranked_lists if hits]
    if not non_empty:
        return [], {"mode": "empty"}

    if len(non_empty) == 1:
        name, hits = non_empty[0]
        return hits[:limit], {"mode": name, "lists": {name: len(hits)}}

    ids_lists = [
        [str(h["doc_id"]) for h in hits if h.get("doc_id")]
        for _, hits in non_empty
    ]
    rrf_scores = reciprocal_rank_fusion(ids_lists, k=k)

    by_id: dict[str, dict[str, Any]] = {}
    for _, hits in non_empty:
        for h in hits:
            did = h.get("doc_id")
            if did:
                by_id[str(did)] = dict(h)

    fused_order = sorted(rrf_scores.keys(), key=lambda d: rrf_scores[d], reverse=True)
    fused: list[dict[str, Any]] = []
    for doc_id in fused_order:
        item = by_id.get(doc_id)
        if not item:
            continue
        enriched = dict(item)
        enriched["score"] = round(
            rrf_scores[doc_id] * score_scale + float(enriched.get("score", 0.0)) * lexical_blend,
            4,
        )
        enriched["rrf_score"] = round(rrf_scores[doc_id], 6)
        fused.append(enriched)
        if len(fused) >= limit:
            break

    debug = {
        "mode": "rrf_" + "_".join(name for name, _ in non_empty),
        "lists": {name: len(hits) for name, hits in non_empty},
        "fused_count": len(fused),
    }
    return fused, debug
