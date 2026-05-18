# RAG artifact policy (Phase 4)

## What is tracked in git

| Path | In git? | Notes |
|------|---------|--------|
| `data/indexes/rag_artifacts_manifest.json` | Yes | Checksums + document count for last production build |
| `data/indexes/bm25_index.pkl` | No | Large binary; rebuild locally or in CI |
| `data/processed/places_rag_documents.jsonl` | No | Full corpus; export from DB |
| `data/processed/places_app.json` | No | Export from `app_places` |
| `tests/fixtures/rag_corpus_sample.jsonl` | Yes | Small reproducible corpus for CI |
| `tests/fixtures/places_app_sample.json` | Yes | Small PlaceStore snapshot for CI |

## Production build (local / release pipeline)

```bash
cd backend/rag
# Requires MySQL with v2 tables populated
python jobs/build_rag_artifacts.py --from-db --export-places
python scripts/verify_rag_artifacts.py
```

Steps:

1. `export_rag_knowledge_base_to_corpus.py` → `places_rag_documents.jsonl`
2. `export_app_places_to_json.py` → `places_app.json` (optional but recommended)
3. `06_build_bm25_index.py` → `bm25_index.pkl` + updates manifest checksums

Do **not** commit `.pkl` or full JSONL. Update the manifest only when you intentionally refresh production checksums after a local build.

## CI build (reproducible, no DB)

```bash
python jobs/build_rag_artifacts.py --from-fixture
python scripts/verify_rag_artifacts.py
python scripts/eval_rag_retrieval.py --golden eval/golden_queries_ci.json --ci \
  --min-province-accuracy 1.0 --min-hit-at5 0.5
```

CI copies tracked fixtures, builds a small BM25 index, and verifies manifest checksums in **strict** mode (no `--allow-missing`).

## Distribution options for full artifacts

1. **CI-only build** (current default) — developers without DB still get green CI via fixtures.
2. **Release asset / S3** — upload `bm25_index.pkl` + corpus from release job; download in deploy.
3. **Git LFS** — optional if team wants versioned binaries without bloating normal git objects.

## Health / readiness

`/health/ready` requires `bm25_index.pkl` on disk. In Docker, mount pre-built artifacts or run `build_rag_artifacts` in an init container.
