"""VectorRetriever with synthetic embedding artifact."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pytest
from rank_bm25 import BM25Okapi

from core.config import settings
from retrieval.bm25_retriever import BM25Retriever
from retrieval.vector_retriever import EMBEDDING_INDEX_FILE, VectorRetriever


@pytest.fixture
def mini_vector_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(settings, "indexes_dir", tmp_path / "indexes")
    monkeypatch.setattr(settings, "processed_data_dir", tmp_path / "processed")
    settings.indexes_dir.mkdir(parents=True, exist_ok=True)

    docs = [
        {
            "doc_id": "d1",
            "doc_type": "place",
            "place_id": "P1",
            "title": "Bãi biển A",
            "text": "biển nắng",
            "metadata": {"province_norm": "khanh_hoa"},
        },
        {
            "doc_id": "d2",
            "doc_type": "place",
            "place_id": "P2",
            "title": "Núi B",
            "text": "leo núi",
            "metadata": {"province_norm": "lao_cai"},
        },
    ]
    tokenized = [[w for w in (d["title"] + " " + d["text"]).split()] for d in docs]
    bm25 = BM25Okapi(tokenized)
    bm25_path = settings.indexes_dir / "bm25_index.pkl"
    with bm25_path.open("wb") as f:
        pickle.dump(
            {"docs": docs, "tokenized_corpus": tokenized, "bm25": bm25},
            f,
        )

    # d1 ~ [1,0], d2 ~ [0,1]
    emb = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    emb_path = settings.indexes_dir / "embedding_vectors.npz"
    np.savez_compressed(emb_path, embeddings=emb, model_name=np.array("test-model"))

    return emb_path


def test_vector_search_filters_province(
    mini_vector_index: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "retrieval.vector_retriever.encode_query",
        lambda _q, _m: np.array([1.0, 0.0], dtype=np.float32),
    )
    bm25_path = settings.indexes_dir / "bm25_index.pkl"
    vr = VectorRetriever(
        index_file=mini_vector_index,
        bm25=BM25Retriever(index_file=bm25_path),
    )
    vr.load()
    hits = vr.search("bien", top_k=5, province_norm="khanh_hoa")
    assert len(hits) == 1
    assert hits[0]["doc_id"] == "d1"


def test_vector_index_exists() -> None:
    assert isinstance(VectorRetriever.index_exists(EMBEDDING_INDEX_FILE), bool)
