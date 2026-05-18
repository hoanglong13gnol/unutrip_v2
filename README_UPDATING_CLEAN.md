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

---

## Phải làm (backlog ưu tiên)

### Dữ liệu & artifact (cao)

- [ ] Tạo / commit pipeline corpus: `places_rag_documents.jsonl` (export DB hoặc Excel) rồi `jobs/build_rag_artifacts.py`
- [ ] Chính sách artifact rõ ràng: Git LFS, S3/release asset, hoặc **chỉ CI build** (không commit `.pkl` 250MB+)
- [ ] `places_app.json` / `places_app_reviewed.json` cho `PlaceStore` + itinerary preview khi không có DB

### Production (cao)

- [ ] Bắt buộc prod: `RAG_INTERNAL_API_KEY`, `RAG_ADMIN_API_KEY`, `RAG_DEBUG=false`, `JWT_SECRET` mạnh (Node)
- [ ] `/health/ready` phản ánh đúng policy (có index vs chỉ pipeline)
- [ ] Sửa `GeminiGenerator`: không tạo `ThreadPoolExecutor` mỗi request (pool dùng chung / async)

### Retrieval & chất lượng (trung bình)

- [ ] Golden set có `relevant_place_ids` + ngưỡng `hit@5` trong CI
- [ ] Fixture index nhỏ trong `tests/fixtures/` cho test retrieval không phụ thuộc `.pkl` production
- [ ] Rerank thật (cross-encoder) thay `rerank_stub.py`
- [ ] Vector / hybrid dense+sparse (nếu cần)

### Code & kiến trúc (trung bình)

- [ ] Tách nhỏ `services/itinerary/category.py` (rule table / config)
- [ ] `core/` → `infrastructure/` (tùy chọn, align `docs/v2/RAG_ARCHITECTURE.md`)
- [ ] Deprecate route legacy không version (timeline `/v1` only)
- [ ] Bỏ flag chưa implement: `ENABLE_LORA`, `ENABLE_VALIDATOR` hoặc implement

### Monorepo & Android (thấp–trung bình)

- [ ] Phase Node trong `docs/v2/REFACTOR_PHASE_PLAN.md` (repository layer, `place_id_map`, …)
- [ ] Đảm bảo `node_modules/` không lọt VCS; `npm ci` trong CI Node (đã có)
- [ ] Push remote + branch protection + bắt buộc `rag-ci` / `backend-ci`

---

## Làm tiếp theo (đề xuất thứ tự)

```text
Phase 4 — Dữ liệu reproducible
  → export corpus + build index + verify strict trong CI (fail nếu thiếu trên branch release)

Phase 5 — Retrieval nâng cao
  → golden labels, hit@5 gate, optional rerank / vector

Phase 6 — Production hardening
  → secrets, Gemini pool, metrics (Prometheus), structured logs

Phase 7 — Node / Android parity
  → theo REFACTOR_PHASE_PLAN.md (DB v2, contract E2E)
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

# Chất lượng
ruff check app core domain generation llm pipelines retrieval services tests scripts
python -m pytest tests/ -q
python scripts/verify_rag_artifacts.py --allow-missing
python scripts/eval_rag_retrieval.py --ci --min-province-accuracy 0.5
```

---

## Commit Git (phase 0–3)

| Commit | Message gợi ý |
|--------|----------------|
| 1 | `chore(rag): phase 0 repo hygiene and artifact policy` |
| 2 | `refactor(rag): phase 1 package layout and editable install` |
| 3 | `refactor(rag): phase 2 split admin and itinerary modules` |
| 4 | `test(rag): phase 3 API tests, contracts, ruff and CI` |

File monorepo còn lại (Android, Node, Docker, `docs/`) nằm commit khởi tạo hoặc commit riêng `chore: add UNUtrip v2 monorepo scaffold` tùy chiến lược team.

---

## Tham chiếu

- Kiến trúc mục tiêu: `docs/v2/RAG_ARCHITECTURE.md`
- Ranh giới Node ↔ RAG: `docs/v2/BACKEND_RAG_BOUNDARY.md`
- Lộ trình DB/Android: `docs/v2/REFACTOR_PHASE_PLAN.md`
- Chạy stack: `README.md`, `docker-compose.yml`, `.env.example`
