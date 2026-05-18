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

## Quality (Phase 3)

```bash
ruff check app core domain generation llm pipelines retrieval services tests scripts
python -m pytest tests/ -q
python scripts/eval_rag_retrieval.py --ci --min-province-accuracy 0.5
```

- `tests/api/` — FastAPI `TestClient` with mocked pipeline
- `tests/contracts/` — `/rag/chat/simple` shape aligned with Node `ragContract.js`
- `domain/contracts/` — Pydantic validators reused in tests
- CI: `.github/workflows/rag-ci.yml` (lint + pytest + eval); Node-only checks in `backend-ci.yml`
