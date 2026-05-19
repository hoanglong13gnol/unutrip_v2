"""Lazy-loaded sentence-transformers encoder for vector retrieval."""

from __future__ import annotations

import numpy as np

_ENCODER = None
_ENCODER_MODEL: str | None = None
_LOAD_FAILED = False


def load_encoder(model_name: str):
    global _ENCODER, _ENCODER_MODEL, _LOAD_FAILED

    if _LOAD_FAILED:
        raise RuntimeError(
            "Embedding model unavailable. Install: pip install -e \".[embeddings]\""
        )

    if _ENCODER is not None and _ENCODER_MODEL == model_name:
        return _ENCODER

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        _LOAD_FAILED = True
        raise RuntimeError(
            "Install optional embedding deps: pip install -e \".[embeddings]\""
        ) from exc

    _ENCODER = SentenceTransformer(model_name)
    _ENCODER_MODEL = model_name
    return _ENCODER


def encode_texts(
    texts: list[str],
    model_name: str,
    *,
    batch_size: int = 64,
    show_progress: bool = False,
) -> np.ndarray:
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)

    model = load_encoder(model_name)
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return np.asarray(vectors, dtype=np.float32)


def encode_query(query: str, model_name: str) -> np.ndarray:
    model = load_encoder(model_name)
    vec = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return np.asarray(vec[0], dtype=np.float32)
