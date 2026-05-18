# Hướng dẫn Agent — UNUtrip v2

Tài liệu **bàn giao** cho agent / dev mới: đã làm gì, còn gì, chạy thế nào, tránh lỗi gì.  
Repo: `UNUtrip_v2` (tách từ demo `e:\UNUtrip` — **không sửa** demo gốc).

**Cập nhật:** sau P0–P3b + Phase D (một phần). Chi tiết lịch sử commit: `README_UPDATING_CLEAN_v2.md`.

---

## 1. Mục tiêu hệ thống

| Thành phần | Vai trò |
|------------|---------|
| `app/` | Android — gọi **Node**, không gọi RAG trực tiếp |
| `backend/nodejs/` | Express API, JWT, MySQL, proxy RAG, `place_id_map` |
| `backend/rag/` | FastAPI: BM25/hybrid retrieval + Gemini/template generation |
| `database/migrations/` | Schema v2 (`app_places`, `rag_knowledge_base`, …) |
| `docker-compose.yml` | MySQL + Redis + RAG + Node + `db-migrate` |

**Luồng RAG:** Android → Node (`/api/ai/rag-chat`) → RAG (`/v1/rag/chat/simple`) → artifact BM25 trên disk.

**Boundary:** `docs/v2/BACKEND_RAG_BOUNDARY.md` — Node persist, RAG không ghi DB app.

---

## 2. Cấu trúc RAG (đọc trước khi sửa)

```text
backend/rag/
  app/routers/          # HTTP only — rag, health, admin, ai_itinerary
  services/             # RagService, ItineraryService, admin/*
  pipelines/
    rag_pipeline.py     # Orchestration (~130 dòng) — KHÔNG nhét logic retrieval vào đây
    policies/           # location_filter, generation_router
    response_builder.py, request_logger.py
  providers/            # gemini_provider, template_provider (wrap llm/)
  retrieval/            # bm25, hybrid, intent, fusion, rerank, place_store
  retrieval/scoring/    # travel_rules, dedup
  generation/           # context + prompt builders
  llm/                  # Gemini client, executor, cache
  repositories/         # artifact_store (fetch/package runtime files)
  core/                 # config, security, artifacts, metrics, readiness
  domain/               # models, contracts (Node parity)
  jobs/                 # build_rag_artifacts, package_rag_artifacts
  scripts/              # verify, eval, fetch artifacts, docker entrypoint
  tests/                # pytest — 110 tests, coverage gate 70%
```

**Quy tắc khi refactor:**

- Logic retrieval → `retrieval/` hoặc `retrieval/scoring/`
- Policy (fallback, location) → `pipelines/policies/`
- Provider SDK → `providers/` + `llm/`
- Không thêm `sys.path` hack — dùng `pip install -e ".[dev]"`

---

## 3. Đã làm (bắt buộc hiểu — đừng làm lại / đừng phá)

### 3.1 Kiến trúc & làm sạch (Phase A–B)

- [x] Xóa dead code: `retrieval/normalizer.py`, `rerank_stub.py`
- [x] Chuẩn hóa text: `core/text_normalization.py`
- [x] Tách pipeline: policies, providers, response_builder, request_logger
- [x] `LocationFilter` + `target_city` / `target_province` có test

### 3.2 Chất lượệ & CI (Phase C, P2–P3)

- [x] **110** pytest RAG, coverage **~79%**, gate **≥70%** (`pyproject.toml`)
- [x] Ruff + mypy: `core`, `domain`, `generation`, `providers`, `pipelines`, `repositories`, `retrieval.scoring`
- [x] CI `rag-ci.yml`: lint, mypy, pytest, Docker RAG, verify manifest, golden eval
- [x] CI `backend-ci.yml`: **chỉ** Node + `database/` (không trigger trùng khi sửa RAG)
- [x] Docker build Node trong backend-ci
- [x] Workflow manual: `rag-artifact-release.yml` (zip fixture)

### 3.3 Coverage đã mở (P3, P3b)

- [x] Test unit: `rag_pipeline`, `request_logger`, retrieval (`place_store`, `bm25`, `hybrid`, `logger`, `rerank`)
- [x] Bỏ omit: hầu hết `retrieval/*`, `pipelines/rag_pipeline`, `intent_parser`
- [x] Vẫn **omit** (cố ý): `services/admin/*`, `services/itinerary/builder|catalog|scoring`

### 3.4 Artifact & deploy (P0, Phase D)

- [x] Manifest path **relative** (`data/processed/...`) — CI `--strict` từ chối path tuyệt đối
- [x] `repositories/artifact_store.py`, `fetch_rag_artifacts.py`, `package_rag_artifacts.py`
- [x] Docker `entrypoint` fetch khi `RAG_ARTIFACT_BUNDLE_URL` / `RAG_ARTIFACT_SOURCE_DIR`
- [x] Docs: `ARTIFACT_POLICY.md`, `DEPLOY_CHECKLIST.md`, `deploy/prometheus/unutrip-rag-alerts.yml`

### 3.5 Database v2 (P1)

- [x] `database/migrations/` = canonical schema
- [x] `database/scripts/run_migrations.sh` + Compose service `db-migrate`
- [x] `database.sql` deprecated — chỉ bootstrap DB trống
- [x] Compose: `USE_V2_PLACE_TABLES=true`, `PLACE_ID_LEGACY_FALLBACK=false` trên backend

### 3.6 Node / contract

- [x] Destinations API đọc `app_places`
- [x] `placeIdMap.repository` + flags v2 (`USE_V2_PLACE_TABLES`)
- [x] Contract tests: `tests/contracts/`, Node `ragContract*.test.js`

### 3.7 Hygiene repo (P0)

- [x] `.gitignore`: cache Python, `.coverage`, `data/raw/`, uploads Node, `dist/`

---

## 4. Chưa làm / cần làm (ưu tiên cho agent tiếp theo)

### P0 — Không được regression

- [ ] Sau test local: **không commit** thay đổi `built_at_utc` trong manifest nếu chỉ chạy pytest/build fixture (checksum giữ nguyên thì restore file)
- [ ] Không commit `.pkl`, JSONL lớn, `.env`, `__pycache__`

### Cao — Production

| # | Task | Gợi ý |
|---|------|--------|
| 1 | Build corpus production | `cd backend/rag && python jobs/build_rag_artifacts.py --from-db --export-places` (cần MySQL + `rag_knowledge_base`) |
| 2 | Upload bundle | `python jobs/package_rag_artifacts.py` → S3/Release → `RAG_ARTIFACT_BUNDLE_URL` |
| 3 | Staging E2E | `docker compose up -d` + mount artifact hoặc bundle URL; `bash scripts/smoke_staging_e2e.sh` |
| 4 | Branch protection | GitHub: bắt buộc `RAG service` + `Backend CI` trên `main` |

### Trung bình — Chất lượng

| # | Task | Gợi ý |
|---|------|--------|
| 5 | `travel_rules.py` coverage | Mở rộng `tests/retrieval/test_travel_rules_golden.py` |
| 6 | Mypy full `retrieval/`, `app/` | Sửa sklearn stubs / type hints; cập nhật `rag-ci.yml` |
| 7 | Bỏ omit admin/itinerary | Test từng service hoặc giữ omit có comment |
| 8 | Golden full index | `eval/golden_queries.json` trên index production |
| 9 | Cross-encoder prod | `pip install -e ".[rerank]"`, `RAG_ENABLE_CROSS_ENCODER=true` |

### Thấp — Sản phẩm / legacy

| # | Task |
|---|------|
| 10 | Deprecate route không `/v1` |
| 11 | `ENABLE_LORA` / `ENABLE_VALIDATOR`: implement hoặc xóa flag |
| 12 | Tách `services/itinerary/category.py` ra config |
| 13 | Phase 8 Android: test ViewModel, `RagService` |
| 14 | `USE_V2_PLACE_TABLES=true` mặc định local sau khi team bỏ XAMPP legacy |

---

## 5. Lệnh thường dùng

### RAG (luôn từ `backend/rag`)

```bash
cd backend/rag
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"

make quality          # ruff + mypy + pytest + verify manifest
make test-fast        # pytest không coverage
make clean            # xóa cache dev

python jobs/build_rag_artifacts.py --from-fixture   # CI / không DB
python jobs/build_rag_artifacts.py --from-db --export-places   # production

uvicorn app.main:app --reload --port 8001
```

### Monorepo / stack

```bash
cp .env.example .env
docker compose up -d --build

# Smoke (stack đang chạy)
export RAG_INTERNAL_API_KEY=...
bash scripts/smoke_staging_e2e.sh
```

### Node

```bash
cd backend/nodejs
npm ci
npm test
npm run lint
```

### Database

```bash
export MYSQL_HOST=127.0.0.1 MYSQL_USER=... MYSQL_PASSWORD=... DB_NAME=unudata
bash database/scripts/run_migrations.sh
```

---

## 6. CI — workflow map

| File | Khi nào chạy | Làm gì |
|------|----------------|--------|
| `.github/workflows/rag-ci.yml` | `backend/rag/**` | Ruff, mypy, pytest 70%, Docker RAG, verify, eval golden CI |
| `.github/workflows/backend-ci.yml` | `backend/nodejs/**`, `database/**` | ESLint, Prettier, Vitest, Docker Node, `bash -n` migrations |
| `.github/workflows/rag-artifact-release.yml` | Manual | Package zip fixture → artifact |
| `.github/workflows/android-ci.yml` | `app/**` | Unit test + lint + assemble devDebug |

**Local = CI RAG:**

```bash
cd backend/rag
ruff check app core domain generation llm pipelines providers repositories retrieval services tests scripts jobs
python -m mypy --explicit-package-bases -p core -p domain -p generation -p providers -p pipelines -p repositories -p retrieval.scoring
python jobs/build_rag_artifacts.py --from-fixture
python -m pytest tests/ -q
python scripts/verify_rag_artifacts.py --strict
```

---

## 7. Pitfalls (đọc kỹ)

| Vấn đề | Cách tránh |
|--------|------------|
| Manifest path Windows tuyệt đối | `write_manifest` dùng `artifact_path_for_manifest()` — CI strict sẽ fail |
| Test ghi đè manifest | Monkeypatch `settings.root_dir` / `indexes_dir`; không gọi `write_manifest` trỏ ra temp ngoài svc root |
| RAG `/health/ready` 503 | Thiếu `bm25_index.pkl` — build fixture hoặc fetch bundle |
| Compose DB trống | Cần `db-migrate` hoặc `DATABASE_BOOTSTRAP_LEGACY=true` |
| Place id không map | Kiểm tra `place_id_map`, `USE_V2_PLACE_TABLES`, legacy fallback |
| sklearn version | Phải `scikit-learn==1.7.1` (pickle index) |
| Commit secrets | Chỉ `.env.example` — không `.env` |

---

## 8. Checklist trước khi PR (agent)

1. [ ] `cd backend/rag && make quality` (hoặc từng bước nếu chậm)
2. [ ] `cd backend/nodejs && npm test` (nếu đụng Node/contract)
3. [ ] Không file nhạy cảm / artifact lớn trong `git status`
4. [ ] Manifest chỉ đổi khi **cố ý** rebuild production
5. [ ] Cập nhật doc nếu đổi env, API, migration, artifact policy
6. [ ] Commit message: `feat|fix|chore|test(rag|node): ...` — một mục đích rõ

**Không** tự `git push` / tạo PR trừ khi user yêu cầu.

---

## 9. Tài liệu tham chiếu

| File | Nội dung |
|------|----------|
| `README.md` | Tổng quan monorepo |
| `README_UPDATING_CLEAN_v2.md` | Roadmap chi tiết Phase A–E, P0–P3 |
| `README_UPDATING_CLEAN.md` | Lịch sử Phase 0–7 |
| `docs/v2/RAG_ARCHITECTURE.md` | Kiến trúc mục tiêu |
| `docs/v2/BACKEND_RAG_BOUNDARY.md` | Ranh giới Node ↔ RAG |
| `docs/v2/PHASE7_NODE_ANDROID_PARITY.md` | Place tables, flags |
| `backend/rag/README.md` | Setup RAG |
| `backend/rag/docs/ARTIFACT_POLICY.md` | Manifest / rebuild |
| `backend/rag/docs/DEPLOY_CHECKLIST.md` | Prod deploy |
| `database/README.md` | Migrations |
| `deploy/prometheus/README.md` | Alerting |

---

## 10. Gợi ý task cho agent mới (pick one)

1. **Prod artifact:** build `--from-db`, upload zip, doc URL staging.  
2. **travel_rules:** thêm golden tests, tăng coverage >70% file.  
3. **Mypy `app/`:** type routers + deps, sửa CI.  
4. **Android Phase 8:** test `ChatbotViewModel` / `RagService` errors.  
5. **Deprecate legacy routes:** `/rag/*` → chỉ `/v1`, cập nhật Node client nếu cần.

Khi xong task, cập nhật mục **§4** và **§3** trong file này hoặc `README_UPDATING_CLEAN_v2.md`.
