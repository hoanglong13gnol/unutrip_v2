# UNUtrip v2 — Làm sạch & nâng cấp RAG (trạng thái cập nhật)

Tài liệu theo dõi refactor backend RAG (`backend/rag/`) và hygiene monorepo.  
Demo gốc `e:\UNUtrip` **không** bị sửa; mọi thay đổi trên tree v2 này.

---

## Đã làm (Phase 0 → 3)

### Phase 0 — Hygiene repo

| Hạng mục | Chi tiết |
|----------|----------|
| Git | Khởi tạo repo tại root (`git init`) |
| Dọn rác | Xóa `app/routers/_admin_extracted.txt`, `.pytest_cache/` |
| `.gitignore` | `__pycache__`, `.pytest_cache`, `node_modules`; **không** commit `bm25_index.pkl`, corpus JSONL (giữ `rag_artifacts_manifest.json`) |
| Verify artifacts | `scripts/verify_rag_artifacts.py` — resolve path đúng; BM25 checksum khi thiếu corpus → WARN + `--allow-missing` |
| CI RAG | Bỏ `\|\| true` trên verify; thêm bước pytest (sau này gộp thêm ruff ở Phase 3) |
| README root | Ghi rõ artifact track / rebuild |

### Phase 1 — Package Python chuẩn

| Hạng mục | Chi tiết |
|----------|----------|
| Layout | Xóa package `rag/` cũ → `retrieval/`, `generation/`, `pipelines/`, `domain/` |
| `pyproject.toml` | Editable install `unutrip-rag`, pytest `pythonpath` |
| `sys.path` | Gỡ khỏi `app/main.py` và `scripts/*` |
| `main.py` | `_mount_api_routes()` cho `/` và `/v1` |
| Schemas | `app/schemas/` (HTTP), `domain/models.py` + re-export `core/schemas.py` |
| Docker / CI | `pip install --no-deps -e .` |
| Docs | `backend/rag/README.md` |

### Phase 2 — Tách file lớn

| Hạng mục | Chi tiết |
|----------|----------|
| Admin | `app/routers/admin/` → `ai_monitoring`, `rag_ops`, `data_quality`, `system` |
| Services admin | `services/admin/` — log_store, rag_artifacts, data_quality_service, system_service |
| Itinerary | `app/routers/ai_itinerary.py` (mỏng) + `services/itinerary/*` + `app/schemas/itinerary.py` |
| Xóa | `app/routers/admin.py`, `app/ai_itinerary.py` |

### Phase 3 — Chất lượng & CI

| Hạng mục | Chi tiết |
|----------|----------|
| Test API | `tests/conftest.py` (mock pipeline), `tests/api/*` |
| Contract Node | `domain/contracts/rag_chat_simple.py` + `tests/contracts/` |
| Test khác | `tests/services/test_itinerary_service.py` — **31** pytest pass |
| Ruff | `requirements-dev.txt`, lint trong `rag-ci.yml` (line-length 120) |
| CI gộp | `backend-ci.yml` bỏ job `rag-tests` trùng; RAG chỉ qua `rag-ci.yml` |
| Eval | `--min-province-accuracy`, `--min-hit-at5` (khi có label) |

### Phase 4 — Dữ liệu reproducible

| Hạng mục | Chi tiết |
|----------|----------|
| Fixture CI | `tests/fixtures/rag_corpus_sample.jsonl`, `places_app_sample.json` |
| Build | `jobs/build_rag_artifacts.py --from-fixture` / `--from-db` + `--export-places` |
| Export DB | `export_rag_knowledge_base_to_corpus.py`, `export_app_places_to_json.py` |
| Verify strict | CI: `verify_rag_artifacts.py --strict` (không `--allow-missing`) |
| Golden CI | `eval/golden_queries_ci.json` + `hit@5` / province gates |
| Policy | `backend/rag/docs/ARTIFACT_POLICY.md` |
| Fix | `intent_parser`: alias `thua thien hue` → `thua_thien_hue` |

### Phase 5 — Retrieval nâng cao

| Hạng mục | Chi tiết |
|----------|----------|
| Rerank | `retrieval/rerank.py` — dense TF-IDF (default) + optional cross-encoder |
| Hybrid | `HybridRetriever` gọi rerank sau travel rules; debug `rerank_mode` |
| RRF | BM25 + char TF-IDF fusion (đã có, bật `RAG_ENABLE_RRF`) |
| Golden | `golden_queries_ci.json` 4 case có label; `--require-labels` trong eval |
| CI gate | `mean_hit@5 >= 0.75`, province `1.0` trên fixture |
| Tests | `test_rerank.py`, `test_retrieval_fixture.py` |
| Docs | `docs/RETRIEVAL.md`, `requirements-rerank.txt` (optional) |

### Phase 6 — Production hardening

| Hạng mục | Chi tiết |
|----------|----------|
| Secrets | `core/production.py` — bắt buộc prod: API keys, `RAG_DEBUG=false` |
| Node | `assertSafeProductionConfig()` — JWT mạnh, 2 RAG keys khác nhau |
| Ready | `core/readiness.py` — index + pipeline + prod config; Node gọi RAG `/health/ready` |
| Gemini | `llm/gemini_executor.py` — shared pool, không tạo executor/request |
| Metrics | `prometheus-client`, `GET /metrics` khi `RAG_ENABLE_METRICS=true` |
| Logs | JSON access logs + `request_id` / duration trên `rag.access` |
| Docs | `docs/PRODUCTION.md` |

### Phase 7 — Node / Android parity

| Hạng mục | Chi tiết |
|----------|----------|
| v2 tables | Node đọc `app_places` / `place_images`; reviews → `app_places` |
| Place ID | `placeIdMap.service.js` batch resolve + diagnostics |
| Flags | `USE_V2_PLACE_TABLES`, `PLACE_ID_LEGACY_FALLBACK` |
| Contract E2E | `docs/v2/fixtures/rag_chat_simple_sample.json` (Node Zod + RAG Pydantic) |
| Android | `androidDestinationContract.test.js` — khóa field DTO ổn định |
| Docs | `docs/v2/PHASE7_NODE_ANDROID_PARITY.md` |

---

## Phải làm (backlog ưu tiên)

### Dữ liệu & artifact (cao)

- [ ] Production corpus full: export DB → `places_rag_documents.jsonl` + cập nhật manifest checksum (local, không commit `.pkl`)
- [ ] Release asset / S3 / Git LFS nếu cần deploy artifact ngoài CI fixture
- [ ] `places_app_reviewed.json` (human review) — tùy chọn, ngoài export `app_places`

### Production (cao)

- [ ] Deploy checklist: set `RAG_ENV=production`, `NODE_ENV=production`, metrics scrape, artifact mount
- [ ] Alerting trên `/metrics` và 503 `/health/ready`

### Retrieval & chất lượng (trung bình)

- [ ] Golden production: gán `relevant_place_ids` trên full index (`golden_queries.json`)
- [ ] Bật cross-encoder prod (`RAG_ENABLE_CROSS_ENCODER`) sau khi cài `requirements-rerank.txt`
- [ ] Dense vector DB / embedding index riêng (ngoài char TF-IDF) nếu cần scale

### Code & kiến trúc (trung bình)

- [ ] Tách nhỏ `services/itinerary/category.py` (rule table / config)
- [ ] `core/` → `infrastructure/` (tùy chọn, align `docs/v2/RAG_ARCHITECTURE.md`)
- [ ] Deprecate route legacy không version (timeline `/v1` only)
- [ ] Bỏ flag chưa implement: `ENABLE_LORA`, `ENABLE_VALIDATOR` hoặc implement

### Monorepo & Android (thấp–trung bình)

- [ ] Push remote + branch protection + bắt buộc `rag-ci` / `backend-ci`
- [ ] Android polish (REFACTOR phase 8) sau khi staging E2E pass

---

## Làm tiếp theo (đề xuất thứ tự)

```text
Phase 8 — Android polish (sau khi API ổn định trên staging)
```

---

## Lệnh dev nhanh (RAG)

```bash
cd backend/rag
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
pip install --no-deps -e .

# Chạy API
uvicorn app.main:app --reload --port 8001

# Chất lượng (+ Phase 4 fixture pipeline)
ruff check app core domain generation llm pipelines retrieval services tests scripts
python -m pytest tests/ -q
python jobs/build_rag_artifacts.py --from-fixture
python scripts/verify_rag_artifacts.py
python scripts/eval_rag_retrieval.py --golden eval/golden_queries_ci.json --ci \
  --require-labels --min-province-accuracy 1.0 --min-hit-at5 0.75
```

---

## Commit Git (đã tạo trên `master`)

| # | SHA (rút gọn) | Message |
|---|---------------|---------|
| 1 | `dc6285c` | `chore(rag): phase 0 repo hygiene and artifact policy` |
| 2 | `b64420a` | `refactor(rag): phases 1-2 package layout and split routers` |
| 3 | `30ce73f` | `test(rag): phase 3 API tests, contracts, ruff and CI` |
| 4 | `41f1ae7` | `chore: add UNUtrip v2 monorepo scaffold and clean roadmap` |

Xem log: `git log --oneline -4`

---

## Tham chiếu

- Kiến trúc mục tiêu: `docs/v2/RAG_ARCHITECTURE.md`
- Ranh giới Node ↔ RAG: `docs/v2/BACKEND_RAG_BOUNDARY.md`
- Lộ trình DB/Android: `docs/v2/REFACTOR_PHASE_PLAN.md`
- Chạy stack: `README.md`, `docker-compose.yml`, `.env.example`
