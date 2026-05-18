from dataclasses import asdict
from typing import Any

from core.config import settings
from retrieval.bm25_retriever import BM25Retriever
from retrieval.fusion import reciprocal_rank_fusion
from retrieval.intent_parser import IntentParser, ParsedIntent
from retrieval.rerank import rerank_candidates
from retrieval.scoring.dedup import deduplicate_scored_results, is_near_duplicate_name, name_dedup_key
from retrieval.scoring.travel_rules import TravelRuleScorer


class HybridRetriever:
    def __init__(self) -> None:
        self._last_fusion_debug: dict[str, Any] = {}
        self.intent_parser = IntentParser()
        self.bm25 = BM25Retriever()
        self.bm25.load()
        self._rule_scorer = TravelRuleScorer()

    def retrieve(self, query: str, top_k: int = 8) -> dict[str, Any]:
        intent = self.intent_parser.parse(query)

        raw_results = self._lexical_candidates(
            query=query,
            intent=intent,
        )

        scored = []
        for item in raw_results:
            rerank_score, reasons = self._rule_scorer.score(item, intent)
            final_score = float(item["score"]) + rerank_score

            enriched = dict(item)
            enriched["bm25_score"] = item["score"]
            enriched["rule_score"] = round(rerank_score, 4)
            enriched["final_score"] = round(final_score, 4)
            enriched["reasons"] = reasons

            scored.append(enriched)

        rerank_k = max(top_k * 2, 16)
        scored, rerank_mode = rerank_candidates(
            query,
            scored,
            retriever=self.bm25,
            top_k=rerank_k,
        )

        scored.sort(key=lambda x: x["final_score"], reverse=True)
        deduped = deduplicate_scored_results(scored, top_k)

        return {
            "query": query,
            "intent": asdict(intent),
            "results": deduped,
            "debug": {
                "raw_count": len(raw_results),
                "scored_count": len(scored),
                "final_count": len(deduped),
                "fusion": self._last_fusion_debug,
                "rerank_mode": rerank_mode,
            },
        }

    def _lexical_candidates(self, query: str, intent: ParsedIntent) -> list[dict[str, Any]]:
        self._last_fusion_debug = {"mode": "bm25_only"}

        bm25_hits = self.bm25.search(
            query=query,
            top_k=120,
            doc_types=intent.preferred_doc_types,
            province_norm=intent.province_norm,
        )

        use_rrf = (
            settings.enable_rrf_fusion
            and self.bm25.has_tfidf()
        )

        if not use_rrf:
            return bm25_hits

        tfidf_hits = self.bm25.search_tfidf(
            query=query,
            top_k=120,
            doc_types=intent.preferred_doc_types,
            province_norm=intent.province_norm,
        )

        if not tfidf_hits:
            self._last_fusion_debug = {"mode": "bm25_only", "reason": "tfidf_empty"}
            return bm25_hits

        bm25_ids = [str(h["doc_id"]) for h in bm25_hits if h.get("doc_id")]
        tfidf_ids = [str(h["doc_id"]) for h in tfidf_hits if h.get("doc_id")]
        rrf_scores = reciprocal_rank_fusion([bm25_ids, tfidf_ids], k=60.0)

        by_id: dict[str, dict[str, Any]] = {}
        for h in bm25_hits:
            did = h.get("doc_id")
            if did:
                by_id[str(did)] = dict(h)

        for h in tfidf_hits:
            did = h.get("doc_id")
            if did and str(did) not in by_id:
                by_id[str(did)] = dict(h)

        fused_order = sorted(rrf_scores.keys(), key=lambda d: rrf_scores[d], reverse=True)

        fused: list[dict[str, Any]] = []
        for doc_id in fused_order:
            item = by_id.get(doc_id)
            if not item:
                continue
            enriched = dict(item)
            enriched["score"] = round(rrf_scores[doc_id] * 400.0 + float(enriched.get("score", 0.0)) * 0.01, 4)
            enriched["rrf_score"] = round(rrf_scores[doc_id], 6)
            fused.append(enriched)
            if len(fused) >= 120:
                break

        self._last_fusion_debug = {
            "mode": "rrf_bm25_tfidf",
            "bm25_count": len(bm25_hits),
            "tfidf_count": len(tfidf_hits),
            "fused_count": len(fused),
        }
        return fused

    # Backward-compatible helpers for tests or admin tooling.
    def _name_dedup_key(self, title: str | None) -> str:
        return name_dedup_key(title)

    def _is_near_duplicate_name(self, a: str | None, b: str | None) -> bool:
        return is_near_duplicate_name(a, b)

    def _travel_rule_score(self, item: dict[str, Any], intent: ParsedIntent) -> tuple[float, list[str]]:
        return self._rule_scorer.score(item, intent)
