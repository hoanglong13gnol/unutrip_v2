from dataclasses import asdict
from typing import Any

from core.config import settings, vector_retrieval_active
from retrieval.bm25_retriever import BM25Retriever
from retrieval.intent_parser import IntentParser, ParsedIntent
from retrieval.recall_fusion import fuse_ranked_hit_lists
from retrieval.rerank import rerank_candidates
from retrieval.scoring.dedup import deduplicate_scored_results, is_near_duplicate_name, name_dedup_key
from retrieval.scoring.travel_rules import TravelRuleScorer
from retrieval.vector_retriever import VectorRetriever


class HybridRetriever:
    def __init__(self) -> None:
        self._last_fusion_debug: dict[str, Any] = {}
        self.intent_parser = IntentParser()
        self.bm25 = BM25Retriever()
        self.bm25.load()
        self.vector = VectorRetriever(bm25=self.bm25)
        self._vector_active = vector_retrieval_active() and self.vector.try_load()
        self._rule_scorer = TravelRuleScorer()

    def retrieve(
        self,
        query: str,
        top_k: int = 8,
        *,
        province_norm_override: str | None = None,
    ) -> dict[str, Any]:
        intent = self.intent_parser.parse(query)
        province_norm = province_norm_override or intent.province_norm

        raw_results = self._recall_candidates(
            query=query,
            intent=intent,
            province_norm=province_norm,
        )

        scored = []
        for item in raw_results:
            rerank_score, reasons = self._rule_scorer.score(item, intent)
            final_score = float(item["score"]) + rerank_score

            enriched = dict(item)
            enriched["bm25_score"] = item.get("bm25_score", item["score"])
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
                "vector_active": self._vector_active,
                "rerank_mode": rerank_mode,
            },
        }

    def _recall_candidates(
        self,
        query: str,
        intent: ParsedIntent,
        *,
        province_norm: str | None = None,
    ) -> list[dict[str, Any]]:
        pool_k = settings.vector_candidate_top_k
        province_filter = province_norm if province_norm is not None else intent.province_norm

        bm25_hits = self.bm25.search(
            query=query,
            top_k=pool_k,
            doc_types=intent.preferred_doc_types,
            province_norm=province_filter,
        )
        for h in bm25_hits:
            h["bm25_score"] = h["score"]

        ranked_lists: list[tuple[str, list[dict[str, Any]]]] = [("bm25", bm25_hits)]

        use_rrf = settings.enable_rrf_fusion and self.bm25.has_tfidf()
        if use_rrf:
            tfidf_hits = self.bm25.search_tfidf(
                query=query,
                top_k=pool_k,
                doc_types=intent.preferred_doc_types,
                province_norm=province_filter,
            )
            if tfidf_hits:
                ranked_lists.append(("tfidf", tfidf_hits))

        if self._vector_active:
            vector_hits = self.vector.search(
                query=query,
                top_k=pool_k,
                doc_types=intent.preferred_doc_types,
                province_norm=province_filter,
            )
            if vector_hits:
                ranked_lists.append(("vector", vector_hits))

        if len(ranked_lists) == 1:
            self._last_fusion_debug = {
                "mode": "bm25_only",
                "vector_active": self._vector_active,
            }
            return bm25_hits

        fused, debug = fuse_ranked_hit_lists(
            ranked_lists,
            k=settings.rrf_k,
            limit=pool_k,
        )
        debug["vector_active"] = self._vector_active
        self._last_fusion_debug = debug
        return fused

    def _name_dedup_key(self, title: str | None) -> str:
        return name_dedup_key(title)

    def _is_near_duplicate_name(self, a: str | None, b: str | None) -> bool:
        return is_near_duplicate_name(a, b)

    def _travel_rule_score(self, item: dict[str, Any], intent: ParsedIntent) -> tuple[float, list[str]]:
        return self._rule_scorer.score(item, intent)
