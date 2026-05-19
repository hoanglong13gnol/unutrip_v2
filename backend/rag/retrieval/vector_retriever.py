"""Dense vector retrieval over precomputed document embeddings (artifact npz)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from core.config import settings
from retrieval.bm25_retriever import BM25Retriever
from retrieval.embedding_encoder import encode_query

EMBEDDING_INDEX_FILE = settings.indexes_dir / "embedding_vectors.npz"


class VectorRetriever:
    """Cosine search on L2-normalized embedding matrix aligned with BM25 doc order."""

    def __init__(
        self,
        index_file: Path = EMBEDDING_INDEX_FILE,
        *,
        bm25: BM25Retriever | None = None,
    ) -> None:
        self.index_file = index_file
        self._bm25 = bm25 or BM25Retriever()
        self.embeddings: np.ndarray | None = None
        self.model_name: str | None = None
        self.embedding_dim: int = 0

    @classmethod
    def index_exists(cls, index_file: Path = EMBEDDING_INDEX_FILE) -> bool:
        return index_file.is_file()

    def try_load(self) -> bool:
        if not self.index_file.exists():
            return False
        try:
            self.load()
            return True
        except Exception:
            return False

    def load(self) -> None:
        if self._bm25.bm25 is None:
            self._bm25.load()

        with np.load(self.index_file, allow_pickle=False) as data:
            matrix = np.asarray(data["embeddings"], dtype=np.float32)
            self.model_name = str(data["model_name"])
            self.embedding_dim = int(matrix.shape[1]) if matrix.ndim == 2 else 0

        if matrix.shape[0] != len(self._bm25.docs):
            raise ValueError(
                f"Embedding rows ({matrix.shape[0]}) != BM25 docs ({len(self._bm25.docs)})"
            )

        self.embeddings = matrix

    def is_ready(self) -> bool:
        return self.embeddings is not None and self.model_name is not None

    def search(
        self,
        query: str,
        top_k: int = 10,
        doc_types: list[str] | None = None,
        province_norm: str | None = None,
    ) -> list[dict[str, Any]]:
        if not self.is_ready():
            if not self.try_load():
                return []

        assert self.embeddings is not None
        assert self.model_name is not None

        model_name = settings.embedding_model or self.model_name
        try:
            query_vec = encode_query(query, model_name)
        except RuntimeError:
            return []
        if query_vec.shape[0] != self.embeddings.shape[1]:
            return []

        scores = self.embeddings @ query_vec
        ranked_indices = np.argsort(scores)[::-1]

        results: list[dict[str, Any]] = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score <= 0:
                break

            doc = self._bm25.docs[int(idx)]
            metadata = doc.get("metadata") or {}

            if doc_types and doc.get("doc_type") not in doc_types:
                continue

            if province_norm and metadata.get("province_norm") != province_norm:
                continue

            results.append(
                {
                    "score": round(score, 6),
                    "doc_id": doc.get("doc_id"),
                    "doc_type": doc.get("doc_type"),
                    "place_id": doc.get("place_id"),
                    "title": doc.get("title"),
                    "text": doc.get("text"),
                    "metadata": metadata,
                }
            )

            if len(results) >= top_k:
                break

        return results
