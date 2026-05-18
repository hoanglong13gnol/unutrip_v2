"""Backward-compatible re-exports; canonical implementation in `core.text_normalization`."""

from core.text_normalization import normalize_text, remove_accents, tokenize_vi

__all__ = ["normalize_text", "remove_accents", "tokenize_vi"]
