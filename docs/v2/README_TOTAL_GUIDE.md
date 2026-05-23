# README TOTAL — Backlog khắc phục điểm yếu (UNUtrip v2)

Playbook bổ sung cho [`AGENT_GUIDE.md`](AGENT_GUIDE.md): **việc còn lại** sau rà soát code (Android, Node, RAG, DB, CI, deploy).

**Không phải snapshot “đã xong hết”** — đối chiếu [`REFACTOR_PHASE_PLAN.md`](REFACTOR_PHASE_PLAN.md) cho phase đã đóng.

**Index tài liệu:** [`README.md`](README.md)

---

## 1. Bản đồ điểm mạnh / điểm yếu (cập nhật)

| Lớp | Điểm | Trạng thái | Hành động chính |
|-----|------|-----------|-----------------|
| RAG FastAPI | **8.5** | Ổn | Prod eval, optional vector/cross-encoder |
| Docs v2 | **8** | Ổn (vừa sync code) | Giữ AGENT_GUIDE + architecture updated |
| Monorepo hygiene | **8** | Ổn | Luận văn → `backup_suport_file/` |
| Node Express | **6.5** | Khá | Fix failing tests, harden admin/upload |
| DB / migrations | **6** | Khá | Bootstrap Docker trống vẫn dễ fail 007–009 |
| CI GitHub Actions | **5.5** | Yếu | Thiếu compose smoke job |
| Deploy / ops | **5.5** | Khá | Có `deploy/README.md`; thiếu nginx prod example |
| Android | **5** | Yếu | DI, test, legacy nav, GEMINI key trong gradle |

**Đã cải thiện so với bản cũ:**

- ✅ Node runtime đọc `app_places` / `place_images` (không còn “mọi route dùng destinations”)
- ✅ Admin modular shell
- ✅ Contract parity Node↔RAG (fixture + tests)
- ✅ Phase 1–7 refactor plan (trừ Android Phase 8)

---

## 2. P0 — Database & Docker bootstrap

### 2.1 Vấn đề còn lại

- `database.sql` bootstrap thiếu một số bảng legacy → migration **006–009** skip hoặc fail trên DB trống.
- Không có bảng `schema_migrations` — khó audit apply tới đâu.

### 2.2 Ba hướng (chọn một)

#### A — Khuyến nghị: import dump rồi migrate

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS unudata CHARACTER SET utf8mb4;"
mysql -u root -p unudata < database/dumps/unudata_v2.sql
export MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD= DB_NAME=unudata
export DATABASE_BOOTSTRAP_LEGACY=false
bash database/scripts/run_migrations.sh
```

#### B — Docker DB trống

- Giữ `DATABASE_BOOTSTRAP_LEGACY=true` (default Compose)
- Hoặc mở rộng `database.sql` / skip 007–009 khi thiếu `rag_places`

#### C — Fresh v2 (dài hạn)

- Migration `000_bootstrap_users.sql` + seed tối thiểu
- `DATABASE_BOOTSTRAP_LEGACY=false` mặc định

### 2.3 Compose checklist

| Việc | Trạng thái |
|------|------------|
| `db-migrate` before backend | ✅ |
| Backend `USE_V2_PLACE_TABLES=true` | ✅ |
| RAG artifact volume / bundle URL | ⚠️ Cần build local hoặc `RAG_ARTIFACT_BUNDLE_URL` |
| Backend waits RAG **healthy** | ❌ Hiện `service_started` — nên đổi |

### 2.4 Tiêu chí P0-DB

- [ ] `docker compose up` trên volume mới → `db-migrate` exit 0
- [ ] `/api/health/ready` + `/health/ready` → 200
- [x] `database/README.md` có troubleshooting (§ bên dưới file đó)

---

## 3. P0 — CI & tích hợp

### 3.1 Vấn đề

- Không job `docker compose` + smoke tự động
- Node Vitest **52 tests** — **4 fail** cần fix (không block doc nhưng block merge quality)
- Không coverage gate Node

### 3.2 Việc cần làm

- [ ] Workflow `stack-smoke.yml` (phác thảo trong bản cũ — chưa implement)
- [ ] Job migrate trên MySQL service CI
- [ ] Branch protection: `rag-ci`, `backend-ci`, `android-ci`

### 3.3 Tiêu chí P0-CI

- [ ] PR fail nếu migration script lỗi
- [ ] Smoke Node↔RAG pass trên CI hoặc weekly manual signed

---

## 4. P1 — Node backend

### 4.1 Đã xong

- [x] Layered modules/services/repositories
- [x] v2 place reads + place_id_map
- [x] Admin tách file routes
- [x] Production config guard (`assertSafeProductionConfig`)
- [x] RAG client `lib/ragUpstream.js`

### 4.2 Còn lại

| Vấn đề | Khắc phục |
|--------|-----------|
| Upload public `/uploads` | Auth hoặc signed URL prod |
| Test fail (4) | Fix trước release |
| `[NEARBY] console.log` | Xóa khỏi `destinations.service.js` |
| Fat `ai.controller` | Tách validation nếu mở rộng |
| Coverage gate | Vitest `--coverage` ≥50% services/repos |

### 4.3 Test Node hiện có (18 files)

`auth`, `health`, `ragContract`, `ragUpstream`, `placeIdMap`, `destinationDto`, `itineraryDto`, `admin`, `ai-rag-chat`, …

**Đề xuất thêm:** destinations integration, upload security, admin prod auth.

### 4.4 Tiêu chí P1-Node

- [ ] 0 failing Vitest trên `main`
- [ ] Admin không mở công khai prod without Basic auth
- [ ] ≥50% coverage services (optional gate)

---

## 5. P1–P2 — Android

### 5.1 Hiện trạng code

- Bottom nav: Home, Khám phá, Lịch trình, Trợ lý AI, Cá nhân
- AI tour flow: `AIItineraryRequest` → `Options` → `Editor`
- Legacy: `AISuggestFragment` trong nav — **không có navigate()**
- `GeminiService.kt` gọi **Node API** (tên misleading)
- `build.gradle` vẫn embed `GEMINI_API_KEY` — **không cần** cho runtime chat
- OSMDroid maps; weather qua Open-Meteo client-side

### 5.2 Backlog

| # | Task |
|---|------|
| 1 | OkHttp Bearer interceptor + 401 → logout |
| 2 | Hilt/Koin DI |
| 3 | MockWebServer tests cho repositories |
| 4 | Tách `AISuggestFragment` ra file riêng; gỡ hoặc wire nav |
| 5 | Xóa `GEMINI_API_KEY` từ `build.gradle` |
| 6 | Gỡ Room/Compose deps nếu không dùng |

### 5.3 Tiêu chí P2-Android

- [ ] Không fragment >400 dòng (trừ generated)
- [ ] ≥1 instrumented smoke
- [ ] `testDevDebugUnitTest` pass CI

---

## 6. P1 — Deploy & vận hành

Xem [`../../deploy/README.md`](../../deploy/README.md) và [`../../backend/rag/docs/DEPLOY_CHECKLIST.md`](../../backend/rag/docs/DEPLOY_CHECKLIST.md).

### Checklist staging

| Bước | Lệnh |
|------|------|
| DB | Import dump hoặc §2 |
| RAG artifact | `python jobs/build_rag_artifacts.py --from-db` |
| Package | `python jobs/package_rag_artifacts.py` |
| Env | `RAG_ARTIFACT_BUNDLE_URL`, secrets prod |
| Smoke | `scripts/smoke_staging_e2e.sh` / `.ps1` |

### Còn thiếu (optional)

- [ ] `deploy/nginx/unutrip.conf.example`
- [ ] `docker-compose.prod.yml`
- [ ] `deploy/BACKEND_DEPLOY_CHECKLIST.md`

---

## 7. P1 — RAG tinh chỉnh

### Đã có

- Artifact pipeline, manifest, CI fixture build
- Hybrid BM25 + rerank; optional vector/RRF flags
- ~138 pytest

### Còn lại

- [ ] Fix 2 failing pipeline unit tests (nếu vẫn fail trên main)
- [ ] Golden eval full index `eval/golden_queries.json`
- [ ] Cross-encoder prod optional
- [ ] Staging bundle ≥5000 docs + vector nếu bật semantic

---

## 8. P2 — Đồng bộ tài liệu

| File | Trạng thái |
|------|------------|
| `docs/v2/*` | ✅ Synced với code (2026-05) |
| `README.md` root | ✅ Updated |
| `database/README.md` | ✅ + troubleshooting |
| `backup_suport_file/*` | Archive — không cập nhật theo code |

**Nguồn sự thật hàng ngày:** code + `AGENT_GUIDE.md` + architecture docs.

---

## 9. P3 — Dài hạn

| Hạng mục | Mô tả |
|----------|--------|
| `schema_migrations` table | Track version apply |
| Deprecate RAG không `/v1` | Mirror removal |
| JWT refresh / revoke | Node + Android |
| E2E Maestro/Detox | Tour + chat |
| K8s/Terraform | Khi có prod |

---

## 10. Master checklist

### P0 — Trước demo công khai

- [ ] §2 DB bootstrap documented + tested
- [ ] §3 CI smoke (hoặc manual checklist)
- [ ] RAG `/health/ready` 200 trên staging
- [x] `.env` không commit

### P1 — Staging tin cậy

- [ ] §4 Node tests green + admin/upload
- [ ] §6 Deploy checklist chạy E2E
- [ ] §7 RAG prod bundle
- [x] §8 Docs khớp code

### P2 — Chất lượng sản phẩm

- [ ] §5 Android DI + test
- [ ] Golden eval full index

---

## 11. Lệnh kiểm tra nhanh

```bash
cd backend/rag && make quality
cd backend/nodejs && npm test && npm run lint
./gradlew :app:testDevDebugUnitTest :app:lintDevDebug

docker compose up -d --build
curl -s http://localhost:3000/api/health/ready
curl -s http://localhost:8001/health/ready
```

---

## 12. Liên kết

| Tài liệu | Khi nào đọc |
|----------|-------------|
| [`AGENT_GUIDE.md`](AGENT_GUIDE.md) | Onboarding + lệnh |
| [`BACKEND_ARCHITECTURE.md`](BACKEND_ARCHITECTURE.md) | Node v2 status |
| [`RAG_ARCHITECTURE.md`](RAG_ARCHITECTURE.md) | RAG flow |
| [`REFACTOR_PHASE_PLAN.md`](REFACTOR_PHASE_PLAN.md) | Phase done/open |
| [`backup_suport_file/README_UPDATING_CLEAN_v2.md`](../../backup_suport_file/README_UPDATING_CLEAN_v2.md) | Lịch sử archive |

*Tick §10 khi hoàn thành mục — ghi trong commit message (`docs: close P0-DB`).*
