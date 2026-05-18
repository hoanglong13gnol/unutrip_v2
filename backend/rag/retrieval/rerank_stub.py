"""Backward-compatible re-exports; implementation lives in `retrieval.rerank`."""

from retrieval.rerank import cross_encoder_rerank, maybe_cross_encoder_rerank, rerank_candidates

__all__ = ["cross_encoder_rerank", "maybe_cross_encoder_rerank", "rerank_candidates"]
