# UnuTrip RAG service

FastAPI retrieval + generation API. Layout:

| Package | Role |
|---------|------|
| `app/routers/` | HTTP: `rag`, `health`, `admin/*`, `ai_itinerary` |
| `app/schemas/` | Request models (`rag`, `itinerary`) |
| `services/` | `RagService`, `ItineraryService`, `services/admin/*` |
| `pipelines/` | Orchestration (`RagPipeline`) |
| `retrieval/` | BM25, hybrid retrieval, intent, place store |
| `generation/` | Context + prompt builders |
| `llm/` | Gemini client + response cache |
| `core/` | Config, security, Redis, artifacts |
| `domain/` | Domain Pydantic models |

## Local setup

```bash
cd backend/rag
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt -r requirements-dev.txt
pip install --no-deps -e .
uvicorn app.main:app --reload --port 8001
```

Scripts and tests require editable install (`pip install -e .`) so imports resolve without `sys.path` hacks.

## Quality (Phase 3–5)

```bash
ruff check app core domain generation llm pipelines retrieval services tests scripts
python jobs/build_rag_artifacts.py --from-fixture
python -m pytest tests/ -q
python scripts/verify_rag_artifacts.py
python scripts/eval_rag_retrieval.py --golden eval/golden_queries_ci.json --ci \
  --require-labels --min-province-accuracy 1.0 --min-hit-at5 0.75
```

- `tests/api/` — FastAPI `TestClient` with mocked pipeline
- `tests/contracts/` — `/rag/chat/simple` shape aligned with Node `ragContract.js`
- `tests/fixtures/` — tracked mini corpus + `places_app` for CI builds
- `tests/test_retrieval_fixture.py` — hit@5 on fixture index (Phase 5)
- `retrieval/rerank.py` — dense TF-IDF rerank; optional cross-encoder via `requirements-rerank.txt`
- `docs/ARTIFACT_POLICY.md`, `docs/RETRIEVAL.md`, `docs/PRODUCTION.md`
- CI: `.github/workflows/rag-ci.yml` (build fixture → pytest → verify → eval)

## Production (Phase 6)

```bash
# Example production flags (see docs/PRODUCTION.md)
export RAG_ENV=production
export RAG_INTERNAL_API_KEY=...
export RAG_ADMIN_API_KEY=...
export RAG_DEBUG=false
export RAG_LOG_JSON=true
export RAG_ENABLE_METRICS=true
```
