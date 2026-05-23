# RAG Architecture (FastAPI — V2)

## Purpose

Mô tả kiến trúc dịch vụ **RAG + generation** (`backend/rag/`) và cách nó tích hợp với Node.

## Vai trò trong hệ thống

- **Retrieval:** BM25 (+ TF-IDF rerank; optional dense vector + RRF).
- **Generation:** Gemini (primary) hoặc template fallback.
- **Itinerary suggestions:** preview / options — **không** ghi DB app.
- **Contract:** Trả `rawPlaceId`, `place_key`, metadata; Node resolve sang `app_places.id`.

Boundary: [`BACKEND_RAG_BOUNDARY.md`](BACKEND_RAG_BOUNDARY.md).

## Layout thực tế (code)

```text
backend/rag/
  app/
    main.py                 # lifespan, middleware, /v1 mirror
    routers/                # rag, health, admin/*, ai_itinerary
    schemas/                # Pydantic request/response
    middleware.py           # internal API key, CORS, request ID
  services/
    rag_service.py          # delegate pipeline
    itinerary/              # preview, options, builder, scoring
    admin/                  # ops, data quality, log store
  pipelines/
    rag_pipeline.py         # orchestration (~130 lines)
    policies/               # LocationFilter, GenerationRouter
    response_builder.py
    request_logger.py
  retrieval/
    hybrid_retriever.py     # BM25 + optional vector
    bm25_retriever.py
    intent_parser.py
    fusion.py, rerank.py
    place_store.py          # app place snapshot (places_app.json)
    scoring/travel_rules.py
  generation/
    context_builder.py
    prompt_builder.py
  providers/                # gemini_provider, template_provider
  llm/                      # gemini client, executor, response_cache
  core/                     # config, security, artifacts, redis, metrics
  repositories/artifact_store.py
  domain/                   # shared models
  jobs/                     # build_rag_artifacts, package_rag_artifacts
  scripts/                  # verify, eval, fetch artifacts, entrypoint
  tests/                    # pytest + contracts parity Node
  data/
    indexes/                # manifest (git); bm25 pkl (gitignore)
    processed/              # corpus jsonl (gitignore)
    tests/fixtures/         # mini corpus CI
```

## Luồng request `/v1/rag/chat/simple`

1. Router validate body (`RagChatSimpleRequest`)
2. `RagService.rag_chat_simple` → threadpool
3. `RagPipeline.run`:
   - `IntentParser` → province/city/days
   - `HybridRetriever` → candidates
   - `LocationFilter` → lọc địa lý
   - `ContextBuilder` + `PromptBuilder`
   - `GenerationRouter` → Gemini hoặc template
   - `response_builder` → `answer`, `places[]`, `warnings`
4. Optional Redis cache (Gemini response)
5. JSON response — Node normalize qua `schemas/ragContract.js`

## Source of truth dữ liệu

| Layer | Vai trò |
|-------|---------|
| MySQL `rag_knowledge_base` | Canonical knowledge (export → corpus) |
| `places_rag_documents.jsonl` | Corpus file build index |
| `bm25_index.pkl` | Runtime retrieval artifact |
| `embedding_vectors.npz` | Optional dense recall |
| `rag_artifacts_manifest.json` | Checksum + document count (tracked git) |

Runtime **không** đọc MySQL trực tiếp cho retrieval — đọc artifacts trên disk (reproducible build).

Pipeline build:

```bash
cd backend/rag
python jobs/build_rag_artifacts.py --from-db --export-places
python scripts/verify_rag_artifacts.py --strict
```

Chi tiết: [`../../backend/rag/docs/ARTIFACT_POLICY.md`](../../backend/rag/docs/ARTIFACT_POLICY.md).

## HTTP surface

| Route | Caller | Ghi chú |
|-------|--------|---------|
| `POST /v1/rag/chat/simple` | Node (khuyến nghị) | Contract chính |
| `POST /rag/chat/simple` | Legacy mirror | Cùng handler |
| `POST /v1/ai/itinerary-preview` | Node | JWT qua Node |
| `POST /v1/ai/itinerary-options` | Node | JWT qua Node |
| `GET /health`, `/health/ready` | Compose, probes | Ready cần index |
| `/admin/*` | Node admin | `RAG_ADMIN_API_KEY` |

## Bảo mật & vận hành

- Production: `RAG_INTERNAL_API_KEY`, `RAG_ADMIN_API_KEY` (khác nhau).
- Rate limit: Redis hoặc in-memory (`RAG_RATE_LIMIT_PER_MINUTE`).
- Metrics: `/metrics` khi `RAG_ENABLE_METRICS=true`.
- Deploy: [`../../backend/rag/docs/DEPLOY_CHECKLIST.md`](../../backend/rag/docs/DEPLOY_CHECKLIST.md).

## Test & contract parity

- Fixture: [`fixtures/rag_chat_simple_sample.json`](fixtures/rag_chat_simple_sample.json)
- RAG: `tests/contracts/test_rag_node_fixture.py`
- Node: `tests/ragContractParity.test.js`

Chạy:

```bash
cd backend/rag && python -m pytest tests/contracts/ -q
cd backend/nodejs && npm test -- ragContract
```

## Hướng phát triển

- Deprecate routes không prefix `/v1` (giữ mirror đến khi Node/client cập nhật xong).
- Golden eval trên full production index (`eval/golden_queries.json`).
- Cross-encoder rerank optional (`requirements-rerank.txt`).
- DB-backed online retrieval — chỉ khi corpus > ~50k và artifact rebuild không đủ linh hoạt.
