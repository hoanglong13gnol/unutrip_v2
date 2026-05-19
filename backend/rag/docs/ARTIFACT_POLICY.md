# RAG artifact policy (Phase 4)

## What is tracked in git

| Path | In git? | Notes |
|------|---------|--------|
| `data/indexes/rag_artifacts_manifest.json` | Yes | Checksums + document count for last production build |
| `data/indexes/bm25_index.pkl` | No | Large binary; rebuild locally or in CI |
| `data/indexes/embedding_vectors.npz` | No | Dense vectors; `07_build_embedding_index.py` or `--with-embeddings` |
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
4. (Optional) `07_build_embedding_index.py` → `embedding_vectors.npz` + `embedding_sha256` in manifest

Do **not** commit `.pkl` or full JSONL. Update the manifest only when you intentionally refresh production checksums after a local build.

Manifest `corpus_path` / `bm25_index_path` must be **repo-relative** POSIX paths (e.g. `data/processed/places_rag_documents.jsonl`). CI rejects absolute Windows/Linux paths (`verify_rag_artifacts.py --strict`).

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
2. **Release zip + URL** (Phase D) — `python jobs/package_rag_artifacts.py` → upload zip; set `RAG_ARTIFACT_BUNDLE_URL` in deploy.
3. **Volume mount** — mount host dir with `processed/` + `indexes/` at `/svc/data` or set `RAG_ARTIFACT_SOURCE_DIR`.
4. **Git LFS** — optional if team wants versioned binaries without bloating normal git objects.

```bash
# After --from-db build + verify
python jobs/package_rag_artifacts.py -o dist/unutrip-rag-artifacts.zip
# Deploy: RAG_ARTIFACT_BUNDLE_URL=https://.../unutrip-rag-artifacts.zip
```

See `docs/DEPLOY_CHECKLIST.md` for production env vars and health probes.

## Health / readiness

`/health/ready` requires `bm25_index.pkl` on disk. In Docker, mount pre-built artifacts or run `build_rag_artifacts` in an init container.
