# README_CHUONG_4_FINAL - UNU Trip

> Tài liệu kỹ thuật phục vụ viết **Chương 4 — Triển khai và thử nghiệm hệ thống** đồ án tốt nghiệp.  
> Mọi nhận định dưới đây bám theo code/cấu hình hiện có trong repo `UNUtrip_v2`.  
> Nội dung không xác minh được từ code được ghi **CHƯA XÁC MINH**.

---

## 1. Tổng quan triển khai hệ thống

Hệ thống UNU Trip là monorepo gồm ứng dụng Android, API Node.js, dịch vụ RAG Python, cơ sở dữ liệu MySQL và dashboard quản trị web server-rendered.

| Thành phần | Đường dẫn | Vai trò | Công nghệ chính | Trạng thái hiện tại |
|---|---|---|---|---|
| **Android App** | `app/` | Client di động: đăng nhập, khám phá địa điểm, lịch trình, AI chat, bản đồ, thời tiết | Kotlin, Android SDK 34, Retrofit, OSMDroid, Navigation Component | **Đã có code đầy đủ** — UI + gọi API qua `ApiService.kt`. Trạng thái chạy trên thiết bị thật: **CHƯA XÁC MINH** trong phiên làm việc này |
| **Backend Node.js/Express** | `backend/nodejs/` | REST API `/api/*`, proxy AI/RAG, phục vụ upload ảnh, dashboard admin `/admin/*` | Node.js 20 (Docker), Express 4.x, mysql2, JWT, Zod | **Đã có code + test tự động** (48/52 test pass — xem mục 9). Chạy thực tế: **CHƯA XÁC MINH** E2E |
| **MySQL Database** | `database/migrations/`, legacy `backend/nodejs/database.sql` | Lưu users, địa điểm (v2: `app_places`), reviews, favorites, itineraries, RAG knowledge | MySQL 8.0 (Docker Compose) / MariaDB qua XAMPP (tài liệu) | **Schema + migration có trong repo**. Dữ liệu runtime phụ thuộc import/migration — **CHƯA XÁC MINH** DB demo hiện tại |
| **FastAPI RAG Service** | `backend/rag/` | Retrieval + generation: chat RAG, gợi ý lịch trình AI, admin debug | Python ≥3.12, FastAPI, Uvicorn, BM25/sklearn, Gemini (tùy chọn) | **Đã có code + CI**. Mặc định code: `AI_RUNTIME_MODE=mock`; `.env.example`: `demo` + Gemini — xem mục 4.3 |
| **Admin Dashboard** | `backend/nodejs/src/admin/` | Quản trị users, destinations, reviews, system, RAG monitor (HTML SSR) | Express routes + templates HTML | **Đã có code** (26 route admin — `tests/admin.router.test.js`). Bảo mật admin phụ thuộc biến môi trường — xem mục 4.5 |
| **Dịch vụ bản đồ** | `app/.../MapFragment.kt` | Hiển thị bản đồ OSM, marker địa điểm, định vị người dùng | OSMDroid 6.1.18, Play Services Location | **Đã có code** — tile OSM qua OSMDroid; không dùng Google Maps SDK |
| **Dịch vụ thời tiết** | `app/.../WeatherService.kt` | Hiển thị thời tiết tại chi tiết địa điểm | Open-Meteo API (gọi trực tiếp từ Android) | **Đã có code** — **không qua backend Node** |

**Nguồn:** `README.md`, `docker-compose.yml`, `app/build.gradle`, `backend/nodejs/package.json`, `backend/rag/pyproject.toml`.

---

## 2. Môi trường cài đặt và công cụ sử dụng

| Thành phần | Công cụ/công nghệ | Phiên bản (nếu xác minh được) | Vai trò | Nguồn xác minh |
|---|---|---|---|---|
| Node.js runtime | Node.js | **20** (Docker); local: **CHƯA XÁC MINH** (không có `engines` trong `package.json`) | Chạy backend Express | `backend/nodejs/Dockerfile` (`FROM node:20-bookworm-slim`) |
| Backend framework | Express | ^4.21.2 | HTTP API | `backend/nodejs/package.json` |
| ORM/driver DB | mysql2 | ^3.12.0 | Kết nối MySQL pool | `backend/nodejs/package.json`, `backend/nodejs/src/db.js` |
| Auth/hash | jsonwebtoken, bcryptjs | ^9.0.2, ^3.0.2 | JWT user + hash mật khẩu | `backend/nodejs/package.json`, `auth.controller.js` |
| Validate input | Zod | ^3.25.76 | Schema request body | `backend/nodejs/package.json` |
| Security HTTP | helmet, cors, morgan | ^7.2.0, ^2.8.5, ^1.10.0 | CSP, CORS, logging | `backend/nodejs/package.json`, `src/app.js` |
| Upload | multer | ^2.1.1 | Avatar, ảnh review | `backend/nodejs/package.json`, `src/shared/http/upload.js` |
| Test backend | Vitest, Supertest | ^3.2.4, ^7.1.4 | Unit/integration route test | `backend/nodejs/package.json`, `vitest.config.js` |
| Python runtime | Python | **≥3.12** | Chạy RAG FastAPI | `backend/rag/pyproject.toml` (`requires-python = ">=3.12"`) |
| RAG framework | FastAPI, Uvicorn | fastapi ≥0.115,<0.116; uvicorn ≥0.32,<0.33 | API RAG + AI itinerary | `backend/rag/pyproject.toml` |
| ML retrieval | scikit-learn, rank-bm25 | sklearn **==1.7.1** | BM25/TF-IDF index | `backend/rag/pyproject.toml` |
| Gemini SDK | google-genai | ≥1.0,<2 | Gọi model Gemini (khi bật) | `backend/rag/pyproject.toml` |
| Cache/rate limit | redis | ≥5.0,<6 | Rate limit, cache Gemini (tùy chọn) | `backend/rag/pyproject.toml`, `docker-compose.yml` |
| MySQL server | MySQL | **8.0** (Docker image) | CSDL chính | `docker-compose.yml` (`image: mysql:8.0`) |
| Android Gradle | Gradle | **8.4** | Build Android | `gradle/wrapper/gradle-wrapper.properties` |
| Android Gradle Plugin | AGP | **8.2.2** | Build plugin | `build.gradle` |
| Kotlin | Kotlin | **1.9.23** | Ngôn ngữ Android | `build.gradle` |
| Android SDK | compileSdk / targetSdk / minSdk | **34 / 34 / 26** | Target platform | `app/build.gradle` |
| HTTP client Android | Retrofit, OkHttp | **2.9.0**, **4.12.0** | Gọi API backend | `app/build.gradle` |
| Bản đồ Android | OSMDroid | **6.1.18** | MapView tile OSM | `app/build.gradle` |
| Định vị Android | Play Services Location | **21.3.0** | FusedLocationProvider | `app/build.gradle` |
| Thời tiết | Open-Meteo REST | API công khai (không key) | Forecast 5 ngày | `app/.../WeatherService.kt` |
| Docker Compose | docker-compose | File `docker-compose.yml` ở root | Stack MySQL + Redis + RAG + Backend | `docker-compose.yml` |
| XAMPP / phpMyAdmin | XAMPP (tài liệu) | **CHƯA XÁC MINH phiên bản** | Import legacy SQL / quản lý DB local | `backend/nodejs/database.sql` (dòng 5), `database/README.md`, `.env.example` (dòng 88) |
| Postman | — | **CHƯA XÁC MINH** | Không tìm thấy collection Postman trong repo | Tìm kiếm `*postman*` → 0 file |
| Android Studio | IDE | **CHƯA XÁC MINH phiên bản** | Build/chạy app | Suy luận từ project Gradle — không ghi trong repo |

---

## 3. Cấu trúc thư mục dự án

```
UNUtrip_v2/
├── app/                          # Module Android (Kotlin)
│   └── src/main/java/com/unutrip/
│       ├── data/api/             # Retrofit ApiService, RetrofitClient
│       ├── ui/                   # Activities, Fragments (auth, home, destination, itinerary, chatbot, profile)
│       └── utils/                # WeatherService, SessionManager, MapIntentHelper
├── backend/
│   ├── nodejs/                   # Express API + Admin SSR
│   │   ├── src/modules/          # auth, users, destinations, favorites, reviews, itineraries, ai, health
│   │   ├── src/admin/            # Admin routes + templates HTML
│   │   ├── src/repositories/     # Truy vấn MySQL
│   │   ├── src/services/         # Business logic + proxy RAG
│   │   └── tests/                # Vitest (18 file)
│   └── rag/                      # FastAPI RAG service
│       ├── app/routers/          # health, rag, ai_itinerary, admin/*
│       ├── pipelines/            # RagPipeline, GenerationRouter
│       ├── retrieval/            # BM25, place store
│       └── data/                 # Index, cache (một phần gitignored)
├── database/
│   ├── migrations/               # 001–011: schema v2 + populate + validation
│   ├── scripts/run_migrations.sh # Script apply migration
│   └── dumps/                    # SQL lớn (gitignored)
├── docs/v2/                      # Tài liệu kiến trúc nội bộ (AGENT_GUIDE, RAG_ARCHITECTURE, …)
├── docker-compose.yml            # Stack đầy đủ MySQL + Redis + RAG + Backend
├── .env.example                  # Mẫu biến môi trường root (Node + RAG)
└── README.md                     # Hướng dẫn tổng quan monorepo
```

| Thư mục | Giải thích |
|---|---|
| `app/` | Ứng dụng Android: 2 Activity (`AuthActivity`, `MainActivity`), nhiều Fragment theo `nav_graph.xml`, gọi backend qua `BuildConfig.BASE_URL`. |
| `backend/nodejs/` | API REST prefix `/api`, admin prefix `/admin`, kết nối MySQL `unudata`, proxy sang RAG tại `RAG_BASE_URL`. |
| `backend/rag/` | Microservice Python: endpoint chat/retrieve/itinerary; admin ops; index BM25 cần build hoặc fetch artifact. |
| `database/migrations/` | Nguồn schema v2 chính thức: `app_places`, `rag_knowledge_base`, `place_images`, `place_id_map`, bảng itinerary v2. |
| `backend/nodejs/src/admin/` | Dashboard admin server-rendered: dashboard, users, destinations, reviews, system, RAG AI monitor. |
| `.env.example` | Template cấu hình DB, JWT, RAG, Gemini, admin; Android dùng `local.properties` riêng. |

---

## 4. Quy trình cài đặt và chạy hệ thống

### 4.1. Chuẩn bị cơ sở dữ liệu MySQL

| Hạng mục | Giá trị xác minh |
|---|---|
| **Tên database mặc định** | `unudata` — `backend/nodejs/src/db.js`, `.env.example` |
| **Schema legacy (bootstrap)** | `backend/nodejs/database.sql` — tạo `users`, `destinations`, `favorites`, `reviews`, `itineraries`, `itinerary_days`, `itinerary_items` + seed `destinations` |
| **Schema v2 (canonical)** | `database/migrations/001`–`011` |
| **Script migration** | `database/scripts/run_migrations.sh` |
| **Docker migrate** | Service `db-migrate` trong `docker-compose.yml` |

**Thứ tự migration (theo `database/migrations/README.md`):**

1. `001_create_app_places.sql` → bảng `app_places`
2. `002_create_rag_knowledge_base.sql` → `rag_knowledge_base`
3. `003_create_place_images.sql` → `place_images`
4. `004_create_place_id_map.sql` → `place_id_map`
5. `005_create_v2_indexes.sql` → chỉ index
6. `006`–`009` populate (bỏ qua nếu không có bảng legacy `destinations`)
7. `010_v2_validation_queries.sql` → SELECT kiểm tra
8. `011_create_itinerary_tables.sql` → `itineraries`, `itinerary_days`, `itinerary_items` (FK tới `app_places`)

**Bảng có `CREATE TABLE` trong repo:**

| Bảng | Nguồn CREATE |
|---|---|
| `users`, `destinations`, `favorites`, `reviews`, `itineraries`, `itinerary_days`, `itinerary_items` | `backend/nodejs/database.sql` |
| `app_places` | `database/migrations/001_create_app_places.sql` |
| `rag_knowledge_base` | `database/migrations/002_create_rag_knowledge_base.sql` |
| `place_images` | `database/migrations/003_create_place_images.sql` |
| `place_id_map` | `database/migrations/004_create_place_id_map.sql` |
| `itineraries`, `itinerary_days`, `itinerary_items` (v2 FK) | `database/migrations/011_create_itinerary_tables.sql` |

**Bảng được tham chiếu nhưng KHÔNG có CREATE trong repo:**

| Bảng | Ghi chú |
|---|---|
| `rag_places` | Dùng trong migration populate 006–010; kỳ vọng từ dump ngoài repo — `database/dumps/README.md` |
| `destination_images` | Tương tự — legacy, không có CREATE trong repo |

**Import thủ công (local XAMPP):**

```bash
# 1. Import dump hoặc backend/nodejs/database.sql qua phpMyAdmin / mysql CLI
# 2. Apply migration v2
export MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD=<placeholder> DB_NAME=unudata
export DATABASE_BOOTSTRAP_LEGACY=false
bash database/scripts/run_migrations.sh
```

**Docker (khuyến nghị trong `database/README.md`):**

```bash
cp .env.example .env
docker compose up -d --build
```

**Seed script Node (`backend/nodejs/src/seed.js`):**

- Tạo user demo `demo@unutrip.local`, password hash từ chuỗi `"123456"` (bcrypt) — dòng 115–126.
- Seed `destinations`, `itineraries`, `reviews` vào bảng **legacy** `destinations`.
- **CHƯA XÁC MINH:** script **không** được gọi tự động khi `npm start` (`src/index.js` không import seed). Không có npm script chạy seed.

---

### 4.2. Cấu hình và chạy Backend Node.js/Express

| Hạng mục | Giá trị |
|---|---|
| **Thư mục** | `backend/nodejs/` |
| **Cài dependency** | `npm ci` hoặc `npm install` |
| **Chạy dev** | `npm run dev` → `node --watch src/index.js` |
| **Chạy production local** | `npm start` → `node src/index.js` |
| **Port mặc định** | **3000** (`BACKEND_PORT` / `PORT`) — `src/index.js` |
| **Host mặc định** | `0.0.0.0` |
| **Prefix API** | **`/api`** — `src/app.js` |
| **Prefix Admin** | **`/admin`** — `src/app.js` |
| **Health check** | `GET http://localhost:3000/api/health` |

**Biến môi trường (tên biến thật trong code — không ghi giá trị secret):**

| Biến | Mô tả | Nguồn |
|---|---|---|
| `NODE_ENV` | development / production | `src/config/env.js` |
| `BACKEND_HOST`, `BACKEND_PORT` (hoặc `HOST`, `PORT`) | Bind server | `src/index.js` |
| `JWT_SECRET`, `JWT_EXPIRES_IN` | Ký JWT user (default dev secret nếu không set) | `src/config/env.js`, `src/auth.js` |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL (default DB: `unudata`) | `src/db.js` |
| `DB_POOL_CONNECTION_LIMIT` | Pool mysql2 | `src/config/env.js` |
| `TRUST_PROXY` | Trust X-Forwarded-* | `src/config/env.js` |
| `RAG_BASE_URL`, `RAG_API_BASE` | URL FastAPI RAG (default `http://127.0.0.1:8001`) | `src/config/env.js` |
| `RAG_INTERNAL_API_KEY`, `RAG_ADMIN_API_KEY` | Header gọi RAG | `src/config/env.js`, `src/config/ragClient.js` |
| `RAG_FETCH_TIMEOUT_MS`, `RAG_FETCH_MAX_ATTEMPTS` | Timeout/retry RAG | `src/config/env.js` |
| `RAG_ADMIN_DEBUG_TIMEOUT_MS` | Timeout admin debug query | `src/config/env.js` |
| `HEALTHCHECK_SKIP_RAG` | Bỏ probe RAG trong `/api/health/ready` | `src/config/env.js` |
| `USE_V2_PLACE_TABLES` | Bật bảng v2 (default **false** local; Docker default **true**) | `src/config/env.js`, `docker-compose.yml` |
| `PLACE_ID_LEGACY_FALLBACK` | Fallback bảng `destinations` legacy | `src/config/env.js` |
| `AI_MODEL_URL`, `AI_MODEL_FETCH_TIMEOUT_MS` | LLM cục bộ tùy chọn (mặc định null) | `src/config/env.js` |
| `ADMIN_BASIC_USER`, `ADMIN_BASIC_PASS` | Basic Auth / login form admin | `src/middlewares/adminAuth.middleware.js` |
| `RAG_DEBUG` | Debug flag (cấm khi production) | `src/config/env.js` |

**File `.env`:** load từ **root repo** `UNUtrip_v2/.env` — `src/config/env.js` dòng 10.

**Lỗi thường gặp:**

- Port 3000 bận → log `[startup] Port 3000 is already in use` — `src/index.js`
- Production thiếu JWT/RAG keys → `assertSafeProductionConfig()` throw — `src/config/env.js`

---

### 4.3. Cấu hình và chạy FastAPI RAG Service

| Hạng mục | Giá trị |
|---|---|
| **Thư mục** | `backend/rag/` |
| **Tạo venv** | `python -m venv .venv` |
| **Kích hoạt (Windows)** | `.venv\Scripts\activate` |
| **Cài package** | `pip install -e ".[dev]"` |
| **Chạy service** | `uvicorn app.main:app --reload --port 8001` |
| **Port mặc định** | **8001** (Dockerfile, README, `.env.example`) |
| **Swagger docs** | `http://localhost:8001/docs` — ghi trong `docker-compose.yml` comment |

**Endpoint chính (Node proxy tới các path này):**

| Endpoint RAG | Node proxy tương ứng |
|---|---|
| `POST /rag/chat/simple` | `POST /api/ai/rag-chat` |
| `POST /ai/itinerary-preview` | `POST /api/ai/itinerary-preview` |
| `POST /ai/itinerary-options` | `POST /api/ai/itinerary-options` |
| `GET /health`, `GET /health/ready` | Probe từ `GET /api/health/ready` |

**Biến môi trường AI/RAG (tên thật):**

| Biến | Default trong **code** | Ghi chú |
|---|---|---|
| `AI_RUNTIME_MODE` | **`mock`** | `backend/rag/core/config.py` |
| `ENABLE_GEMINI` | **`false`** | `core/config.py` |
| `GEMINI_API_KEY` | `None` | Chỉ RAG đọc — `.env.example` |
| `GEMINI_MODEL` | `gemini-2.5-flash` | `core/config.py` |
| `RAG_ENV`, `RAG_LOG_LEVEL`, `RAG_DEBUG` | development, INFO, … | `core/config.py`, `core/security.py` |
| `RAG_INTERNAL_API_KEY`, `RAG_ADMIN_API_KEY` | optional | `core/security.py` |
| `RAG_ENABLE_RRF`, `RAG_ENABLE_VECTOR`, `RAG_ENABLE_RERANK` | true, false, true | `core/config.py` |
| `RAG_RATE_LIMIT_PER_MINUTE` | 120 | `core/config.py` |
| `REDIS_URL`, `REDIS_KEY_PREFIX` | None | `core/config.py` |
| `RAG_ARTIFACT_BUNDLE_URL`, `RAG_FETCH_ARTIFACTS_ON_START` | None, false | `core/config.py` |
| `RAG_READY_REQUIRES_INDEX` | true | Readiness cần index BM25 |

**Trạng thái mock vs model thật:**

| Cấu hình | Hành vi |
|---|---|
| Code default (`AI_RUNTIME_MODE=mock`, `ENABLE_GEMINI=false`) | Trả lời template mock, `model_used: "mock"` — `pipelines/policies/generation_router.py` |
| `.env.example` (`AI_RUNTIME_MODE=demo`, `ENABLE_GEMINI=true`) + `GEMINI_API_KEY` hợp lệ | Gọi Gemini khi mode ∈ `{demo, gemini_only, hybrid}` |
| Không có index BM25 | `/health/ready` có thể fail nếu `RAG_READY_REQUIRES_INDEX=true` — **CHƯA XÁC MINH** trạng thái index trên máy dev |

**Build index (cần cho RAG retrieval thật):**

```bash
cd backend/rag
python jobs/build_rag_artifacts.py --from-db   # hoặc --from-fixture cho CI
python scripts/verify_rag_artifacts.py
```

Nguồn: `README.md`, `backend/rag/README.md`.

---

### 4.4. Cấu hình và chạy ứng dụng Android

| Hạng mục | Giá trị |
|---|---|
| **Module** | `app/` (`settings.gradle`: `include ':app'`) |
| **Application ID** | `com.unutrip` (flavor `dev`: suffix `.dev`) |
| **BASE_URL config** | `app/build.gradle` đọc `API_BASE_URL` từ **`local.properties`** (root repo, gitignored) |
| **Default BASE_URL** | `http://10.0.2.2:3000/api/` (emulator → host loopback) |
| **Thiết bị thật / LAN** | Ghi `API_BASE_URL=http://<IP-máy-chạy-backend>:3000/api/` vào `local.properties` — `.env.example` dòng 126, `docs/v2/README_TOTAL_GUIDE.md` |
| **Flavor dev** | `usesCleartextTraffic=true` — cho phép HTTP — `app/src/dev/AndroidManifest.xml` |
| **Flavor prod** | `usesCleartextTraffic=false` — `app/src/prod/AndroidManifest.xml` |

**Quyền AndroidManifest (`app/src/main/AndroidManifest.xml`):**

- `INTERNET`
- `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`
- `CAMERA`
- `READ_EXTERNAL_STORAGE` (maxSdk 32), `WRITE_EXTERNAL_STORAGE` (maxSdk 29 — OSMDroid cache)

**Chạy bằng Android Studio:**

1. Mở project root `UNUtrip_v2/`
2. Tạo/sửa `local.properties`: `API_BASE_URL=...`
3. Chọn flavor **devDebug** (khuyến nghị cho HTTP local)
4. Run trên emulator hoặc thiết bị USB

**Màn hình chính:**

| Loại | Class | Route nav |
|---|---|---|
| Launcher | `AuthActivity` | — |
| Shell | `MainActivity` + Bottom Nav | — |
| Trang chủ | `HomeFragment` | `homeFragment` |
| Khám phá | `DestinationListFragment` | `destinationListFragment` |
| Chi tiết địa điểm | `DestinationDetailFragment` | `destinationDetailFragment` |
| Bản đồ | `MapFragment` | `mapFragment` |
| Lịch trình | `ItineraryFragment`, `ItineraryDetailFragment` | `itineraryFragment`, `itineraryDetailFragment` |
| AI lịch trình | `AIItineraryRequestFragment`, `AIItineraryOptionsFragment`, `AIItineraryEditorFragment` | nav graph |
| Chatbot | `ChatbotFragment` | `chatbotFragment` |
| Hồ sơ | `ProfileFragment`, `SettingsFragment` | `profileFragment`, `settingsFragment` |

Nguồn: `app/src/main/res/navigation/nav_graph.xml`, `app/src/main/java/com/unutrip/ui/`.

**Lưu ý:** Android **không** gọi Gemini SDK trực tiếp — comment trong `app/build.gradle` dòng 130; AI qua Node `/api/ai/*`.

---

### 4.5. Truy cập Dashboard Admin

| Hạng mục | Giá trị |
|---|---|
| **URL gốc** | `http://<host>:3000/admin/` → redirect dashboard |
| **Dashboard** | `GET /admin/dashboard` |
| **Login** | `GET /admin/login`, `POST /admin/auth/login`, `POST /admin/auth/logout` |

**Cơ chế xác thực (`src/middlewares/adminAuth.middleware.js`):**

| Điều kiện | Hành vi |
|---|---|
| **Cả `ADMIN_BASIC_USER` và `ADMIN_BASIC_PASS` đều set** | Yêu cầu cookie JWT `admin_session` (24h) **hoặc** HTTP Basic Auth. HTML chưa auth → redirect `/admin/login`. API JSON → 401. |
| **Thiếu một trong hai biến** | **Passthrough — không xác thực** (dev mode), log cảnh báo một lần. |

**Màn hình admin có trong code:**

| Route | Chức năng |
|---|---|
| `/admin/dashboard` | Tổng quan |
| `/admin/users` (+ api/save/delete) | Quản lý người dùng |
| `/admin/destinations` (+ api/save/delete) | Quản lý địa điểm |
| `/admin/reviews` (+ api/save/delete) | Quản lý đánh giá |
| `/admin/system` | Thông tin hệ thống |
| `/admin/rag-ai` (+ reload, clear-cache, metrics, logs, debug-query) | RAG AI Monitor |
| `/admin/ai-report` | Báo cáo AI |

Nguồn: `src/admin/index.js`, `tests/admin.router.test.js`.

---

## 5. Danh sách API/Endpoint chính

> Tất cả endpoint REST dưới prefix **`/api`**. Admin HTML dưới **`/admin`** (không JSON REST chuẩn).

### 5.1. Auth

| Method | Endpoint | Token | Request chính | Response chính | File liên quan |
|---|---|---|---|---|---|
| POST | `/api/auth/register` | Không | `{ fullName, email, password, phone? }` | `{ success, token, user }` | `modules/auth/auth.routes.js`, `auth.controller.js`, `users.repository.js` |
| POST | `/api/auth/login` | Không | `{ email, password }` | `{ success, token, user }` |同上 |
| POST | `/api/auth/logout` | **JWT Bearer** | — | `{ success, message }` | `auth.routes.js` |

### 5.2. User / Profile / Stats

| Method | Endpoint | Token | Request chính | Response chính | File liên quan |
|---|---|---|---|---|---|
| GET | `/api/users/profile` | JWT | — | `{ success, data: User }` | `modules/users/users.routes.js` |
| GET | `/api/users/stats` | JWT | — | Thống kê user | `users.routes.js` |
| PUT | `/api/users/profile` | JWT | User fields | User cập nhật | `users.controller.js` |
| PUT | `/api/users/preferences` | JWT | `{ preferences: string[] }` | User | `users.controller.js` |
| POST | `/api/users/avatar` | JWT | multipart `avatar` | User + avatar URL | `users.routes.js`, `upload.js` |

### 5.3. Destinations / Places

| Method | Endpoint | Token | Request chính | Response chính | File liên quan |
|---|---|---|---|---|---|
| GET | `/api/destinations` | Optional JWT | Query: page, limit, category, province, search, sort | Danh sách destination DTO | `destinations.routes.js`, `destinations.repository.js` |
| GET | `/api/destinations/featured` | Optional JWT | — | Featured list |同上 |
| GET | `/api/destinations/nearby` | Optional JWT | lat, lng, radiusKm, limit | Nearby list |同上 |
| GET | `/api/destinations/:id` | Optional JWT | — | Chi tiết + images | `destinationImages.repository.js` |

**Ghi chú:** Khi `USE_V2_PLACE_TABLES=true`, repository đọc `app_places`; legacy fallback `destinations` — `src/config/env.js`.

### 5.4. Favorites

| Method | Endpoint | Token | Request chính | Response chính | File liên quan |
|---|---|---|---|---|---|
| GET | `/api/users/favorites` | JWT | — | Danh sách destination yêu thích | `favorites.routes.js`, `favorites.repository.js` |
| POST | `/api/users/favorites` | JWT | `{ destinationId }` | OK |同上 |
| DELETE | `/api/users/favorites/:destinationId` | JWT | — | OK |同上 |

### 5.5. Reviews

| Method | Endpoint | Token | Request chính | Response chính | File liên quan |
|---|---|---|---|---|---|
| GET | `/api/destinations/:id/reviews` | JWT | — | Danh sách review | `reviews.routes.js`, `reviews.repository.js` |
| POST | `/api/reviews` | JWT | multipart: destinationId, rating, comment, images (≤3) | Review mới | `reviews.routes.js`, `upload.js` (5MB, jpeg/png/webp) |

### 5.6. Itineraries

| Method | Endpoint | Token | Request chính | Response chính | File liên quan |
|---|---|---|---|---|---|
| GET | `/api/itineraries` | JWT | — | Danh sách lịch trình | `itineraries.routes.js`, `itineraries.repository.js` |
| GET | `/api/itineraries/:id` | JWT | — | Chi tiết + days + items |同上 |
| POST | `/api/itineraries` | JWT | title, dates, … | Tạo mới | `itineraries.controller.js` |
| PUT | `/api/itineraries/:id` | JWT | metadata | Cập nhật |同上 |
| DELETE | `/api/itineraries/:id` | JWT | — | Xóa |同上 |
| POST | `/api/itineraries/:id/days` | JWT | day data | Thêm ngày |同上 |
| DELETE | `/api/itineraries/:id/days/:dayId` | JWT | — | Xóa ngày |同上 |
| POST | `/api/itineraries/:id/items` | JWT | item data | Thêm điểm dừng |同上 |
| PUT | `/api/itineraries/:id/items/:itemId` | JWT | item data | Sửa item |同上 |
| DELETE | `/api/itineraries/:id/items/:itemId` | JWT | — | Xóa item |同上 |
| POST | `/api/itineraries/save-ai` | JWT | AI itinerary payload | Lưu lịch trình AI | `itineraries.service.js` |
| POST | `/api/itineraries/create-from-option` | JWT | option payload | Tạo từ phương án AI | `ai.routes.js`, `ai.controller.js` |
| POST | `/api/itineraries/create-from-selection` | JWT | selection payload | Tạo từ lựa chọn AI |同上 |

### 5.7. AI / RAG (Node proxy → FastAPI)

| Method | Endpoint | Token | Request chính | Response chính | File liên quan |
|---|---|---|---|---|---|
| POST | `/api/ai/suggest-itinerary` | JWT | preferences[], startDate, endDate, budget?, startLocation? | Gợi ý lịch trình (logic Node + DB) | `ai.controller.js`, `ai.service.js` |
| POST | `/api/ai/rag-chat` | **Optional JWT** | `{ message }` | RAG chat normalized | `ai.routes.js` → RAG `/rag/chat/simple` |
| POST | `/api/ai/chat` | Optional JWT | `{ message }` | Chat (RAG fallback / AI_MODEL_URL) | `ai.controller.js` |
| POST | `/api/ai/itinerary-preview` | JWT | title, dates, budget, preferences, province | Preview từ RAG | `ai.service.js` → `/ai/itinerary-preview` |
| POST | `/api/ai/itinerary-options` | JWT | dates, preferences, … | Nhiều phương án tour | → `/ai/itinerary-options` |

### 5.8. Weather

| Method | Endpoint | Ghi chú |
|---|---|---|
| — | **Không có endpoint weather trên backend** | Android gọi trực tiếp `https://api.open-meteo.com/v1/forecast` — `WeatherService.kt` |

### 5.9. Health

| Method | Endpoint | Token | Response | File |
|---|---|---|---|---|
| GET | `/api/health` | Không | `{ success: true, … }` | `modules/health/health.routes.js` |
| GET | `/api/health/ready` | Không | DB + RAG readiness |同上 |

### 5.10. Admin (HTML + form POST — không phải REST `/api`)

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| GET | `/admin/dashboard` | Admin gate | Dashboard |
| GET/POST | `/admin/users`, `/admin/users/save`, … | Admin gate | CRUD users |
| GET/POST | `/admin/destinations`, … | Admin gate | CRUD địa điểm |
| GET/POST | `/admin/reviews`, … | Admin gate | CRUD reviews |
| GET | `/admin/system` | Admin gate | System info |
| GET/POST | `/admin/rag-ai/*` | Admin gate | RAG monitor, debug |
| GET | `/admin/ai-report` | Admin gate | AI report |

---

## 6. Danh sách giao diện cần chụp cho Chương 4

> Cột **Trạng thái ảnh** = có file ảnh báo cáo sẵn trong repo hay chưa (không phải trạng thái code).

### 6.1. Android

| Mã hình | Tên hình đề xuất | Màn hình / file | Dữ liệu cần chuẩn bị | Trạng thái ảnh |
|---|---|---|---|---|
| H01 | Đăng nhập | `AuthActivity` | Tài khoản demo (seed: `demo@unutrip.local`) | **CHƯA XÁC MINH** |
| H02 | Đăng ký | `AuthActivity` (tab/form đăng ký) | Email mới chưa tồn tại | **CHƯA XÁC MINH** |
| H03 | Trang chủ | `HomeFragment` | Backend + DB có destinations | **CHƯA XÁC MINH** |
| H04 | Danh sách / tìm kiếm địa điểm | `DestinationListFragment` | Nhiều địa điểm, thử search/filter | **CHƯA XÁC MINH** |
| H05 | Chi tiết địa điểm | `DestinationDetailFragment` | 1 địa điểm có ảnh, tọa độ | **CHƯA XÁC MINH** |
| H06 | Bản đồ / định vị | `MapFragment` | Tọa độ từ chi tiết địa điểm; cấp quyền location | **CHƯA XÁC MINH** |
| H07 | Thời tiết | `DestinationDetailFragment` (section weather) | Thành phố có trong map `cityCoords` | **CHƯA XÁC MINH** |
| H08 | Danh sách lịch trình | `ItineraryFragment` | User đã có ≥1 itinerary | **CHƯA XÁC MINH** |
| H09 | Chi tiết lịch trình | `ItineraryDetailFragment` | Itinerary nhiều ngày + items | **CHƯA XÁC MINH** |
| H10 | Gợi ý lịch trình AI | `AIItineraryRequestFragment` → `AIItineraryOptionsFragment` | Backend + RAG chạy; JWT hợp lệ | **CHƯA XÁC MINH** |
| H11 | Chỉnh tour AI | `AIItineraryEditorFragment` | Sau khi có options từ AI | **CHƯA XÁC MINH** |
| H12 | Chatbot tư vấn | `ChatbotFragment` | RAG/backend phản hồi | **CHƯA XÁC MINH** |
| H13 | Hồ sơ người dùng | `ProfileFragment` | User đã đăng nhập | **CHƯA XÁC MINH** |
| H14 | Yêu thích | `profileFavoriteListFragment` / list mode | ≥1 favorite | **CHƯA XÁC MINH** |
| H15 | Gửi / xem đánh giá | `DestinationDetailFragment` (reviews) | User JWT; destination hợp lệ | **CHƯA XÁC MINH** |
| H16 | Cài đặt | `SettingsFragment` | — | **CHƯA XÁC MINH** |

### 6.2. Admin

| Mã hình | Tên hình | Route | Dữ liệu cần chuẩn bị | Trạng thái ảnh |
|---|---|---|---|---|
| A01 | Dashboard admin | `/admin/dashboard` | Set `ADMIN_BASIC_*`; backend chạy | **CHƯA XÁC MINH** (có `diagram/Admin.png` — sơ đồ, không phải screenshot UI) |
| A02 | Quản lý người dùng | `/admin/users` | Có users trong DB | **CHƯA XÁC MINH** |
| A03 | Quản lý địa điểm | `/admin/destinations` | Có app_places/destinations | **CHƯA XÁC MINH** |
| A04 | Quản lý reviews | `/admin/reviews` | Có reviews | **CHƯA XÁC MINH** |
| A05 | RAG AI Monitor | `/admin/rag-ai` | RAG service chạy | **CHƯA XÁC MINH** |
| A06 | System | `/admin/system` | — | **CHƯA XÁC MINH** |

---

## 7. Biện pháp bảo vệ hệ thống đang có trong code

| Biện pháp | Mô tả triển khai thực tế | File/code liên quan | Mức độ | Ghi chú / hạn chế |
|---|---|---|---|---|
| JWT user API | Bearer token; `authMiddleware` / `optionalAuthMiddleware` | `src/auth.js`, các `*.routes.js` | **Đã có** | Default dev secret yếu nếu không set `JWT_SECRET` |
| Hash mật khẩu | bcrypt cost 10 khi register | `auth.controller.js` | **Đã có** | — |
| Middleware auth | JWT verify; optional cho guest browse/chat | `src/auth.js` | **Đã có** | `/api/ai/rag-chat`, `/api/ai/chat` cho phép guest |
| Validate input | Zod schema nhiều controller | `auth.controller.js`, `ai.controller.js`, … | **Đã có** | Một số endpoint validate thủ công (reviews) |
| CORS | `cors()` default, không whitelist tùy chỉnh | `src/app.js` | **Đã có** | **CHƯA XÁC MINH** cấu hình production |
| Helmet + CSP nonce | CSP với nonce per-request | `src/app.js`, `cspNonce.middleware.js` | **Đã có** | — |
| Morgan logging | Skip `/api/health`, `/favicon.ico` | `src/app.js` | **Đã có** | — |
| Biến môi trường `.env` | Load root `.env`; production guard | `src/config/env.js` | **Đã có** | `.env` gitignored |
| Android không truy cập DB trực tiếp | Chỉ HTTP qua Retrofit | `ApiService.kt`, `RetrofitClient.kt` | **Đã có** | — |
| Admin Basic Auth + session cookie | Khi `ADMIN_BASIC_USER/PASS` set | `adminAuth.middleware.js`, `adminSession.js` | **Một phần** | **Không auth khi thiếu env** — dev passthrough |
| Xử lý lỗi API | `errorHandler.middleware.js`; ẩn stack production | `middlewares/errorHandler.middleware.js` | **Đã có** | — |
| Giới hạn upload | 5MB; jpeg/jpg/png/webp; review max 3 ảnh | `upload.js`, `reviews.routes.js` | **Đã có** | — |
| JSON body limit | 2MB | `src/app.js` | **Đã có** | — |
| Kiểm soát API key AI | Gemini key chỉ ở RAG service; Node proxy qua RAG keys | `core/security.py`, `ragClient.js` | **Một phần** | Keys optional ở dev; production bắt buộc |
| Rate limit RAG | Per-IP `/rag/*`, `/ai/*` | `app/rate_limit_middleware.py` | **Đã có (RAG)** | Node API **CHƯA XÁC MINH** rate limit |
| Request ID | Header `X-Request-ID` | `requestId.middleware.js` | **Đã có** | — |
| Timing-safe compare | Admin credentials | `adminAuth.middleware.js` | **Đã có** | — |
| Session Android | Encrypted storage | `security-crypto`, `SessionManager.kt` | **Đã có** | **CHƯA XÁC MINH** chi tiết implementation |
| CSRF protection | — | — | **CHƯA XÁC MINH / không thấy** | Admin form POST SSR |
| Rate limit Node | — | — | **Không thấy trong src/** | — |

---

## 8. Dữ liệu thử nghiệm

| Loại dữ liệu | Nguồn trong repo | Giá trị / ghi chú |
|---|---|---|
| **User demo** | `backend/nodejs/src/seed.js` dòng 118–126 | Email: `demo@unutrip.local`; password plaintext trong seed: `"123456"` (hash bcrypt) — **chỉ dùng môi trường dev** |
| **Users giả hàng loạt** | `seed.js` | `user{N}@unutrip.local`, cùng password `"123456"` |
| **Admin test** | `.env.example` dòng 95–96 | Biến `ADMIN_BASIC_USER`, `ADMIN_BASIC_PASS` — **placeholder, không ghi giá trị thật** |
| **Destinations legacy** | `backend/nodejs/database.sql` | Nhiều INSERT (ví dụ Bãi Dài Cam Ranh, …) — dòng 128+ |
| **Destinations seed script** | `seed.js` `DESTINATIONS_DATA` | 50 địa điểm VN hardcoded |
| **Destinations JSON** | `backend/nodejs/src/data/destinations.json` | Nguồn mở rộng cho seed — **CHƯA XÁC MINH** số lượng record |
| **Reviews mẫu** | `seed.js` | 50 reviews random nếu chạy seed |
| **Itineraries mẫu** | `seed.js` | 100 itineraries random |
| **Favorites mẫu** | — | **CHƯA XÁC MINH** — không có seed favorites trong `seed.js` |
| **RAG knowledge** | `database/migrations/009_populate_rag_knowledge_base.sql` | Populate từ legacy — cần bảng nguồn |
| **RAG artifacts** | `backend/rag/data/indexes/rag_artifacts_manifest.json` | Manifest tracked; `bm25_index.pkl` gitignored |
| **Ảnh địa điểm** | `place_images` migration 008; URLs trong `database.sql` | URL external trong SQL legacy |
| **Tọa độ thời tiết** | `WeatherService.kt` `cityCoords` | Default fallback Hà Nội `(21.0285, 105.8542)` nếu không khớp tên thành phố |

**Cách tạo dữ liệu demo:**

| Cách | Lệnh / thao tác | Trạng thái |
|---|---|---|
| Docker bootstrap | `docker compose up` + `DATABASE_BOOTSTRAP_LEGACY=true` | Import `database.sql` + migrations |
| Seed Node | **CHƯA XÁC MINH** lệnh chính thức — export `seed()` trong `seed.js` nhưng không wired vào npm | Cần xác nhận team |
| Bridge dev | `database/quick_populate_app_places_from_legacy_database_sql.sql` | Copy `destinations` → `app_places` |

---

## 9. Kịch bản thử nghiệm chức năng

> **Kết quả thực tế E2E:** **CHƯA XÁC MINH** (chưa chạy demo thủ công trong phiên này).  
> **Test tự động backend:** chạy `npm test` tại `backend/nodejs` → **48 pass / 4 fail / 52 total** (2026-05-21).

| Mã TC | Chức năng | Điều kiện trước | Các bước | Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| TC01 | Đăng ký | Backend + MySQL chạy | POST register từ app hoặc API | email mới, password ≥4 | 200, token + user | **CHƯA XÁC MINH** E2E; unit test register mock pass | **Chưa xác minh** | `tests/auth.routes.test.js` |
| TC02 | Đăng nhập | User tồn tại | POST login | email + password đúng | 200, token | **CHƯA XÁC MINH** E2E; unit test pass | **Chưa xác minh** | Seed demo user nếu đã chạy seed |
| TC03 | Xem danh sách địa điểm | DB có places | GET `/api/destinations` hoặc màn Khám phá | page=1 | Danh sách không rỗng | **CHƯA XÁC MINH** | **Chưa xác minh** | Guest test: `destinations-guest.test.js` |
| TC04 | Chi tiết địa điểm | id hợp lệ | GET `/api/destinations/:id` | id=1 (nếu có) | Chi tiết + ảnh | **CHƯA XÁC MINH** | **Chưa xác minh** | — |
| TC05 | Thêm/bỏ yêu thích | JWT hợp lệ | POST + DELETE favorites | destinationId | 200 OK | **CHƯA XÁC MINH** | **Chưa xác minh** | Không có test file riêng |
| TC06 | Gửi đánh giá | JWT; destination tồn tại | POST `/api/reviews` | rating 0–5, comment | Review lưu DB | **CHƯA XÁC MINH** | **Chưa xác minh** | Max 3 ảnh |
| TC07 | Tạo lịch trình thủ công | JWT | POST `/api/itineraries` từ app | title, dates | Itinerary mới | **CHƯA XÁC MINH** | **Chưa xác minh** | UI: dialog trong `ItineraryFragment` |
| TC08 | Xem/xóa lịch trình | Có itinerary | GET + DELETE | itinerary id | Hiển thị / xóa thành công | **CHƯA XÁC MINH** | **Chưa xác minh** | — |
| TC09 | Gợi ý lịch trình AI/RAG | JWT; RAG chạy | AI flow: preview/options | dates, preferences | Options trả về | **CHƯA XÁC MINH** | **Chưa xác minh** | Phụ thuộc RAG index + mode |
| TC10 | Chatbot RAG | Backend + RAG | POST `/api/ai/rag-chat` | message text | Answer + sources | Unit test JWT pass; guest **CHƯA XÁC MINH** | **Chưa xác minh** | Route dùng `optionalAuthMiddleware` |
| TC11 | Xem bản đồ | App cài; có tọa độ địa điểm | Mở MapFragment | lat, lng args | Map hiển thị marker | **CHƯA XÁC MINH** | **Chưa xác minh** | Cần quyền location cho nút "vị trí tôi" |
| TC12 | Xem thời tiết | Internet | Mở chi tiết địa điểm | city name | Open-Meteo data | **CHƯA XÁC MINH** | **Chưa xác minh** | Fallback Hà Nội nếu city không khớp |
| TC13 | Hồ sơ / thống kê | JWT | ProfileFragment; GET stats | — | Profile + stats | **CHƯA XÁC MINH** | **Chưa xác minh** | — |
| TC14 | Admin dashboard | Backend; admin auth | Truy cập `/admin/dashboard` | ADMIN_BASIC_* | HTML dashboard | Admin route test pass; UI **CHƯA XÁC MINH** | **Chưa xác minh** | Dev mode không auth nếu thiếu env |
| TC15 | Admin RAG monitor | RAG chạy | `/admin/rag-ai` | — | Metrics/logs | **CHƯA XÁC MINH** | **Chưa xác minh** | — |

**4 test backend fail (không phải E2E):**

1. `adminAuth.middleware.test.js` — dev passthrough warning (2 case)
2. `ai-rag-chat.route.test.js` — test kỳ vọng 401 không auth nhưng route thực tế cho phép guest (`optionalAuthMiddleware`)
3. `env.v2PlaceFlags.test.js` — legacy fallback default

---

## 10. Checklist chạy demo tổng hợp

| # | Bước | Lệnh / thao tác | Kết quả cần thấy | Lỗi thường gặp |
|---|---|---|---|---|
| 1 | Bật MySQL | XAMPP MySQL **hoặc** `docker compose up mysql` | Port 3306 listen | Connection refused → kiểm tra `DB_HOST` |
| 2 | Import / migrate DB | `bash database/scripts/run_migrations.sh` hoặc Docker `db-migrate` | Bảng `users`, `app_places` tồn tại | Thiếu legacy → skip 006–009 (log script) |
| 3 | Copy env | `cp .env.example .env`; điền `JWT_SECRET`, `GEMINI_API_KEY` (placeholder) | File `.env` ở root repo | Node load sai path nếu đặt env trong `backend/nodejs/` only |
| 4 | Chạy backend | `cd backend/nodejs && npm ci && npm run dev` | Log `UNUtrip backend running on http://0.0.0.0:3000` | `EADDRINUSE` port 3000 — `src/index.js` |
| 5 | Chạy RAG | `cd backend/rag && pip install -e ".[dev]" && uvicorn app.main:app --port 8001` | `GET http://127.0.0.1:8001/health` 200 | `/health/ready` fail nếu thiếu BM25 index |
| 6 | Build index RAG (nếu cần) | `python jobs/build_rag_artifacts.py --from-db` | `verify_rag_artifacts.py` pass | **CHƯA XÁC MINH** DB đủ dữ liệu RAG |
| 7 | Cấu hình Android | `local.properties`: `API_BASE_URL=http://10.0.2.2:3000/api/` | BuildConfig.BASE_URL đúng | Thiết bị thật cần IP LAN, flavor dev |
| 8 | Chạy Android | Android Studio → Run `devDebug` | `AuthActivity` hiển thị | Cleartext blocked → dùng flavor dev |
| 9 | Đăng nhập | Login demo user (nếu đã seed) | Vào `MainActivity` | 401 nếu user chưa tồn tại trong DB |
| 10 | Demo destination | Tab Khám phá | List + detail | List rỗng → DB chưa có places / sai `USE_V2_PLACE_TABLES` |
| 11 | Demo map/weather | Chi tiết → Map; xem weather section | OSM map; nhiệt độ Open-Meteo | Weather fallback Hà Nội nếu city không map |
| 12 | Demo itinerary | Tab Lịch trình; tạo mới | CRUD lịch trình | **CHƯA XÁC MINH** |
| 13 | Demo AI/RAG | AI gợi ý tour / chatbot | Phản hồi AI (mock hoặc Gemini) | 502 nếu RAG down; mock nếu `AI_RUNTIME_MODE=mock` |
| 14 | Demo admin | `http://localhost:3000/admin/dashboard` | Dashboard HTML | Không auth ở dev nếu chưa set `ADMIN_BASIC_*` |

---

## 11. Hạn chế triển khai hiện tại

| Hạn chế | Bằng chứng code |
|---|---|
| **AI mặc định mock trong code RAG** | `AI_RUNTIME_MODE` default `"mock"` — `backend/rag/core/config.py`; `.env.example` khuyến nghị `demo` |
| **Gemini tắt mặc định** | `ENABLE_GEMINI=false` — `core/config.py` |
| **RAG cần dataset/index** | `RAG_READY_REQUIRES_INDEX=true`; `bm25_index.pkl` gitignored — `README.md` |
| **Hai schema địa điểm song song** | Legacy `destinations` vs v2 `app_places`; flag `USE_V2_PLACE_TABLES` — `env.js` |
| **Bảng `rag_places`, `destination_images` không có CREATE trong repo** | Chỉ populate/validation — migrations 006–010 |
| **Seed Node không tự chạy** | `index.js` không gọi `seed()` |
| **Admin không bảo mật khi thiếu env** | Passthrough — `adminAuth.middleware.js` |
| **Weather fallback tọa độ Hà Nội** | `WeatherService.kt` dòng 49: `Pair(21.0285, 105.8542)` |
| **Weather map thành phố hữu hạn** | Chỉ các key trong `cityCoords` — không geocode động (comment Nominatim nhưng **CHƯA XÁC MINH** code gọi Nominatim) |
| **Map phụ thuộc quyền vị trí cho "current location"** | `MapFragment.kt` request `ACCESS_FINE_LOCATION` |
| **Docker Compose có stack đầy đủ** | `docker-compose.yml`: mysql, redis, rag, backend — **CHƯA XÁC MINH** Android trong compose |
| **Chỉnh sửa lịch trình UI** | Có `EditItineraryDialog`, `AIItineraryEditorFragment`, API PUT items — **CHƯA XÁC MINH** mức hoàn thiện UX |
| **4/52 backend unit test fail** | Chạy local 2026-05-21 — mismatch test vs code (rag-chat guest, admin warning) |
| **Postman collection không có** | Không file trong repo |
| **Node không rate-limit API** | Không middleware rate limit trong `src/` |

---

## 12. Hướng phát triển

*(Suy ra từ hạn chế đã xác minh — không phải roadmap chính thức)*

| Hướng | Lý do (từ hạn chế thực tế) |
|---|---|
| Bật model AI thật ổn định | Set `AI_RUNTIME_MODE=demo/hybrid`, `ENABLE_GEMINI=true`, key hợp lệ |
| Hoàn thiện RAG/dataset | Build/fetch BM25 artifacts; populate `rag_knowledge_base` |
| Chuẩn hóa v2 places | `USE_V2_PLACE_TABLES=true`, migrate hết khỏi `destinations` |
| Bảo mật admin production | Bắt buộc `ADMIN_BASIC_*` hoặc session; không passthrough |
| HTTPS / production deploy | `assertSafeProductionConfig()` yêu cầu secrets mạnh — `env.js` |
| Rate limit Node API | Hiện chỉ RAG có rate limit |
| Geocoding thời tiết động | Giảm fallback Hà Nội cố định |
| Test tự động E2E | Bổ sung integration test + sửa 4 test fail |
| Mở rộng dữ liệu du lịch | Import dumps vào `database/dumps/` |
| Docker artifact mount | Uncomment volume RAG data trong `docker-compose.yml` |

---

## 13. Kết luận dữ liệu dùng cho Chương 4

| Thành phần | Đủ dữ liệu viết báo cáo? | Cần chụp hình? | Cần test thêm? | Cần xác nhận từ team |
|---|---|---|---|---|
| Kiến trúc tổng thể | **Có** — README, docker-compose, AGENT_GUIDE | Sơ đồ kiến trúc (có `diagram/`, `docs/diagrams/`) | — | — |
| Backend API | **Có** — routes, controllers, tests | — | E2E manual TC01–TC15 | DB demo thực tế đang dùng |
| Android UI | **Có** — nav graph, fragments | **Có** — H01–H16 | Chạy app trên emulator/device | BASE_URL máy demo |
| MySQL schema | **Có** — migrations + legacy SQL | ERD (nếu có) | Import/migrate trên máy báo cáo | Dump SQL lớn trong `database/dumps/` |
| RAG/AI | **Có** — endpoints, config, modes | A05 RAG monitor | TC09, TC10 với Gemini thật | Index BM25 đã build chưa |
| Admin | **Có** — 26 routes | A01–A06 | TC14, TC15 | Credentials admin demo |
| Bảo mật | **Có** — JWT, bcrypt, helmet, hạn chế admin dev | — | Pentest **CHƯA XÁC MINH** | Chính sách production |
| Thử nghiệm | **Một phần** — 48 unit test pass | Screenshot kết quả test | Toàn bộ E2E TC01–TC15 | Kết quả "Đạt/Không đạt" thực tế |

**Tóm lắt:** Repo cung cấp đủ bằng chứng kỹ thuật để viết **mô tả triển khai, cấu hình, API, bảo mật và kịch bản test** cho Chương 4. Các mục **kết quả thực nghiệm E2E, ảnh chụp màn hình app/admin, và trạng thái DB demo** cần team chạy hệ thống và bổ sung — hiện ghi **CHƯA XÁC MINH**.

---

*Tài liệu tạo từ codebase `UNUtrip_v2` — không sửa mã nguồn. Cập nhật: 2026-05-21.*
