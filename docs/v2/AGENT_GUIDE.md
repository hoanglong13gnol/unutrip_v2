# Hướng dẫn Agent — UNUtrip v2

Tài liệu **bàn giao** cho agent / dev mới: kiến trúc, trạng thái code, lệnh, pitfalls.  
Index tài liệu: [`README.md`](README.md) · Repo tách từ `e:\UNUtrip` (demo gốc **không sửa**).

**Lịch sử phase (archive):** [`backup_suport_file/README_UPDATING_CLEAN_v2.md`](../../backup_suport_file/README_UPDATING_CLEAN_v2.md)

---

## 1. Mục tiêu hệ thống

| Thành phần | Vai trò |
|------------|---------|
| `app/` | Android — gọi **Node**, không gọi RAG trực tiếp |
| `backend/nodejs/` | Express API, JWT, MySQL, proxy RAG, admin web |
| `backend/rag/` | FastAPI: BM25/hybrid retrieval + Gemini/template |
| `database/migrations/` | Schema v2 (`app_places`, `rag_knowledge_base`, …) |
| `docker-compose.yml` | MySQL + Redis + RAG + Node + `db-migrate` |
| `backup_suport_file/` | Luận văn / use case — **không** spec runtime |

**Luồng RAG:** Android → Node (`/api/ai/rag-chat`) → RAG (`/v1/rag/chat/simple`) → BM25 artifact trên disk.

**Boundary:** [`BACKEND_RAG_BOUNDARY.md`](BACKEND_RAG_BOUNDARY.md)

---

## 2. Cấu trúc RAG (đọc trước khi sửa)

Chi tiết: [`RAG_ARCHITECTURE.md`](RAG_ARCHITECTURE.md)

```text
backend/rag/
  app/routers/          # HTTP only
  services/             # RagService, ItineraryService, admin/*
  pipelines/            # RagPipeline + policies + response_builder
  retrieval/            # bm25, hybrid, intent, fusion, rerank
  providers/ + llm/     # Gemini + template
  jobs/ + scripts/      # build artifacts, verify, eval
  tests/                # pytest + contracts/
```

**Quy tắc refactor:** retrieval → `retrieval/`; policy → `pipelines/policies/`; không `sys.path` hack — `pip install -e ".[dev]"`.

---

## 3. Đã làm (đừng phá / đừng làm lại)

### 3.1 Node v2 place tables

- [x] Destinations API đọc **`app_places`** + **`place_images`**
- [x] Reviews aggregate ghi **`app_places`**
- [x] `place_id_map` + flags `USE_V2_PLACE_TABLES` / `PLACE_ID_LEGACY_FALLBACK`
- [x] Contract tests: `ragContract*.test.js`, `tests/contracts/`

### 3.2 RAG kiến trúc & CI

- [x] Pipeline tách: policies, providers, response_builder
- [x] Pytest RAG **~138 tests** (xem §7 — một vài test pipeline có thể fail local)
- [x] Coverage gate **≥70%** (`pyproject.toml`)
- [x] CI: `rag-ci.yml`, `backend-ci.yml`, `android-ci.yml`
- [x] Artifact pipeline: `jobs/build_rag_artifacts.py`, manifest, `artifact_store`

### 3.3 Database & Docker

- [x] `database/migrations/` canonical; `database.sql` deprecated bootstrap
- [x] Compose service `db-migrate`; backend `USE_V2_PLACE_TABLES=true`

### 3.4 Admin Node

- [x] Admin tách module: `admin/index.js` + `*.admin.routes.js`

### 3.5 Repo hygiene

- [x] `.gitignore`: artifacts lớn, `.env`, uploads, cache
- [x] Tài liệu luận văn → `backup_suport_file/`

---

## 4. Còn làm / backlog

Chi tiết ưu tiên: [`README_TOTAL_GUIDE.md`](README_TOTAL_GUIDE.md)

### P0 — Không regression

- [ ] Không commit `.pkl`, JSONL lớn, `.env`, manifest chỉ đổi timestamp
- [ ] Fix test đang fail (Node 4, RAG 2 — xem §7)

### Cao

| # | Task | Ghi chú |
|---|------|---------|
| 1 | Branch protection GitHub | Bắt buộc `rag-ci` + `backend-ci` trên `main` |
| 2 | CI stack smoke | Workflow `docker compose` + `smoke_staging_e2e` — chưa có |
| 3 | `backend` depends_on RAG **healthy** | Hiện `service_started` trong compose |

### Trung bình

| # | Task |
|---|------|
| 4 | Test admin/itinerary services RAG (hiện omit coverage) |
| 5 | Golden eval trên full production index |
| 6 | Xóa `[NEARBY] console.log` trong `destinations.service.js` |

### Thấp / Phase 8 Android

| # | Task |
|---|------|
| 7 | Hilt/DI, OkHttp 401 interceptor |
| 8 | Xóa `GEMINI_API_KEY` khỏi `build.gradle` |
| 9 | Gỡ hoặc wire legacy `AISuggestFragment` |
| 10 | Deprecate RAG routes không `/v1` |

---

## 5. Lệnh thường dùng

### Stack Docker

```bash
cp .env.example .env
docker compose up -d --build
curl http://localhost:3000/api/health
curl http://localhost:8001/health/ready
```

### RAG (`backend/rag`)

```bash
pip install -e ".[dev]"
make quality          # hoặc ruff + mypy + pytest + verify
python jobs/build_rag_artifacts.py --from-fixture
uvicorn app.main:app --reload --port 8001
```

### Node

```bash
cd backend/nodejs
npm ci && npm test && npm run lint
```

### Database

```bash
export MYSQL_HOST=127.0.0.1 MYSQL_USER=... MYSQL_PASSWORD=... DB_NAME=unudata
bash database/scripts/run_migrations.sh
```

### Android

```properties
# local.properties
API_BASE_URL=http://10.0.2.2:3000/api/
```

```bash
./gradlew :app:assembleDevDebug :app:testDevDebugUnitTest
```

---

## 6. CI — workflow map

| File | Trigger | Việc chính |
|------|---------|------------|
| `rag-ci.yml` | `backend/rag/**` | Ruff, mypy, pytest, Docker, verify, golden eval |
| `backend-ci.yml` | `backend/nodejs/**`, `database/**` | ESLint, Vitest, Docker Node |
| `android-ci.yml` | `app/**` | Unit test, lint, assemble devDebug |
| `rag-artifact-release*.yml` | Manual | Package/upload RAG bundle |

---

## 7. Trạng thái test (cập nhật khi chạy local)

Chạy trước PR:

```bash
cd backend/rag && python -m pytest tests/ -q
cd backend/nodejs && npm test
./gradlew :app:testDevDebugUnitTest
```

**Kỳ vọng hiện tại (có thể thay đổi):**

| Suite | Số lượng | Ghi chú |
|-------|----------|---------|
| RAG pytest | ~138 | Đa số pass; known fail có thể ở `test_rag_pipeline_unit.py` |
| Node Vitest | 52 (18 files) | Một số fail env/route — fix trước khi merge nếu đụng Node |
| Android unit | xem CI | Robolectric + mockk |

---

## 8. Pitfalls

| Vấn đề | Cách tránh |
|--------|------------|
| Manifest path tuyệt đối Windows | Dùng path relative; `verify --strict` |
| RAG `/health/ready` 503 | Thiếu `bm25_index.pkl` — `build --from-fixture` hoặc fetch bundle |
| Compose DB trống | `db-migrate` + `DATABASE_BOOTSTRAP_LEGACY=true` hoặc import dump |
| Place id không map | `place_id_map`, `USE_V2_PLACE_TABLES`, legacy fallback |
| sklearn pickle | `scikit-learn==1.7.1` cho index |
| Doc luận văn cũ | Đọc `docs/v2/*` + code, không tin `backup_suport_file/` flow doc |
| Android gọi RAG trực tiếp | Sai — chỉ qua Node `/api/ai/*` |

---

## 9. Checklist PR

1. [ ] RAG quality / Node test nếu đụng backend
2. [ ] Không secrets / artifacts lớn trong `git status`
3. [ ] Cập nhật doc nếu đổi env, API, migration
4. [ ] Không tự `git push` / tạo PR trừ khi user yêu cầu

---

## 10. Tài liệu tham chiếu

| File | Nội dung |
|------|----------|
| [`README.md`](README.md) | Index docs v2 |
| [`README_TOTAL_GUIDE.md`](README_TOTAL_GUIDE.md) | Backlog P0–P3 |
| [`BACKEND_ARCHITECTURE.md`](BACKEND_ARCHITECTURE.md) | Node layers + v2 status |
| [`RAG_ARCHITECTURE.md`](RAG_ARCHITECTURE.md) | RAG layers + flow |
| [`PHASE7_NODE_ANDROID_PARITY.md`](PHASE7_NODE_ANDROID_PARITY.md) | Place flags + contract |
| [`REFACTOR_PHASE_PLAN.md`](REFACTOR_PHASE_PLAN.md) | Phase 1–8 status |
| [`../../README.md`](../../README.md) | Monorepo root |
| [`../../database/README.md`](../../database/README.md) | Migrations |
| [`../../backend/rag/docs/`](../../backend/rag/docs/) | Artifact, deploy, retrieval |

Khi đóng task lớn: cập nhật §3–§4 file này hoặc archive log trong `backup_suport_file/`.
