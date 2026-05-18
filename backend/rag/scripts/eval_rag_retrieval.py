"""
Offline retrieval evaluation: hit@k on place_id labels + MRR + optional intent/province checks.

Usage:
  python scripts/eval_rag_retrieval.py
  python scripts/eval_rag_retrieval.py --golden eval/custom.json
  python scripts/eval_rag_retrieval.py --ci   # exit 0 if index missing; else run checks
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.config import settings
from retrieval.hybrid_retriever import HybridRetriever

ROOT = Path(__file__).resolve().parents[1]


def hit_at_k(relevant: set[str], ranked_ids: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    top = ranked_ids[:k]
    return 1.0 if any(rid in relevant for rid in top) else 0.0


def mrr(relevant: set[str], ranked_ids: list[str]) -> float:
    if not relevant:
        return 0.0
    for i, rid in enumerate(ranked_ids, start=1):
        if rid in relevant:
            return 1.0 / float(i)
    return 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", type=Path, default=ROOT / "eval" / "golden_queries.json")
    ap.add_argument("--ci", action="store_true")
    ap.add_argument(
        "--min-hit-at5",
        type=float,
        default=0.0,
        help="CI: fail if mean_hit@5 below threshold (only when labeled cases exist)",
    )
    ap.add_argument(
        "--min-province-accuracy",
        type=float,
        default=0.5,
        help="CI: fail if province_norm_accuracy below threshold",
    )
    ap.add_argument(
        "--require-labels",
        action="store_true",
        help="CI: fail when no case has relevant_place_ids",
    )
    args = ap.parse_args()

    bm25 = ROOT / "data" / "indexes" / "bm25_index.pkl"
    if not bm25.exists():
        print("SKIP: no BM25 index (build artifacts first)")
        sys.exit(0 if args.ci else 1)

    cases = json.loads(args.golden.read_text(encoding="utf-8"))
    retriever = HybridRetriever()

    print(
        "retrieval_config:",
        f"rrf={settings.enable_rrf_fusion}",
        f"rerank={settings.enable_rerank}",
        f"cross_encoder={settings.enable_cross_encoder}",
    )

    hit_scores: list[float] = []
    mrr_scores: list[float] = []
    prov_hits = 0
    prov_total = 0
    rerank_mode: str | None = None

    for row in cases:
        q = row["query"]
        rel = {str(x) for x in (row.get("relevant_place_ids") or []) if x}
        top_k = int(row.get("top_k", 8))
        out = retriever.retrieve(q, top_k=top_k)
        ranked = [str(x.get("place_id")) for x in out.get("results", []) if x.get("place_id")]
        if rerank_mode is None:
            rerank_mode = (out.get("debug") or {}).get("rerank_mode")

        if rel:
            hit_scores.append(hit_at_k(rel, ranked, min(5, top_k)))
            mrr_scores.append(mrr(rel, ranked))

        exp = row.get("expect_province_norm")
        if exp:
            prov_total += 1
            intent = (out.get("intent") or {}).get("province_norm")
            if intent == exp:
                prov_hits += 1

    if rerank_mode:
        print(f"rerank_mode: {rerank_mode}")

    labeled = sum(1 for row in cases if row.get("relevant_place_ids"))
    if args.require_labels and labeled == 0:
        print("CI FAIL: --require-labels but golden set has no relevant_place_ids")
        sys.exit(1)

    mean_hit5: float | None = None
    if hit_scores:
        mean_hit5 = sum(hit_scores) / len(hit_scores)
        print(f"mean_hit@5: {mean_hit5:.4f} (n={len(hit_scores)})")
    else:
        print("mean_hit@5: n/a (no labeled relevant_place_ids in golden set)")

    if mrr_scores:
        print(f"mean_mrr: {sum(mrr_scores) / len(mrr_scores):.4f} (n={len(mrr_scores)})")
    else:
        print("mean_mrr: n/a (no labeled relevant_place_ids in golden set)")

    if prov_total:
        acc = prov_hits / prov_total
        print(f"province_norm_accuracy: {acc:.4f} ({prov_hits}/{prov_total})")
        if args.ci and acc < args.min_province_accuracy:
            print(f"CI FAIL: province_norm_accuracy below {args.min_province_accuracy}")
            sys.exit(1)

    if args.ci and mean_hit5 is not None and args.min_hit_at5 > 0 and mean_hit5 < args.min_hit_at5:
        print(f"CI FAIL: mean_hit@5 {mean_hit5:.4f} below {args.min_hit_at5}")
        sys.exit(1)

    print("eval_ok")


if __name__ == "__main__":
    main()
