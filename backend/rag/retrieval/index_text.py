"""Shared document text extraction for lexical + vector index builds."""

from __future__ import annotations

from retrieval.text_utils import tokenize_vi


def doc_full_text(doc: dict) -> tuple[list[str], str]:
    """Return (tokenized for BM25, raw string for TF-IDF / embeddings)."""
    title = doc.get("title") or ""
    text = doc.get("text") or ""
    doc_type = doc.get("doc_type") or ""
    metadata = doc.get("metadata") or {}

    metadata_text = " ".join(
        [
            str(metadata.get("province") or ""),
            str(metadata.get("city") or ""),
            str(metadata.get("area") or ""),
            str(metadata.get("category_main") or ""),
            str(metadata.get("category_sub") or ""),
            str(metadata.get("budget_level_norm") or ""),
            str(metadata.get("walking_level_norm") or ""),
            str(metadata.get("slot_norm") or ""),
            str(metadata.get("recommended_use_norm") or ""),
            str(doc_type),
        ]
    )

    full_text = f"{title}\n{text}\n{metadata_text}"
    tokens = tokenize_vi(full_text)
    return tokens, full_text
