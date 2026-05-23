# Dữ liệu kỹ thuật vẽ sơ đồ thiết kế hệ thống — UNUTrip (Chương 3)

> Trích xuất **READ-ONLY** từ codebase. Mọi kết luận có đường dẫn file chứng minh.  
> Không sửa code. Không đoán. Chỗ không thấy trong project ghi: **CHƯA XÁC ĐỊNH / KHÔNG TÌM THẤY TRONG PROJECT**.

---

# PHẦN 1 — TÓM TẮT NGẮN ĐỂ VẼ SƠ ĐỒ

## Sơ đồ 1 — Kiến trúc UML 3 lớp

**Thành phần cần vẽ**
- **Presentation:** Android (Kotlin/XML/ViewBinding), Admin Dashboard (HTML server-side Express)
- **Business:** Node.js Express (`/api`, `/admin`), FastAPI RAG (`backend/rag`, port 8001)
- **Data:** MySQL (`unudata`), file RAG (BM25, JSONL, JSON places, cache Gemini)

**Quan hệ chính:** Android/Admin → Node → MySQL; Node → FastAPI RAG → file index; Android → Open-Meteo/OSMDroid trực tiếp

**Nhánh lỗi:** FastAPI lỗi → Node 502; Android chat RAG lỗi → fallback qua `/api/ai/chat`

**Ghi chú:** Không vẽ Android → FastAPI trực tiếp. `GeminiService` trên Android thực chất gọi Node `/api/ai/chat`, không gọi Gemini SDK trực tiếp.

---

## Sơ đồ 2 — Client-Server + AI/RAG

**Nodes:** Android | Admin Web | Node.js | FastAPI RAG | MySQL | Open-Meteo | OSM tiles | Google Maps (intent ngoài app) | Gemini API (trong FastAPI)

**Luồng chính:** Android → Retrofit → `http://…:3000/api/*` → Node → MySQL / FastAPI `:8001`

**Weather:** Android → `api.open-meteo.com` trực tiếp (`WeatherService.kt`)

**Map:** Android OSMDroid + tile OpenStreetMap; chỉ đường/mở ngoài → Google Maps intent

**RAG runtime:** FastAPI đọc **file/index**, không đọc MySQL runtime

**Gemini:** Chủ yếu trong FastAPI `GenerationRouter`; Android prepare/validate/repair qua Node `/api/ai/chat` (có thể kích hoạt RAG/Gemini gián tiếp)

---

## Sơ đồ 3 — CSDL rút gọn

**Bảng runtime chính:** `users`, `app_places`, `place_images`, `favorites`, `reviews`, `itineraries`, `itinerary_days`, `itinerary_items`, `place_id_map`

**Legacy (migration/fallback):** `destinations`, `destination_images`, `rag_places`

**RAG MySQL:** `rag_knowledge_base` — dùng export/build, **không** query runtime FastAPI

**FK thực tế:** `favorites.destination_id`, `reviews.destination_id` join `app_places.id` tại runtime; schema legacy FK vẫn trỏ `destinations`

---

## Sơ đồ 4 — Luồng Chatbot AI/RAG

**Luồng chính (10 bước):**
User → `ChatbotFragment` → `ChatbotViewModel.getFinalChatbotResult()` → `GeminiService.prepareRagQuery()` (Node `/api/ai/chat`) → `RagService.chat()` (Node `/api/ai/rag-chat`) → FastAPI `/rag/chat/simple` → BM25+template/Gemini → trả về → `GeminiService.validateRagOutputFull()` → (retry RAG nếu invalid) → `GeminiService.repairRagAnswer()` hoặc `fallbackChat()`

**Nhánh lỗi:** RAG fail → `fallbackChat`; province mismatch → retry strict query hoặc thông báo; validate fail → retry hoặc thông báo

---

## Sơ đồ 5 — Luồng gợi ý lịch trình AI/RAG

**Luồng A (tạo options):** `AIItineraryRequestFragment` → `POST /api/ai/itinerary-options` → Node proxy → FastAPI `/ai/itinerary-options` → scoring + 4 template options từ file places

**Luồng B (lưu itinerary):** `AIItineraryOptionsFragment` → (tùy chọn) `AIItineraryEditorFragment` → `POST /api/itineraries/create-from-option` → `place_id_map` resolve → insert `itineraries` + `itinerary_days` + `itinerary_items`

**Nhánh lỗi:** thiếu title/date → Toast Android; RAG 502 → error; không map được ID → 400 `no_mapped_destinations`; item không map → **skip** (continue), không fail toàn bộ nếu còn item map được

---

## Sơ đồ 6 — Bản đồ, định vị, thời tiết

**Map:** `DestinationDetailFragment` → nav `MapFragment` (lat/lon từ API `app_places`) → OSMDroid marker + FusedLocation marker user

**Weather:** `DestinationDetailFragment.loadWeather(city)` → `WeatherService.getWeather(cityName)` → city mapping cứng → Open-Meteo

**Location:** `HomeFragment` FusedLocation → `GET /api/destinations/nearby`; `MapFragment` FusedLocation `lastLocation`

**Backend:** **KHÔNG** có endpoint weather/map

---

## Sơ đồ 7 — Bản đồ và thời tiết (rút gọn)

Hai nhánh từ **Chi tiết địa điểm:**
- **Bản đồ:** lat/lon từ Destination API → OSMDroid in-app; nút mở Google Maps / chỉ đường ngoài app
- **Thời tiết:** city name → mapping tọa độ → Open-Meteo → hiển thị card; lỗi → ẩn card

---

# PHẦN 2 — DỮ LIỆU CHI TIẾT CÓ FILE CHỨNG MINH

---

## A. DỮ LIỆU CHUNG

### 1. Android app

| Hạng mục | Kết quả | File chứng minh |
|---|---|---|
| Ngôn ngữ | **Kotlin 100%** (0 file `.java` trong `app/`) | `E:/UNUtrip_v2/app/src/main/java/com/unutrip/` |
| UI | **XML + ViewBinding** (35 layout); Compose chỉ theme preview | `E:/UNUtrip_v2/app/build.gradle` L57-61; `app/src/main/res/layout/` |
| Activities | `AuthActivity` (launcher), `MainActivity` (shell) | `app/src/main/java/com/unutrip/ui/auth/AuthActivity.kt`, `ui/home/MainActivity.kt` |
| Fragments chính | Home, DestinationList/Detail/Map, Itinerary*, Chatbot, Profile, Settings | `app/src/main/res/navigation/nav_graph.xml` |
| Navigation Component | **Có** + Safe Args + bottom nav 5 tab | `nav_graph.xml`, `activity_main.xml`, `bottom_nav_menu.xml` |
| Retrofit/OkHttp/Gson | **Có** | `app/src/main/java/com/unutrip/data/api/RetrofitClient.kt` L74-80; `build.gradle` |
| ViewModel/LiveData/Repository | **Có** | `viewmodel/*.kt`, `data/repository/Repositories.kt` |
| SessionManager/JWT | **EncryptedSharedPreferences**, key `auth_token` | `app/src/main/java/com/unutrip/utils/SessionManager.kt` L119-130 |
| Base URL | Default `http://10.0.2.2:3000/api/`; override `API_BASE_URL` trong `local.properties` | `app/build.gradle` L13-18, L32-33 |
| API chính | `ApiService.kt` | `app/src/main/java/com/unutrip/data/api/ApiService.kt` |

### 2. Backend Node.js

| Hạng mục | Kết quả | File chứng minh |
|---|---|---|
| Framework | **Express 4.x** | `backend/nodejs/package.json`; `src/app.js` |
| Entry | `src/index.js` (listen), `src/app.js` (factory) | `src/index.js`, `src/app.js` |
| API prefix | **`/api`** | `src/app.js` L87 |
| Admin route | **`/admin`** + `adminAuthMiddleware` | `src/app.js` L88 |
| Cấu trúc | `modules/*/*.routes.js` + `*.controller.js` → `services/` → `repositories/` | `src/api/router.js`, `src/services/`, `src/repositories/` |
| Auth JWT API | `src/auth.js` (`authMiddleware`, `signToken`) | `src/auth.js` |
| Auth Admin | Cookie JWT `admin_session` hoặc HTTP Basic | `src/middlewares/adminAuth.middleware.js`, `src/admin/_shared/adminSession.js` |
| Config env | `src/config/env.js` (load `.env` repo root) | `src/config/env.js` L9-10 |
| DB config | `src/db.js` | `src/db.js` L7 |

### 3. FastAPI RAG

| Hạng mục | Kết quả | File chứng minh |
|---|---|---|
| Thư mục | `E:/UNUtrip_v2/backend/rag` | `backend/rag/app/main.py` |
| Port mặc định | **8001** | `backend/rag/Dockerfile`; `backend/nodejs/src/config/env.js` L28-31 |
| Endpoint chatbot | `/rag/chat/simple`, `/rag/chat`, `/rag/retrieve` (+ prefix `/v1`) | `backend/rag/app/routers/rag.py` |
| Endpoint itinerary | `/ai/itinerary-options`, `/ai/itinerary-preview` | `backend/rag/app/routers/ai_itinerary.py` |
| Runtime mode mock/fallback | **Có** — `AI_RUNTIME_MODE` default `"mock"` | `backend/rag/core/config.py` L96; `pipelines/policies/generation_router.py` |
| Gemini trong FastAPI | **Có** — `GeminiProvider.generate()` khi mode `demo`/`gemini_only`/`hybrid` | `backend/rag/providers/gemini_provider.py`, `generation_router.py` L49-55 |
| prepare query / repair trong FastAPI | **KHÔNG TÌM THẤY** (grep zero match `prepare`, `repair`) | `backend/rag/` |
| validate LLM output trong FastAPI | **KHÔNG** — chỉ Pydantic contract response | `backend/rag/domain/contracts/rag_chat_simple.py` |
| RAG đọc MySQL runtime | **KHÔNG** — chỉ file/index; MySQL trong script export | `backend/rag/scripts/export_*.py`; `tests/retrieval/test_place_store.py` |

### 4. Database

| Hạng mục | Kết quả | File chứng minh |
|---|---|---|
| DB engine | **MySQL** (mysql2, docker mysql:8.0) | `backend/nodejs/src/db.js`; `docker-compose.yml` |
| Tên DB mặc định | **`unudata`** | `backend/nodejs/src/db.js` L7; `.env.example` |
| Schema chính thức | `database/migrations/001-011` | `E:/UNUtrip_v2/database/migrations/` |
| Legacy bootstrap | `backend/nodejs/database.sql` (deprecated) | `backend/nodejs/DATABASE_LEGACY.md` |
| Bảng địa điểm runtime | **`app_places`** | `backend/nodejs/src/repositories/destinations.repository.js` L38 |
| Bảng ảnh runtime | **`place_images`** | `backend/nodejs/src/repositories/destinationImages.repository.js` |
| `place_id_map` | **Có** | `database/migrations/004_create_place_id_map.sql` |
| RAG runtime MySQL | **Không** — FastAPI dùng file; bảng `rag_knowledge_base` cho export | `database/migrations/002_create_rag_knowledge_base.sql`; RAG scripts |

### 5. External services

| Hạng mục | Kết quả | File chứng minh |
|---|---|---|
| Bản đồ in-app | **OSMDroid + OpenStreetMap (MAPNIK tiles)** | `MapFragment.kt` L99; `fragment_map.xml` L8-16 |
| Google Maps | Chỉ **intent ngoài app** (không SDK in-app) | `MapIntentHelper.kt`; `AndroidManifest.xml` L32 |
| Định vị | **FusedLocationProviderClient** | `HomeFragment.kt` L272; `MapFragment.kt` L132-143 |
| Thời tiết | **Open-Meteo** `api.open-meteo.com` | `WeatherService.kt` L52-56 |
| Weather qua backend | **KHÔNG** — Android gọi trực tiếp | `WeatherService.kt`; grep `weather` trong `backend/nodejs/src` = 0 |
| Map qua backend | **KHÔNG** tile/map API; có `GET /api/destinations/nearby` (geo query DB) | `destinations.routes.js` L12 |

---

## B. SƠ ĐỒ 1 — UML 3 LỚP

### Bảng thành phần theo lớp

| Lớp | Thành phần | Vai trò | File chứng minh |
|---|---|---|---|
| **Presentation** | Android App (Fragments, ViewModels) | UI người dùng: duyệt địa điểm, lịch trình, chatbot, profile | `app/src/main/java/com/unutrip/ui/` |
| **Presentation** | Admin Dashboard (HTML) | Quản trị users, places, reviews, RAG status | `backend/nodejs/src/admin/templates/`, `admin/index.js` |
| **Presentation** | OSMDroid MapView | Hiển thị bản đồ in-app | `MapFragment.kt`, `fragment_map.xml` |
| **Presentation** | WeatherService (Android) | Gọi Open-Meteo, hiển thị card thời tiết | `WeatherService.kt`, `DestinationDetailFragment.kt` L169-196 |
| **Business** | Node.js Express `/api` | Auth, users, destinations, favorites, reviews, itineraries, AI proxy | `src/api/router.js`, `src/modules/` |
| **Business** | Node.js `/admin` | Admin auth, CRUD, RAG admin proxy | `src/app.js` L88, `src/admin/` |
| **Business** | FastAPI RAG Service | Retrieve BM25, generate answer, itinerary options | `backend/rag/app/main.py`, `pipelines/rag_pipeline.py` |
| **Business** | Gemini (trong FastAPI) | Generate RAG answer khi runtime mode phù hợp | `generation_router.py`, `gemini_provider.py` |
| **Business** | Android GeminiService logic | prepare/validate/repair query qua Node `/api/ai/chat` | `GeminiService.kt`, `ChatbotViewModel.kt` |
| **Data** | MySQL `unudata` | Users, places, favorites, reviews, itineraries, place_id_map | `database/migrations/`, `src/repositories/` |
| **Data** | RAG file store | BM25 index, corpus JSONL, places JSON, embedding NPZ, Gemini cache | `backend/rag/core/config.py`, `data/indexes/`, `data/processed/` |
| **External** | Open-Meteo API | Thời tiết | `WeatherService.kt` |
| **External** | OpenStreetMap tiles | Tile bản đồ OSMDroid | `MapFragment.kt` L99 |
| **External** | Google Maps (browser/app) | Mở ngoài app, chỉ đường | `MapIntentHelper.kt` |
| **External** | Gemini API (Google) | LLM generation trong FastAPI | `backend/rag/llm/gemini_generator.py` |

### Bảng quan hệ/kết nối

| Từ | Đến | Kiểu | Mô tả | File chứng minh |
|---|---|---|---|---|
| Android | Node.js | HTTP/Retrofit JWT | REST `/api/*` | `RetrofitClient.kt`, `ApiService.kt` |
| Android | Open-Meteo | HTTPS trực tiếp | Weather forecast | `WeatherService.kt` |
| Android | OSM tile server | HTTPS (OSMDroid) | Map tiles | `MapFragment.kt` |
| Android | Google Maps | Intent ACTION_VIEW | Mở/chỉ đường ngoài app | `MapIntentHelper.kt` |
| Admin Web | Node.js | HTTP cookie/Basic | `/admin/*` HTML + API | `admin/index.js`, `app.js` |
| Node.js | MySQL | mysql2 pool | CRUD nghiệp vụ | `src/db.js`, repositories |
| Node.js | FastAPI RAG | HTTP fetch + `X-RAG-Internal-Key` | Proxy AI/RAG | `src/lib/ragUpstream.js`, `src/services/ai.service.js` |
| Admin Node | FastAPI RAG | HTTP `/admin/*` | RAG ops, metrics | `src/admin/_shared/ragHttp.js` |
| FastAPI RAG | File index/corpus | File I/O | BM25, places JSON | `hybrid_retriever.py`, `place_store.py` |
| FastAPI RAG | Gemini API | HTTPS | Generate answer | `gemini_generator.py` |

---

## C. SƠ ĐỒ 2 — CLIENT-SERVER + AI/RAG

| Nguồn | Đích | Giao thức | Endpoint/path | Vai trò | File chứng minh |
|---|---|---|---|---|---|
| Android | Node.js | HTTP REST | `/api/auth/*`, `/api/destinations/*`, … | Nghiệp vụ chính | `ApiService.kt` |
| Android | Node.js | POST | `/api/ai/rag-chat` | Chatbot RAG | `ApiService.kt` L222; `RagService.kt` |
| Android | Node.js | POST | `/api/ai/chat` | Fallback + prepare/validate/repair | `ApiService.kt` L227; `GeminiService.kt` |
| Android | Node.js | POST | `/api/ai/itinerary-options` | Lấy tour AI options | `ApiService.kt` L232; `ItineraryViewModel.kt` L312 |
| Android | Node.js | POST | `/api/itineraries/create-from-option` | Lưu itinerary | `ApiService.kt` L238; `ItineraryViewModel.kt` L344 |
| Android | Open-Meteo | HTTPS | `api.open-meteo.com/v1/forecast` | Thời tiết | `WeatherService.kt` L52-56 |
| Android | OSM (via OSMDroid) | HTTPS tiles | MAPNIK tile source | Bản đồ in-app | `MapFragment.kt` L99 |
| Android | Google Maps | Intent | `google.com/maps`, `google.navigation:` | Map ngoài app | `MapIntentHelper.kt` |
| Node.js | MySQL | SQL | — | Persistence | `src/db.js` |
| Node.js | FastAPI | POST | `/rag/chat/simple` | RAG chat proxy | `ai.service.js` L51 |
| Node.js | FastAPI | POST | `/rag/chat` | suggest-itinerary fallback | `ai.service.js` L194 |
| Node.js | FastAPI | POST | `/ai/itinerary-options` | Itinerary options | `ai.service.js` L33 |
| Node.js | FastAPI | GET | `/health/ready` | Health probe | `health.controller.js` |
| FastAPI | BM25/corpus/places files | File | `data/indexes/bm25_index.pkl`, `places_rag_documents.jsonl`, `places_app.json` | RAG knowledge | `core/config.py` |
| FastAPI | Gemini API | HTTPS | — | LLM generation | `gemini_generator.py` |
| Admin Dashboard | Node.js | HTTP | `/admin/dashboard`, `/admin/rag-ai`, … | Quản trị | `admin/index.js` |
| Admin Dashboard | FastAPI | **Gián tiếp qua Node** | `/admin/rag/*` proxy | RAG admin | `admin/ragAi.admin.routes.js`, `ragHttp.js` |

**Xác nhận:**
- **Weather:** Android → Open-Meteo **trực tiếp** (không qua backend)
- **Map tiles:** Android → OSMDroid/OSM **trực tiếp**; backend chỉ cung cấp lat/lon qua destinations API
- **RAG runtime MySQL:** **Không** — dùng file/index
- **Gemini:** **FastAPI** (generation); Android **không** gọi Gemini SDK trực tiếp (`GEMINI_API_KEY` có trong `BuildConfig` nhưng **không thấy** code Android gọi Gemini API — `GeminiService.kt` chỉ gọi Node)

---

## D. SƠ ĐỒ 3 — CSDL RÚT GỌN

### Bảng

| Bảng | Vai trò | PK | FK chính | Cột quan trọng | Runtime? | File chứng minh |
|---|---|---|---|---|---|---|
| `users` | Tài khoản | `id` | — | email, password_hash, full_name | **Có** | `database.sql` L13-23; `users.repository.js` |
| `app_places` | Catalog địa điểm v2 | `id` | — | place_key, name, lat/lng, category, rating | **Có (chính)** | `001_create_app_places.sql`; `destinations.repository.js` L38 |
| `destinations` | Legacy catalog | `id` | — | name, lat/lng, … | **Legacy/fallback** | `database.sql`; `placeIdMap.repository.js`; `seed.js` |
| `place_images` | Ảnh địa điểm v2 | `id` | `app_place_id`→`app_places` | image_url, is_primary, status | **Có** | `003_create_place_images.sql`; `destinationImages.repository.js` |
| `destination_images` | Legacy ảnh | `id` | destination_id (inferred) | image_url | **Migration only** | `008_populate_place_images.sql` |
| `favorites` | Yêu thích | (`user_id`,`destination_id`) | user_id→users; destination_id (schema→destinations) | created_at | **Có** (join app_places) | `database.sql` L51-58; `favorites.repository.js` |
| `reviews` | Đánh giá | `id` | user_id→users; destination_id | rating, comment | **Có** (join app_places) | `database.sql` L63-74; `reviews.repository.js` |
| `itineraries` | Lịch trình | `id` | user_id→users | title, start_date, end_date, status | **Có** | `011_create_itinerary_tables.sql`; `itineraries.repository.js` |
| `itinerary_days` | Ngày trong lịch trình | `id` | itinerary_id→itineraries | day_number, date | **Có** | `011`; `itineraries.repository.js` |
| `itinerary_items` | Điểm trong ngày | `id` | day_id→itinerary_days; destination_id→**app_places** (v2) | start_time, end_time, order_index | **Có** | `011` L38-51; `itineraries.repository.js` L40 |
| `place_id_map` | Map RAG ID → app_places | `id` | new_app_place_id→app_places | rag_place_id, place_key, old_destination_id | **Có** | `004_create_place_id_map.sql`; `placeIdMap.repository.js` |
| `rag_knowledge_base` | Knowledge RAG v2 | `id` | app_place_id→app_places | knowledge_key, content, search_text | **Export/build, không RAG runtime** | `002_create_rag_knowledge_base.sql` |
| Admin/log tables | — | — | — | — | **KHÔNG TÌM THẤY** | Admin dùng cookie JWT + env |

### Quan hệ

| Cha | Con | Quan hệ | FK | Ý nghĩa | File |
|---|---|---|---|---|---|
| users | favorites | 1-N | user_id | User yêu thích địa điểm | `database.sql` |
| app_places | favorites | 1-N | destination_id (runtime join) | FK column tên destination_id nhưng join app_places | `favorites.repository.js` |
| users | reviews | 1-N | user_id | User viết review | `reviews.repository.js` |
| app_places | reviews | 1-N | destination_id | Review cho địa điểm | `reviews.repository.js` |
| users | itineraries | 1-N | user_id | Lịch trình của user | `itineraries.repository.js` |
| itineraries | itinerary_days | 1-N | itinerary_id | Các ngày | `011` |
| itinerary_days | itinerary_items | 1-N | day_id | Các stop trong ngày | `011` |
| app_places | itinerary_items | 1-N | destination_id (v2 FK) | Địa điểm trong lịch trình | `011` L50 |
| app_places | place_images | 1-N | app_place_id | Ảnh | `003` |
| app_places | place_id_map | 1-N | new_app_place_id | Map ID RAG/legacy | `004`, `007` |

### Xác nhận đặc biệt

1. **API địa điểm đọc `app_places`** — `FROM app_places d` (`destinations.repository.js` L38)
2. **Ảnh đọc `place_images`** — `destinationImages.repository.js`
3. **`reviews` liên kết** — column `destination_id`, runtime join `app_places.id` (`reviews.repository.js`)
4. **`favorites` liên kết** — column `destination_id`, runtime join `app_places.id` (`favorites.repository.js`)
5. **`itinerary_items`** — FK v2 → `app_places.id`; insert qua `destinationId` đã resolve (`itineraries.service.js` L569)
6. **`place_id_map`** — map `rag_place_id`/`place_key`/`RAG_ALIAS_*` → `new_app_place_id` (`007_populate_place_id_map.sql`, `placeIdMap.repository.js`)
7. **`destinations`** — **legacy/fallback**, không phải bảng đọc chính; vẽ rút gọn có thể ghi chú legacy
8. **RAG runtime DB** — **không**; chỉ file/index + script export từ MySQL

---

## E. SƠ ĐỒ 4 — LUỒNG CHATBOT AI/RAG

### 1. Android

| Hạng mục | Chi tiết | File |
|---|---|---|
| Màn hình chatbot | `ChatbotFragment` | `ui/chatbot/ChatbotFragment.kt` |
| ViewModel | `ChatbotViewModel` | `viewmodel/ChatbotViewModel.kt` |
| Gọi RAG | `RagService.chat()` → `POST ai/rag-chat` | `RagService.kt` L41; `ApiService.kt` L222 |
| Gọi fallback/prepare/validate/repair | `GeminiService` → `POST ai/chat` | `GeminiService.kt` |
| Request model | `ChatRequest(message, top_k, mode, targetProvince, targetCity)` | `Models.kt` L333-339 |
| Response model | `ChatResponse(answer, success, places)` | `Models.kt` L340-345 |

### 2. Node.js

| Hạng mục | Chi tiết | File |
|---|---|---|
| Route RAG chat | `POST /api/ai/rag-chat` | `ai.routes.js` L19; `ai.controller.js` `ragChat` L98-157 |
| Proxy FastAPI | `/rag/chat/simple` | `ai.service.js` L50-51 |
| Route fallback chat | `POST /api/ai/chat` | `ai.routes.js` L20; `ai.controller.js` `chat` L160-202 |
| Node gọi Gemini trực tiếp | **KHÔNG** | grep Gemini trong `backend/nodejs/src` |
| FastAPI lỗi | `/api/ai/rag-chat` → **502** `{ success:false, message:"FastAPI RAG trả lỗi" }` | `ai.controller.js` L130-136 |
| `/api/ai/chat` fallback | Optional `AI_MODEL_URL` → else RAG `/rag/chat/simple` | `ai.controller.js` L176-185; `env.js` L145-149 |

### 3. FastAPI RAG pipeline (`RagPipeline.run`)

| Bước | Component | File |
|---|---|---|
| Parse intent | `IntentParser.parse` | `retrieval/intent_parser.py` |
| Retrieve | `HybridRetriever.retrieve` (BM25 + optional vector) | `retrieval/hybrid_retriever.py`, `bm25_retriever.py` |
| Location filter | `LocationFilter.apply` | `pipelines/policies/location_filter.py` |
| Build context | `ContextBuilder.build_context` | `generation/context_builder.py` |
| Build prompt | `PromptBuilder.build_prompt` | `generation/prompt_builder.py` |
| Generate | `GenerationRouter.generate` (Gemini hoặc template) | `generation_router.py` |
| Shape response | `extract_places`, `extract_warnings` | `pipelines/response_builder.py` |

**BM25:** `data/indexes/bm25_index.pkl` + corpus JSONL  
**Corpus:** `data/processed/places_rag_documents.jsonl`  
**Place store:** `data/processed/places_app.json` (hoặc `places_app_reviewed.json`)  
**Gemini:** trong `GenerationRouter._generate_with_gemini_or_template`  
**Mock/template:** khi `AI_RUNTIME_MODE=mock` hoặc Gemini fail

### 4. Gemini prepare/validate/repair — **trên Android qua Node `/api/ai/chat`**

| Chức năng | Android function | Gọi endpoint | File |
|---|---|---|---|
| Prepare query | `GeminiService.prepareRagQuery()` | `/api/ai/chat` (prompt JSON schema) | `GeminiService.kt` L59-134 |
| Validate output | `GeminiService.validateRagOutputFull()` | `/api/ai/chat` | `GeminiService.kt` L136-205 |
| Repair answer | `GeminiService.repairRagAnswer()` | `/api/ai/chat` | `GeminiService.kt` L207-298 |
| Fallback chat | `GeminiService.fallbackChat()` | `/api/ai/chat` | `GeminiService.kt` L21-57 |

**Lưu ý:** Node `/api/ai/chat` không gọi Gemini SDK; nó gọi `AI_MODEL_URL` (nếu set) hoặc FastAPI RAG — có thể kích hoạt Gemini **gián tiếp** trong FastAPI.

### Step-by-step

| Bước | Actor | Hành động | Endpoint/function | Input | Output | File |
|---|---|---|---|---|---|---|
| 1 | User | Nhập tin nhắn | — | text | — | `ChatbotFragment.kt` |
| 2 | ChatbotViewModel | `sendMessage()` | — | userText | — | `ChatbotViewModel.kt` L48-87 |
| 3 | GeminiService | Prepare query | `POST /api/ai/chat` | prompt chuẩn hóa | `GeminiPreparedQuery` | `GeminiService.kt` L59; `ChatbotViewModel.kt` L90-93 |
| 4 | ChatbotViewModel | Build context-aware query | — | preparedQuery + province + tripDays | ragQuery | `ChatbotViewModel.kt` L113-119 |
| 5 | RagService | Gọi RAG | `POST /api/ai/rag-chat` | `ChatRequest` | answer + places | `RagService.kt` L33-44 |
| 6 | Node | Proxy | FastAPI `/rag/chat/simple` | message, top_k, targetProvince | RAG JSON | `ai.controller.js` L119; `ai.service.js` L51 |
| 7 | FastAPI | Pipeline | `RagPipeline.run` | query | answer, places, model_used | `rag_pipeline.py` L32+; `rag_service.py` L47 |
| 8 | ChatbotViewModel | Check province mismatch | — | places vs targetProvince | retry strict query hoặc fail message | `ChatbotViewModel.kt` L137-179 |
| 9 | GeminiService | Validate RAG output | `POST /api/ai/chat` | RAG answer + places | valid/correctedQuery | `ChatbotViewModel.kt` L182-227 |
| 10a | GeminiService | Repair (RAG OK) | `POST /api/ai/chat` | ragAnswer + places | ChatbotResult | `ChatbotViewModel.kt` L237-247 |
| 10b | GeminiService | Fallback (RAG fail) | `POST /api/ai/chat` | userMessage | ChatbotResult | `ChatbotViewModel.kt` L231-235 |

### Nhánh điều kiện

| Điều kiện | Nhánh | Component | Kết quả |
|---|---|---|---|
| RAG HTTP fail / blank answer | `isRagFailed=true` | ChatbotViewModel | `fallbackChat()` |
| Province mismatch lần 1 | Retry strict province query | ChatbotViewModel + RagService | Gọi RAG lần 2 |
| Vẫn mismatch sau retry | Return message cố định | ChatbotViewModel | Không fallback Gemini |
| Validate invalid + có correctedQuery | Retry RAG với query mới | ChatbotViewModel | Gọi RAG lần 3 |
| Validate invalid, không correctedQuery | Return message | ChatbotViewModel | Thông báo không tìm được |
| RAG OK | repairRagAnswer | GeminiService | Câu trả lời đã polish |
| repair fail | Template itinerary answer | GeminiService | `buildTemplateItineraryAnswer()` |
| FastAPI down | Node 502 | ai.controller | Android nhận "RAG không trả được…" → fallback |

---

## F. SƠ ĐỒ 5 — LUỒNG GỢI Ý LỊCH TRÌNH AI/RAG

### 1. Android

| Màn hình | Text UI | File |
|---|---|---|
| Form nhập | **"Bạn muốn đi đâu nè? ✨"** | `fragment_ai_itinerary_request.xml` L51; `AIItineraryRequestFragment.kt` |
| Chọn tour | **"Chọn tour AI nè ✨"** | `fragment_ai_itinerary_options.xml` L44; `AIItineraryOptionsFragment.kt` |
| Chi tiết/chỉnh trước lưu | `AIItineraryEditorFragment` (checkbox từng địa điểm) | `AIItineraryEditorFragment.kt` |
| Lấy options | `POST /api/ai/itinerary-options` | `ApiService.kt` L232; `ItineraryViewModel.kt` L289-320 |
| Tạo itinerary | `POST /api/itineraries/create-from-option` | `ApiService.kt` L238; `ItineraryViewModel.kt` L322-355 |
| Request options | `AIItineraryPreviewRequest(title, startDate, endDate, budget, preferences, province)` | `Models.kt` L216-226 |
| Response options | `AIItineraryOptionsResponse` → `options: List<AIItineraryOption>` | `Models.kt` L277-298 |
| Request create | `CreateItineraryFromOptionRequest(optionId, days, …)` | `Models.kt` L305-313 |

**Luồng cũ (vẫn có code):** `POST /api/ai/suggest-itinerary` — tạo và lưu luôn (`GeminiService.suggestItinerary`, `ai.routes.js` L18)

### 2. Node.js

| Endpoint | Handler | FastAPI | File |
|---|---|---|---|
| `POST /api/ai/itinerary-options` | `itineraryOptions` | `/ai/itinerary-options` | `ai.routes.js` L22; `ai.controller.js` L250-296 |
| `POST /api/itineraries/create-from-option` | `createFromOption` | — (MySQL only) | `ai.routes.js` L23; `ai.controller.js` L299-356 |
| Service persist | `createItineraryFromAiOption` | — | `itineraries.service.js` L435+ |
| place_id_map | `placeIdMapService.resolveRawPlaceIdsFromItems` | — | `placeIdMap.service.js`; `itineraries.service.js` L491-493 |
| Lưu bảng | `itineraries`, `itinerary_days`, `itinerary_items` | — | `itineraries.service.js` L502-586 |

### 3. FastAPI itinerary options

| Hạng mục | Chi tiết | File |
|---|---|---|
| Endpoint | `POST /ai/itinerary-options` | `ai_itinerary.py` |
| Service | `ItineraryService.options()` | `services/itinerary/service.py` L87+ |
| Data source | `load_places()` từ **file JSON** | `services/itinerary/catalog.py` |
| 4 options cố định | balanced, checkin, food_culture, relax_nature | `service.py` L104-137 |
| Option fields | optionId, title, summary, theme, estimatedBudget, totalDays, highlights, days[] | `builder.py`, `Models.kt` L289-298 |
| Place ID trong option | `rawPlaceId` (RAG place_id) + `destinationId` (numeric nếu có) | `builder.py` L16-41 |
| confidence/reason/tags | `reason`, `qualityScore`, `estimatedVisitDurationMinutes` — **có**; confidence field — **KHÔNG TÌM THẤY** | `builder.py` L26-40 |
| Gemini trong itinerary options | **KHÔNG** — scoring + template distribution | `service.py`, `scoring.py` |
| Fallback empty places | `success: false`, options: [] | `service.py` L89-97 |

### Luồng A — Tạo option AI/RAG

| Bước | Component | Hành động | Endpoint | File |
|---|---|---|---|---|
| 1 | User | Nhập form | — | `AIItineraryRequestFragment.kt` L88-107 |
| 2 | ItineraryViewModel | Validate title/dates | — | `AIItineraryRequestFragment.kt` L100-107 |
| 3 | ItineraryRepository | HTTP POST | `/api/ai/itinerary-options` | `Repositories.kt` L382+ |
| 4 | Node ai.controller | Validate Zod + proxy | FastAPI `/ai/itinerary-options` | `ai.controller.js` L250-287 |
| 5 | FastAPI ItineraryService | Score places, build 4 options | — | `service.py` L87-150 |
| 6 | Android | Navigate options screen | — | `AIItineraryRequestFragment.kt` (observe navigate) |

### Luồng B — Tạo itinerary từ option

| Bước | Component | Hành động | Endpoint | File |
|---|---|---|---|---|
| 1 | User | Chọn option / chỉnh editor | — | `AIItineraryOptionsFragment.kt`, `AIItineraryEditorFragment.kt` |
| 2 | ItineraryViewModel | `createItineraryFromOption()` | `/api/itineraries/create-from-option` | `ItineraryViewModel.kt` L322-355 |
| 3 | Node | `createItineraryFromAiOption` | — | `itineraries.service.js` L435 |
| 4 | placeIdMap | Resolve rawPlaceId → app_places.id | — | `placeIdMap.service.js`; `itineraryDto.js` L30-77 |
| 5 | DB transaction | insert itinerary + days + items | — | `itineraries.service.js` L502-586 |
| 6 | Response | `{ itineraryId, selectedCount, unresolved }` | — | `itineraries.service.js` L588-597 |

### Nhánh điều kiện

| Điều kiện | Xử lý | Component | Kết quả |
|---|---|---|---|
| Thiếu title/startDate/endDate | Toast | Android | Dừng, không gọi API |
| FastAPI/RAG lỗi | 502 JSON | Node | Android `Resource.Error` |
| Không có places file | success:false, options:[] | FastAPI | Empty options |
| Không map được ID nào | 400 `no_mapped_destinations` | Node | Fail create |
| Một số item không map | `continue` skip item | `itineraries.service.js` L565 | Vẫn tạo nếu còn item map được |
| Ngày invalid | 400 `invalid_dates` | Node | Fail create |
| Tạo thành công | 200 + reload list | Android | Toast success |

---

## G. SƠ ĐỒ 6 — BẢN ĐỒ, ĐỊNH VỊ, THỜI TIẾT

### Bảng thành phần

| Thành phần | Công nghệ/file | Vai trò | Dữ liệu vào | Dữ liệu ra | File |
|---|---|---|---|---|---|
| Map in-app | OSMDroid MapView | Hiển thị marker địa điểm + user | lat/lon từ nav args | Map UI | `MapFragment.kt`, `fragment_map.xml` |
| Map external | Google Maps intent | Mở/chỉ đường ngoài app | lat/lon, route points | External app/browser | `MapIntentHelper.kt` |
| Tọa độ địa điểm | API Destination detail | lat/lon từ `app_places` | destinationId | latitude, longitude | `DestinationDetailFragment.kt` L156-162; `destinations.repository.js` |
| Default map coords | Hardcoded fallback | Nếu thiếu args | — | 21.5878, 105.8069 | `MapFragment.kt` L61-62 |
| Location user (map) | FusedLocationProvider `lastLocation` | Marker "Bạn đang ở đây" | GPS | lat/lng | `MapFragment.kt` L131-167 |
| Location user (home) | FusedLocationProvider `getCurrentLocation` | Nearby destinations | GPS | lat/lng → API nearby | `HomeFragment.kt` L272-296 |
| Nearby API | Node `GET /api/destinations/nearby` | Địa điểm gần | lat, lng, radiusKm | destinations + distanceKm | `destinations.routes.js` L12 |
| Weather | Open-Meteo | Forecast | city name → cityCoords map | temp, humidity, wind, 5-day forecast | `WeatherService.kt` |
| Weather UI | Destination detail card | Hiển thị | WeatherInfo | Text + emoji icon | `DestinationDetailFragment.kt` L173-196 |
| Backend weather/map | **KHÔNG CÓ** | — | — | — | grep `weather` in `backend/nodejs/src` |

### Luồng xử lý

| Luồng | Actor | Hành động | Nguồn/API | Kết quả |
|---|---|---|---|---|
| Xem bản đồ địa điểm | User → DestinationDetail → MapFragment | Navigate với lat/lon/name | `GET /api/destinations/:id` | OSMDroid marker + zoom 15 |
| Lấy vị trí hiện tại (map) | MapFragment | Request FINE_LOCATION → lastLocation | FusedLocationProvider | Marker user hoặc Toast lỗi |
| Lấy vị trí (home nearby) | HomeFragment | getCurrentLocation HIGH_ACCURACY | FusedLocationProvider → `/destinations/nearby` | Danh sách gần hoặc fallback 21.5878,105.8069 |
| Chỉ đường ngoài | MapFragment btn | openRoute / openNavigation | Google Maps intent | App/browser ngoài |
| Xem thời tiết | DestinationDetail | loadWeather(city) | Open-Meteo via city mapping | Card thời tiết hoặc ẩn card |

### Permissions

`INTERNET`, `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, `WRITE_EXTERNAL_STORAGE` (OSMDroid cache) — `AndroidManifest.xml` L5-13

---

## H. SƠ ĐỒ 7 — BẢN ĐỒ VÀ THỜI TIẾT (CHUẨN HÓA)

### Luồng step-by-step

| Bước | Nhánh | Component | Hành động | API/File | Kết quả |
|---|---|---|---|---|---|
| 1 | — | User | Mở chi tiết địa điểm | — | DestinationDetailFragment |
| 2 | Bản đồ | User | Bấm "Xem bản đồ" | — | Nav MapFragment |
| 3 | Bản đồ | DestinationDetail | Pass lat/lon/name qua Bundle | destination.latitude/longitude | MapFragment args |
| 4 | Bản đồ | MapFragment | Render OSMDroid MAPNIK | OSM tiles | Marker địa điểm |
| 5 | Bản đồ | MapFragment | Request location permission | Manifest FINE_LOCATION | loadCurrentLocation |
| 6 | Bản đồ | MapFragment | FusedLocation lastLocation | play-services-location | Marker "Bạn đang ở đây" |
| 7 | Bản đồ | User | Bấm mở Google Maps | MapIntentHelper.openPlace | Intent ngoài app |
| 8 | Bản đồ | User | Bấm chỉ đường | MapIntentHelper.openRoute/openNavigation | Google Maps ngoài app |
| 9 | Thời tiết | DestinationDetail | loadWeather(city) | WeatherService.kt | — |
| 10 | Thời tiết | WeatherService | Map city → lat/lon | cityCoords map L19-41 | Tọa độ |
| 11 | Thời tiết | WeatherService | GET forecast | open-meteo.com | JSON parse |
| 12 | Thời tiết | DestinationDetail | Bind UI card | — | temp, desc, humidity |
| 13 | Thời tiết | Error | catch Exception | WeatherService L90-92 | Ẩn card weather |

### Điều kiện

| Điều kiện | Nhánh | Ghi chú |
|---|---|---|
| Thiếu tọa độ địa điểm (nav args null) | MapFragment dùng default 21.5878, 105.8069 | `MapFragment.kt` L61-62 |
| MapIntentHelper lat/lng invalid | Toast "Địa điểm chưa có tọa độ" | `MapIntentHelper.kt` L17-19 |
| Chưa cấp quyền location | Request permission; Toast nếu deny | `MapFragment.kt` L118-128 |
| GPS null trên map | Toast "Chưa lấy được vị trí hiện tại" | `MapFragment.kt` L145-151 |
| GPS null trên home | Fallback lat/lng ICTU Thái Nguyên | `HomeFragment.kt` L308-317 |
| City không trong cityCoords | Default Hà Nội 21.0285, 105.8542 | `WeatherService.kt` L46-49 |
| Open-Meteo lỗi | `Resource.Error`, ẩn card | `DestinationDetailFragment.kt` L191-193 |
| Không có mạng | Exception trong WeatherService / Retrofit | Error state tương ứng |
| User chọn map ngoài app | Intent Google Maps (không route nội bộ OSMDroid) | `MapIntentHelper.kt` |

**Lưu ý sơ đồ 7:** Weather **không** dùng lat/lon trực tiếp từ destination; dùng **`destination.city`** → city mapping (`DestinationDetailFragment.kt` L170).

---

# PHẦN 3 — CẢNH BÁO KHÔNG ĐƯỢC VẼ SAI

1. **Không vẽ Android → FastAPI trực tiếp** — mọi AI/RAG qua Node `:3000/api` (`RetrofitClient.kt`)
2. **Không vẽ RAG đọc MySQL runtime** — FastAPI dùng BM25 pickle + JSONL + JSON places (`backend/rag/data/`)
3. **Không vẽ weather qua backend** — Android gọi Open-Meteo trực tiếp (`WeatherService.kt`)
4. **Không vẽ Google Maps SDK in-app** — app dùng OSMDroid; Google Maps chỉ intent ngoài (`AndroidManifest.xml` L32, `MapIntentHelper.kt`)
5. **Không vẽ vector database (Pinecone/Chroma/FAISS)** — dense search dùng NPZ in-memory, BM25 pickle (`vector_retriever.py`)
6. **Không vẽ Gemini SDK trên Android** — `GeminiService` gọi Node `/api/ai/chat`; `GEMINI_API_KEY` trong BuildConfig **không thấy** code gọi trực tiếp
7. **Không vẽ prepare/validate/repair trong FastAPI** — logic này nằm **Android + Node proxy** (`GeminiService.kt`, `ChatbotViewModel.kt`)
8. **Không vẽ bảng `destinations` là catalog chính** — runtime đọc `app_places` (`destinations.repository.js`)
9. **Không vẽ `destination_images` runtime** — dùng `place_images`
10. **Không vẽ payment/booking** — **KHÔNG TÌM THẤY** trong project
11. **Không vẽ route optimization nội bộ** — OSMDroid chỉ marker; chỉ đường qua Google Maps intent
12. **Không vẽ fine-tune model** — **KHÔNG TÌM THẤY**
13. **Không vẽ Admin gọi FastAPI trực tiếp từ browser** — Admin Node proxy qua `ragHttp.js`
14. **Không vẽ weather theo lat/lon destination** — chỉ theo **city name mapping** (`DestinationDetailFragment.kt` L170)
15. **Không vẽ itinerary options dùng Gemini** — FastAPI dùng scoring/template từ file places (`ItineraryService.options`)
16. **Không vẽ bảng admin/log trong MySQL** — admin auth bằng cookie JWT + env credentials
17. **Không vẽ Compose UI chính** — UI thực tế là XML/ViewBinding
18. **Không vẽ Node gọi Gemini trực tiếp** — Node proxy RAG hoặc optional `AI_MODEL_URL`

---

# PHẦN 4 — BẢNG COPY NHANH CHO CHATGPT VẼ SƠ ĐỒ

| Sơ đồ | Thành phần | Kết nối/luồng | Endpoint/API | DB/File dữ liệu | Fallback/nhánh lỗi |
|---|---|---|---|---|---|
| **1 UML 3 lớp** | Android, Admin Web, Node, FastAPI, MySQL, RAG files, Open-Meteo, OSM, Gemini | Presentation→Business→Data | `/api/*`, `/admin/*`, RAG `:8001` | MySQL `unudata`; RAG files | FastAPI lỗi→502; template/mock RAG |
| **2 Client-Server+AI** | Android, Admin, Node, FastAPI, MySQL, External APIs | Android→Node→FastAPI/MySQL; Android→Open-Meteo/OSM trực tiếp | `rag-chat`, `itinerary-options`, `create-from-option` | `app_places`, BM25, JSONL | Node→RAG retry; chat fallback `/api/ai/chat` |
| **3 CSDL** | users, app_places, place_images, favorites, reviews, itineraries*, place_id_map | FK + runtime joins | Repositories SQL | migrations 001-011 | destinations=legacy; rag_knowledge_base=export only |
| **4 Chatbot** | ChatbotFragment, ChatbotViewModel, RagService, GeminiService, Node, FastAPI | prepare→rag-chat→validate→repair/fallback | `/api/ai/rag-chat`, `/api/ai/chat`, FastAPI `/rag/chat/simple` | BM25+corpus+places JSON | RAG fail→fallbackChat; province mismatch→retry/abort |
| **5 Itinerary AI** | AIItineraryRequest/Options/Editor, Node, FastAPI, place_id_map | options→user chọn→create-from-option | `/api/ai/itinerary-options`, `/api/itineraries/create-from-option`, FastAPI `/ai/itinerary-options` | itineraries*, app_places, place_id_map | no map→400; unmapped items skipped |
| **6 Map+Location+Weather** | MapFragment, HomeFragment, WeatherService, DestinationDetail | detail→map/weather; home→nearby | `/api/destinations/:id`, `/nearby`, open-meteo.com | app_places lat/lng | GPS null→fallback coords; weather error→hide card |
| **7 Map+Weather only** | DestinationDetail nhánh Bản đồ / Thời tiết | Map: lat/lon→OSMDroid+GPS; Weather: city→Open-Meteo | OSM tiles, Google Maps intent, open-meteo.com | cityCoords hardcoded | thiếu coords→default; deny permission→toast |

---

*Tài liệu được tạo từ phân tích READ-ONLY codebase UNUTrip. Cập nhật: 2026-05-21.*
