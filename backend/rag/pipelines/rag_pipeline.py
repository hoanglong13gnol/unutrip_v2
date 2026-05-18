import logging
import time
from typing import Any

from core.config import settings
from generation.context_builder import ContextBuilder
from generation.prompt_builder import PromptBuilder
from llm.response_cache import ResponseCache
from pipelines.policies.generation_router import GenerationRouter
from pipelines.policies.location_filter import LocationFilter
from pipelines.request_logger import log_rag_request
from pipelines.response_builder import extract_places, extract_warnings
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.logger import AiRequestLogger
from retrieval.place_store import PlaceStore

logger = logging.getLogger(__name__)


class RagPipeline:
    def __init__(self) -> None:
        self.retriever = HybridRetriever()
        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()
        self.ai_logger = AiRequestLogger()
        self.response_cache = ResponseCache()
        self.place_store = PlaceStore()
        self.location_filter = LocationFilter(self.place_store)
        self.generation_router = GenerationRouter(response_cache=self.response_cache)

    def run(
        self,
        query: str,
        top_k: int = 6,
        mode: str = "balanced",
        include_prompt: bool = True,
        target_province=None,
        target_city=None,
    ) -> dict[str, Any]:
        started = time.perf_counter()

        parsed = self.retriever.intent_parser.parse(query)
        top_k_effective = top_k
        if parsed.intent == "itinerary":
            days = parsed.days or 1
            # Đủ địa điểm trong CONTEXT để ghép nhiều khung giờ/ngày (trần 12).
            top_k_effective = min(12, max(top_k, min(10, days * 3)))

        t0 = time.perf_counter()
        retrieved = self.retriever.retrieve(query, top_k=top_k_effective)
        retrieved = self.location_filter.apply(
            retrieved,
            query=query,
            target_province=target_province,
            target_city=target_city,
            top_k=top_k_effective,
        )
        retrieval_ms = (time.perf_counter() - t0) * 1000

        t1 = time.perf_counter()
        context = self.context_builder.build_context(retrieved, max_places=top_k_effective)
        context_ms = (time.perf_counter() - t1) * 1000

        t2 = time.perf_counter()
        prompt = self.prompt_builder.build_prompt(retrieved, context)
        prompt_ms = (time.perf_counter() - t2) * 1000

        place_ids_for_cache = [
            item.get("place_id")
            for item in retrieved.get("results", [])[:top_k_effective]
            if item.get("place_id")
        ]

        cache_key = self.response_cache.make_key(
            query=query,
            runtime_mode=settings.ai_runtime_mode,
            model_name=settings.gemini_model,
            place_ids=place_ids_for_cache,
        )

        generation_started = time.perf_counter()
        answer_payload = self.generation_router.generate(
            prompt=prompt,
            retrieved=retrieved,
            query=query,
            cache_key=cache_key,
        )
        generation_ms = (time.perf_counter() - generation_started) * 1000

        total_ms = (time.perf_counter() - started) * 1000

        response = {
            "answer": answer_payload["answer"],
            "rag_mode": mode,
            "runtime_mode": settings.ai_runtime_mode,
            "model_used": answer_payload["model_used"],
            "fallback_used": answer_payload.get("fallback_used", False),
            "places": extract_places(retrieved),
            "warnings": extract_warnings(retrieved),
            "latency_ms": {
                "retrieval": round(retrieval_ms, 2),
                "context": round(context_ms, 2),
                "prompt": round(prompt_ms, 2),
                "generation": round(generation_ms, 2),
                "gemini": answer_payload.get("gemini_latency_ms", 0),
                "total": round(total_ms, 2),
            },
            "debug": {
                "intent": retrieved.get("intent"),
                "retriever_debug": retrieved.get("debug"),
                "target_province": target_province,
                "target_city": target_city,
                "prompt_chars": len(prompt),
                "context_chars": len(context),
                "generation_error": answer_payload.get("error"),
                "generation_error_type": answer_payload.get("error_type"),
                "retry_after_seconds": answer_payload.get("retry_after_seconds"),
                "gemini_timeout": answer_payload.get("gemini_timeout", False),
                "cache_hit": answer_payload.get("cache_hit", False),
            },
        }

        if include_prompt:
            response["prompt"] = prompt
            response["context"] = context

        log_rag_request(self.ai_logger, query=query, response=response)

        return response
