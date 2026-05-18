# RAG CI fixtures (Phase 4)

Tracked small datasets for reproducible CI builds (no DB, no 250MB+ `.pkl` in git).

| File | Role |
|------|------|
| `rag_corpus_sample.jsonl` | Corpus copied to `data/processed/places_rag_documents.jsonl` before BM25 build |
| `places_app_sample.json` | Copied to `data/processed/places_app.json` for PlaceStore / itinerary preview |

Build locally:

```bash
cd backend/rag
python jobs/build_rag_artifacts.py --from-fixture
python scripts/verify_rag_artifacts.py
python scripts/eval_rag_retrieval.py --golden eval/golden_queries_ci.json --ci --min-hit-at5 0.5 --min-province-accuracy 1.0
```

Production-sized artifacts: export from DB (`--from-db`) per `docs/ARTIFACT_POLICY.md`.
