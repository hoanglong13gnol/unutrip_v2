# README TOTAL — Hướng dẫn khắc phục toàn bộ điểm yếu (UNUtrip v2)

Tài liệu **playbook** bổ sung cho [`AGENT_GUIDE.md`](AGENT_GUIDE.md): không mô tả “đã làm gì”, mà **cách sửa những phần còn kém** sau rà soát toàn project (Android, Node, RAG, DB, CI, deploy, docs).

**Đối tượng:** tech lead, dev mới, agent — làm theo thứ tự **P0 → P1 → P2 → P3**.

**Tham chiếu nhanh:** [`NAMING.md`](NAMING.md) · [`BACKEND_RAG_BOUNDARY.md`](BACKEND_RAG_BOUNDARY.md) · [`README_UPDATING_CLEAN_v2.md`](../../README_UPDATING_CLEAN_v2.md)

---

## 1. Bản đồ điểm mạnh / điểm yếu

| Lớp | Điểm (1–10) | Trạng thái | Hành động chính trong guide |
|-----|-------------|-----------|------------------------------|
| RAG FastAPI | **8.5** | Ổn | §7 — prod artifact + vector + eval |
| Docs & boundary | **7.5** | Ổn | §8 — đồng bộ doc |
| Monorepo hygiene | **7.5** | Ổn (đã dọn) | §8 — giữ quy ước |
| Node Express | **6** | Trung bình | §4 — test, admin, upload, layering |
| CI GitHub Actions | **6** | Trung bình | §3 — compose + MySQL + smoke |
| DB / migrations | **5.5** | Yếu | §2 — bootstrap Docker |
| Deploy / ops | **5** | Yếu | §6 — full-stack runbook |
| Android | **5** | Yếu | §5 — Hilt, test, tách fragment |

**Mục tiêu sau khi hoàn thành P0–P1:** `docker compose up` ổn định, CI bắt regression stack, staging RAG+Node chạy được với artifact thật.

**Mục tiêu sau P2:** Android và Node đủ test + bảo mật dev/prod rõ ràng.

---

## 2. P0 — Database & Docker bootstrap (ưu tiên cao nhất)

### 2.1 Vấn đề

- `backend/nodejs/database.sql` chỉ có bảng legacy cơ bản, **thiếu** `rag_places`, `destination_images`.
- Compose mặc định `DATABASE_BOOTSTRAP_LEGACY=true` → migration **007–009** có thể **fail** trên DB trống.
- Không có bảng `schema_migrations` — khó biết DB đã apply tới đâu.

### 2.2 Cách khắc phục (chọn một hướng)

#### Hướng A — Khuyến nghị cho dev/staging: import dump rồi migrate

```bash
# 1. Đặt dump tại database/dumps/ (không commit)
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS unudata CHARACTER SET utf8mb4;"
mysql -u root -p unudata < database/dumps/unudata_v2.sql

# 2. Migrate v2 (bỏ bootstrap legacy)
cd database/scripts
export MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD= DB_NAME=unudata
export DATABASE_BOOTSTRAP_LEGACY=false
bash run_migrations.sh
```

#### Hướng B — Sửa bootstrap legacy cho Docker “trống”

1. Mở rộng `backend/nodejs/database.sql` thêm schema tối thiểu cho `rag_places`, `destination_images` (copy từ dump hoặc migration cũ).
2. Hoặc sửa `database/scripts/run_migrations.sh` skip **007–009** khi `rag_places` / `destination_images` không tồn tại (tương tự skip 006 khi không có `destinations`).

```bash
# Ví dụ logic cần thêm trong case 007_*|008_*|009_*:
#   if [[ "$(table_exists rag_places)" == "0" ]]; then continue; fi
```

#### Hướng C — Fresh v2 thuần (dài hạn)

1. Thêm migration `000_bootstrap_users.sql` (users, favorites, reviews tối thiểu) — không phụ thuộc `database.sql`.
2. Đặt Compose default `DATABASE_BOOTSTRAP_LEGACY=false`.
3. Document seed user trong `database/seeds/`.

### 2.3 Docker Compose checklist

| Việc | File | Ghi chú |
|------|------|---------|
| Document 3 path: dump / legacy / fresh | `database/README.md` | Thêm mục “Troubleshooting bootstrap” |
| Sau `db-migrate` success mới start backend | `docker-compose.yml` | Đã có — giữ |
| RAG artifact | `docker-compose.yml`, `.env` | Bật volume hoặc `RAG_ARTIFACT_BUNDLE_URL` |
| `backend` depends_on RAG **healthy** | `docker-compose.yml` | Đổi `service_started` → `service_healthy` |

```yaml
# docker-compose.yml — gợi ý
backend:
  depends_on:
    rag:
      condition: service_healthy
```

### 2.4 Tiêu chí hoàn thành P0-DB

- [ ] `docker compose up -d --build` trên máy sạch (hoặc volume mới) → `db-migrate` exit 0.
- [ ] `GET http://localhost:3000/api/health/ready` → 200.
- [ ] `GET http://localhost:8001/health/ready` → 200 (có index).
- [ ] `database/README.md` mô tả rõ 3 cách khởi tạo DB.

---

## 3. P0 — CI & kiểm thử tích hợp

### 3.1 Vấn đề

- CI không chạy `docker compose`, không apply migration lên MySQL thật.
- `smoke_staging_e2e` chỉ chạy tay — regression Node↔RAG không bị chặn.
- Node không có coverage gate.

### 3.2 Việc cần làm

#### Job mới: `stack-smoke.yml` (gợi ý)

```yaml
# .github/workflows/stack-smoke.yml (phác thảo)
jobs:
  compose-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build RAG fixture + verify
        working-directory: backend/rag
        run: |
          pip install -e ".[dev]"
          python jobs/build_rag_artifacts.py --from-fixture
          python scripts/verify_rag_artifacts.py --strict
      - name: Compose up
        run: |
          cp .env.example .env
          # chỉnh JWT_SECRET, GEMINI_API_KEY (secret), DATABASE_BOOTSTRAP_LEGACY theo chiến lược §2
          docker compose up -d --build --wait
      - name: Smoke Node ↔ RAG
        run: bash scripts/smoke_staging_e2e.sh
```

#### Job: migrate trên MySQL service

```yaml
services:
  mysql:
    image: mysql:8.0
    env: { MYSQL_ROOT_PASSWORD: test, MYSQL_DATABASE: unudata }
steps:
  - run: bash database/scripts/run_migrations.sh
    env:
      MYSQL_HOST: mysql
      DATABASE_BOOTSTRAP_LEGACY: "false"  # hoặc true + dump fixture nhỏ
```

#### Branch protection (GitHub repo settings)

- [ ] Bắt buộc: `rag-ci`, `backend-ci`, `android-ci`, (sau khi có) `stack-smoke`.

### 3.3 Tiêu chí hoàn thành P0-CI

- [ ] PR không merge được nếu migration script lỗi cú pháp hoặc compose health fail.
- [ ] Smoke script pass trên CI ít nhất 1 lần/tuần (hoặc mọi PR vào `main`).

---

## 4. P1 — Node backend

### 4.1 Vấn đề & hướng sửa

| Vấn đề | Khắc phục | File gợi ý |
|--------|-----------|--------------|
| Admin mở khi không set Basic auth | Production: `assertSafeProductionConfig` fail nếu thiếu `ADMIN_BASIC_*` | `config/env.js`, `production` guard |
| Upload public `/uploads` | Thêm auth middleware hoặc signed URL; prod tắt static công khai | `app.js`, `shared/http/upload.js` |
| Test mỏng | Vitest: destinations CRUD, favorites, place_id_map, upload | `tests/*.test.js` |
| Layering lệch | `AuthService`, `UserService`; admin gọi service | `services/`, `modules/` |
| Fat `ai.controller` | Tách validation + map response | `modules/ai/` |
| Hai client RAG | Một `lib/ragClient.js` + profile `api` / `admin` | `lib/ragUpstream.js`, `admin/_shared/ragHttp.js` |
| Legacy fallback | `USE_V2_PLACE_TABLES=true` + tắt fallback trên staging/prod | `.env`, `placeIdMap.repository.js` |
| Debug log | Xóa `[NEARBY] console.log` trong prod path | `destinations.service.js` |
| `asyncHandler` không dùng | Dùng `next(err)` hoặc xóa | `shared/http/asyncHandler.js` |

### 4.2 Test Node — danh sách tối thiểu

```bash
cd backend/nodejs
npm test
```

| Test file đề xuất | Phạm vi |
|-------------------|--------|
| `destinations.routes.test.js` | GET list, nearby mock DB |
| `placeIdMap.integration.test.js` | resolve `rawPlaceId` → `app_places.id` |
| `upload.security.test.js` | reject .exe, oversize |
| `adminAuth.production.test.js` | admin bị chặn khi thiếu credentials prod |

### 4.3 Bảo mật production `.env`

```env
NODE_ENV=production
JWT_SECRET=<random-64+>
RAG_INTERNAL_API_KEY=<random>
RAG_ADMIN_API_KEY=<random-khac>
ADMIN_BASIC_USER=admin
ADMIN_BASIC_PASS=<random>
USE_V2_PLACE_TABLES=true
PLACE_ID_LEGACY_FALLBACK=false
```

### 4.4 Tiêu chí hoàn thành P1-Node

- [ ] Không endpoint admin công khai trên staging.
- [ ] ≥30 test Vitest hoặc coverage gate ≥50% trên `src/services` + `src/repositories`.
- [ ] `npm test` pass trên CI không phụ thuộc `.env` local lệch (mock hoặc test env).

---

## 5. P1–P2 — Android (`app/`)

### 5.1 Vấn đề & hướng sửa

| Vấn đề | Khắc phục |
|--------|-----------|
| Không DI | Thêm **Hilt** (hoặc Koin): `AppModule` provide `ApiService`, repositories |
| `ProfileFragment` gọi API trực tiếp | `UserRepository` + `ProfileViewModel` |
| Token từng request | OkHttp `Interceptor` gắn Bearer + xử lý **401** → logout |
| God fragment | Tách `ItineraryFragment`, `AISuggestFragment`, adapter riêng file |
| Room / Compose dead | Gỡ dependency **hoặc** dùng thật (offline cache / màn Compose mới) |
| `GEMINI_API_KEY` trong APK | Xóa khỏi `build.gradle` / `local.properties` |
| Test ~5% | MockWebServer cho repo; 1 `androidTest` login → home |
| Error không đồng nhất | Dùng `parseErrorMessageOrNull()` mọi repository |

### 5.2 Thứ tự refactor đề xuất

```text
1. OkHttp auth interceptor + 401 handler
2. Hilt + UserRepository + ProfileViewModel
3. Test AuthViewModel + DestinationRepository (MockWebServer)
4. Tách ItineraryFragment (file < 300 dòng mỗi class)
5. (Tuỳ chọn) Compose cho màn mới
```

### 5.3 `local.properties` mẫu

```properties
API_BASE_URL=http://10.0.2.2:3000/api/
# Không cần GEMINI_API_KEY — AI qua Node
```

### 5.4 Tiêu chí hoàn thành P2-Android

- [ ] Không file Kotlin > 400 dòng (trừ generated).
- [ ] ≥1 instrumented test smoke.
- [ ] Không `RetrofitClient` trong Fragment (trừ debug).
- [ ] `assembleDevDebug` + `testDevDebugUnitTest` pass CI.

---

## 6. P1 — Deploy & vận hành

### 6.1 Vấn đề

- Chỉ RAG có `DEPLOY_CHECKLIST.md`; thiếu runbook Node + MySQL.
- Artifact RAG không mount mặc định → ready 503.
- Không IaC (K8s/Terraform).

### 6.2 Checklist deploy staging

| Bước | Lệnh / việc |
|------|----------------|
| DB | Import dump hoặc migrate §2 |
| RAG artifact | `cd backend/rag && python jobs/build_rag_artifacts.py --from-db --with-embeddings` |
| Package | `python jobs/package_rag_artifacts.py` |
| Upload bundle | `scripts/publish_rag_bundle.sh` hoặc GitHub Release |
| Env | `RAG_ARTIFACT_BUNDLE_URL`, `RAG_ENABLE_VECTOR=true`, `RAG_FETCH_ARTIFACTS_ON_START=true` |
| Node | `npm ci`, `NODE_ENV=production`, secrets §4.3 |
| Smoke | `bash scripts/smoke_staging_e2e.sh` |
| Metrics | `RAG_ENABLE_METRICS=true` + `deploy/prometheus/` |

### 6.3 Tạo tài liệu deploy (đề xuất thêm file)

| File đề xuất | Nội dung |
|--------------|----------|
| `deploy/README.md` | Sơ đồ port, dependency, thứ tự khởi động |
| `deploy/nginx/unutrip.conf.example` | Reverse proxy `/api` → Node, `/v1` → RAG |
| `deploy/BACKEND_DEPLOY_CHECKLIST.md` | PM2/Docker, backup MySQL, rotate uploads |
| `docker-compose.prod.yml` | Override secrets, không publish MySQL port |

### 6.4 Tiêu chí hoàn thành P1-Deploy

- [ ] Một người mới làm theo checklist deploy staging trong < 2 giờ.
- [ ] Rollback artifact RAG = đổi `RAG_ARTIFACT_BUNDLE_URL` + restart.

---

## 7. P1 — RAG (tinh chỉnh sau vector hybrid)

RAG đã ổn; phần còn lại là **vận hành & đo chất lượng**.

### 7.1 Production artifact + vector

```bash
cd backend/rag
pip install -e ".[dev,embeddings]"
python jobs/build_rag_artifacts.py --from-db --with-embeddings
python scripts/verify_rag_artifacts.py --strict
python jobs/package_rag_artifacts.py
```

`.env` staging/prod:

```env
RAG_ENABLE_VECTOR=true
RAG_ENABLE_RRF=true
RAG_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
```

### 7.2 Eval & chất lượng retrieval

```bash
python scripts/eval_rag_retrieval.py --golden eval/golden_queries.json --ci \
  --require-labels --min-hit-at5 0.75 --min-province-accuracy 1.0
```

| Việc | Mục đích |
|------|----------|
| Bổ sung `relevant_place_ids` vào `eval/golden_queries.json` | Đo hit@5 production |
| CI optional job `--with-embeddings` (manual/weekiy) | Không làm chậm PR thường |
| Log WARNING khi vector search fail | Tránh im lặng khi thiếu `sentence-transformers` |

### 7.3 Manifest — đừng commit nhầm

- Chỉ commit `rag_artifacts_manifest.json` khi **hash/count** đổi có chủ đích.
- Pre-commit: `backend/rag` → hook `manifest-staged-diff`.
- Sau `pytest` local có thể về fixture 10 docs — **đừng push** nếu không chủ đích.

### 7.4 Tiêu chí hoàn thành P1-RAG

- [ ] Staging dùng bundle ≥5000 docs + vector bật.
- [ ] Golden eval production pass trên release branch.
- [ ] `/admin/rag/status` hiển thị `embedding_enabled: true`.

---

## 8. P2 — Tài liệu & đồng bộ

### 8.1 File cần cập nhật khi sửa code

| File | Sửa gì |
|------|--------|
| `docs/v2/BACKEND_ARCHITECTURE.md` | Node đọc `app_places`, không còn “mọi route dùng destinations” |
| `docs/v2/AGENT_GUIDE.md` | Số test, path contract, link tới **file này** |
| `README.md` (root) | Link `README_TOTAL_GUIDE.md` |
| `database/README.md` | Bootstrap troubleshooting §2 |
| Xóa hoặc archive | `README_UPDATING_CLEAN.md` nếu trùng `_v2` |

### 8.2 Một nguồn sự thật roadmap

- **Trạng thái phase:** chỉ `README_UPDATING_CLEAN_v2.md`.
- **Cách làm việc hàng ngày:** `AGENT_GUIDE.md`.
- **Sửa điểm yếu:** `README_TOTAL_GUIDE.md` (tài liệu này).

---

## 9. P3 — Kiến trúc dài hạn (khi P0–P2 xong)

| Hạng mục | Mô tả |
|----------|--------|
| `schema_migrations` table | Flyway-style version tracking |
| Deprecate RAG `/chat` legacy | Chỉ `/v1/*` |
| FAISS / Qdrant | Khi corpus > 50k documents |
| Certificate pinning Android | Prod flavor |
| JWT refresh / revoke | Node + Android |
| E2E Detox / Maestro | Flow đặt tour + chat |
| Terraform / K8s | Khi có môi trường prod thật |

---

## 10. Master checklist (in ra hoặc tick trong PR)

### P0 — Bắt buộc trước demo công khai

- [ ] §2 DB bootstrap ổn trên Docker hoặc dump documented
- [ ] §3 CI compose smoke (hoặc manual checklist signed)
- [ ] RAG artifact có trên staging (`/health/ready` 200)
- [ ] `.env` không commit; secrets prod khác dev

### P1 — Production staging tin cậy

- [ ] §4 Node admin + upload hardened
- [ ] §6 Deploy checklist chạy được end-to-end
- [ ] §7 RAG bundle prod + vector (nếu dùng semantic)
- [ ] §8 Docs khớp code

### P2 — Chất lượng sản phẩm

- [ ] §5 Android DI + test + không god fragment
- [ ] Node coverage gate
- [ ] Golden eval full index

---

## 11. Lệnh kiểm tra nhanh (copy-paste)

```bash
# Toàn repo — sau khi sửa
cd backend/rag && make quality          # hoặc: ruff + mypy + pytest + verify
cd backend/nodejs && npm test && npm run lint
cd ../.. && ./gradlew :app:testDevDebugUnitTest :app:lintDevDebug

# Stack local
docker compose up -d --build
curl -s http://localhost:3000/api/health/ready | jq .
curl -s http://localhost:8001/health/ready | jq .

# RAG chat thử (cần JWT từ đăng ký)
# POST http://localhost:3000/api/ai/rag-chat  Authorization: Bearer ...
```

---

## 12. Phân công gợi ý (team 2–3 người)

| Người | Focus | Section |
|-------|--------|---------|
| Backend | DB bootstrap + Node test + admin | §2, §4 |
| ML/RAG | Artifact prod + eval + vector | §7 |
| Mobile | Android refactor + test | §5 |
| DevOps | CI stack-smoke + deploy docs | §3, §6 |

---

## 13. Liên kết tài liệu hiện có

| Tài liệu | Khi nào đọc |
|----------|-------------|
| [`AGENT_GUIDE.md`](AGENT_GUIDE.md) | Onboarding, lệnh dev, pitfalls |
| [`NAMING.md`](NAMING.md) | Đặt tên DB/package |
| [`BACKEND_RAG_BOUNDARY.md`](BACKEND_RAG_BOUNDARY.md) | Ai sở hữu bảng / API |
| [`backend/rag/docs/DEPLOY_CHECKLIST.md`](../../backend/rag/docs/DEPLOY_CHECKLIST.md) | Deploy RAG chi tiết |
| [`backend/rag/docs/RETRIEVAL.md`](../../backend/rag/docs/RETRIEVAL.md) | BM25 / TF-IDF / vector |
| [`database/README.md`](../../database/README.md) | Migrations |
| [`README_UPDATING_CLEAN_v2.md`](../../README_UPDATING_CLEAN_v2.md) | Lịch sử phase |

---

*Cập nhật guide này khi hoàn thành từng mục P0–P2 — tick trong §10 và ghi ngày ở commit message (`docs: close P0-DB bootstrap` etc.).*
