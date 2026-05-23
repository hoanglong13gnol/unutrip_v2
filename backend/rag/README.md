# UnuTrip RAG service

FastAPI retrieval + generation API.

**Onboarding:** [`docs/v2/AGENT_GUIDE.md`](../../docs/v2/AGENT_GUIDE.md) · **Architecture:** [`docs/v2/RAG_ARCHITECTURE.md`](../../docs/v2/RAG_ARCHITECTURE.md)

## Layout

| Package | Role |
|---------|------|
| `app/routers/` | HTTP: `rag`, `health`, `admin/*`, `ai_itinerary` |
| `services/` | `RagService`, `ItineraryService`, `admin/*` |
| `pipelines/` | `RagPipeline`, policies, `response_builder` |
| `retrieval/` | BM25, hybrid, intent, fusion, rerank, `place_store` |
| `providers/` + `llm/` | Gemini + template + cache |
| `core/` | config, security, artifacts, redis, metrics |
| `jobs/` | `build_rag_artifacts`, `package_rag_artifacts` |
| `tests/` | pytest (~138) + `tests/contracts/` (Node parity) |

## Local setup

```bash
cd backend/rag
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -e ".[dev]"

# Index CI-sized (không cần MySQL)
python jobs/build_rag_artifacts.py --from-fixture
python scripts/verify_rag_artifacts.py

uvicorn app.main:app --reload --port 8001
# Docs: http://127.0.0.1:8001/docs
```

Editable install bắt buộc — không dùng `sys.path` hack.

## Production corpus (cần MySQL v2)

```bash
python jobs/build_rag_artifacts.py --from-db --export-places
python scripts/verify_rag_artifacts.py --strict
python jobs/package_rag_artifacts.py
```

Policy: [`docs/ARTIFACT_POLICY.md`](docs/ARTIFACT_POLICY.md) · Deploy: [`docs/DEPLOY_CHECKLIST.md`](docs/DEPLOY_CHECKLIST.md)

## Quality

```bash
make quality      # ruff + mypy + pytest (coverage ≥70%) + verify
make test-fast    # pytest không coverage
make clean
```

Contract parity với Node:

```bash
python -m pytest tests/contracts/ -q
# Fixture: docs/v2/fixtures/rag_chat_simple_sample.json
```

Eval retrieval (CI golden):

```bash
python scripts/eval_rag_retrieval.py --golden eval/golden_queries_ci.json --ci \
  --require-labels --min-province-accuracy 1.0 --min-hit-at5 0.75
```

## Integration

- Node gọi qua `RAG_BASE_URL` — path khuyến nghị `/v1/rag/chat/simple`
- Node **không** gọi Gemini trực tiếp; RAG đọc `GEMINI_API_KEY`
- Android **không** gọi RAG — chỉ Node `/api/ai/*`

Boundary: [`docs/v2/BACKEND_RAG_BOUNDARY.md`](../../docs/v2/BACKEND_RAG_BOUNDARY.md)

## Docs trong repo

| File | Nội dung |
|------|----------|
| [`docs/ARTIFACT_POLICY.md`](docs/ARTIFACT_POLICY.md) | Manifest, commit policy |
| [`docs/DEPLOY_CHECKLIST.md`](docs/DEPLOY_CHECKLIST.md) | Prod deploy |
| [`docs/RETRIEVAL.md`](docs/RETRIEVAL.md) | BM25 / TF-IDF / vector |
| [`docs/PRODUCTION.md`](docs/PRODUCTION.md) | Env prod |

CI: [`.github/workflows/rag-ci.yml`](../../.github/workflows/rag-ci.yml)

## Production env (tóm tắt)

```env
RAG_ENV=production
RAG_INTERNAL_API_KEY=...
RAG_ADMIN_API_KEY=...
RAG_DEBUG=false
RAG_LOG_JSON=true
RAG_ENABLE_METRICS=true
# Optional: RAG_ENABLE_VECTOR=true, RAG_ENABLE_RRF=true
```

Chi tiết: [`docs/PRODUCTION.md`](docs/PRODUCTION.md)
