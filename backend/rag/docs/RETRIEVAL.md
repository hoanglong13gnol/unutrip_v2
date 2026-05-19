# Retrieval pipeline (Phase 5)

## Stages

1. **Intent** — `IntentParser` (province, interests, constraints).
2. **Lexical + dense recall** — BM25 (+ optional RRF with char TF-IDF when `RAG_ENABLE_RRF=true`; + dense vectors when `RAG_ENABLE_VECTOR=true` and `embedding_vectors.npz` exists).
3. **Travel rules** — province / budget / elderly / interest boosts in `HybridRetriever`.
4. **Rerank** — second-stage rescore (`RAG_ENABLE_RERANK=true`, default):
   - **dense_tfidf** — cosine on in-index TF-IDF vectors (default, no extra packages).
   - **cross_encoder** — `sentence-transformers` when `RAG_ENABLE_CROSS_ENCODER=true`.

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `RAG_ENABLE_RRF` | `true` | Fuse BM25 + TF-IDF (+ vector when enabled) with RRF |
| `RAG_ENABLE_VECTOR` | `false` | Include sentence-transformer dense recall in RRF |
| `RAG_EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | HF model for index + query encoding |
| `RAG_VECTOR_TOP_K` | `120` | Candidate pool per channel before fusion |
| `RAG_ENABLE_RERANK` | `true` | Second-stage rerank |
| `RAG_ENABLE_CROSS_ENCODER` | `false` | Use cross-encoder instead of dense TF-IDF |
| `RAG_CROSS_ENCODER_MODEL` | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | HF model id |
| `RAG_RERANK_CANDIDATE_POOL` | `48` | Max candidates sent to reranker |

Optional install:

```bash
pip install -r requirements-rerank.txt
pip install -r requirements-embeddings.txt
```

Build vector index (after BM25):

```bash
python jobs/build_rag_artifacts.py --from-fixture --with-embeddings
# or: RAG_BUILD_EMBEDDINGS=true python jobs/build_rag_artifacts.py --from-db
```

## Evaluation

- **CI / fixture**: `eval/golden_queries_ci.json` — labeled `relevant_place_ids`, gates in `rag-ci.yml`.
- **Production smoke**: `eval/golden_queries.json` — province intent checks; add `relevant_place_ids` when labels exist.

```bash
python scripts/eval_rag_retrieval.py --golden eval/golden_queries_ci.json --ci \
  --require-labels --min-hit-at5 0.75 --min-province-accuracy 1.0
```

## Tests

- `tests/test_rerank.py` — rerank unit tests (mock TF-IDF).
- `tests/test_retrieval_fixture.py` — end-to-end on fixture index (`fixture_bm25_index` in `conftest.py`).
