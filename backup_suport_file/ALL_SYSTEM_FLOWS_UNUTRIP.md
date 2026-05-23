# ALL SYSTEM FLOWS - UNU Trip

> Tài liệu trích từ code (read-only). Mọi mục không thấy trong code được ghi **CHƯA XÁC MINH** hoặc **KHÔNG THẤY TRONG CODE**.

---

## 0. Tổng quan phát hiện từ code

### 0.1. Kiến trúc thật

| Thành phần | Mô tả |
|------------|--------|
| **Android** | App Kotlin `com.unutrip` — `AuthActivity`, `MainActivity` + Navigation Component (`nav_graph.xml`). Retrofit `ApiService` → Node backend. Package `com.smarttravel` còn trên disk nhưng **không** có trong `AndroidManifest.xml` / `nav_graph.xml`. |
| **Backend** | Node.js/Express `backend/nodejs` — entry `src/index.js`, router `/api` (`src/api/router.js`), admin `/admin` (`src/admin/index.js`). |
| **Database** | MySQL/MariaDB — tên DB mặc định `unudata`. Runtime đọc chủ yếu bảng v2 `app_places`; bootstrap legacy `backend/nodejs/database.sql`. Migrations v2: `database/migrations/`. |
| **RAG Service** | FastAPI `backend/rag` — retrieval từ file JSON/BM25 local, **không** query MySQL khi xử lý request. Node proxy qua `RAG_BASE_URL`. |
| **Admin Dashboard** | HTML server-side Express tại `/admin/*` (Tailwind CDN), không phải SPA riêng. |
| **Dịch vụ ngoài** | Open-Meteo (Android trực tiếp), OSMDroid/OSM tiles, Google Maps intents; Gemini chỉ trong FastAPI RAG (qua Node proxy). |

### 0.2. Base URL / Port / Prefix thật

| Hạng mục | Giá trị | Nguồn |
|----------|---------|--------|
| **Android BASE_URL** | `local.properties` → `API_BASE_URL`; mặc định `http://10.0.2.2:3000/api/` | `app/build.gradle`, `RetrofitClient.kt` |
| **Backend port** | `BACKEND_PORT` \|\| `PORT` \|\| `3000` | `backend/nodejs/src/index.js`, `.env.example` |
| **API prefix** | `/api` | `backend/nodejs/src/app.js` |
| **RAG URL/port** | `RAG_BASE_URL` mặc định `http://127.0.0.1:8001`; Docker `RAG_PUBLISH_PORT` 8001 | `.env.example`, `docker-compose.yml` |
| **Database name** | `DB_NAME` mặc định `unudata` | `.env.example`, `backend/nodejs/src/config/env.js` |
| **Admin URL** | `http://<host>:3000/admin/` (redirect → `/admin/dashboard`) | `backend/nodejs/src/admin/dashboard.admin.routes.js` |

### 0.3. Danh sách actor thật đề xuất cho biểu đồ

| Actor | Vai trò | Chức năng liên quan | Ghi chú |
|-------|---------|---------------------|---------|
| Người dùng | End user | Auth, khám phá địa điểm, yêu thích, đánh giá, lịch trình, chatbot, hồ sơ | |
| Quản trị viên | Admin web | Dashboard, users, destinations, RAG monitor/debug | HTTP Basic nếu cấu hình `ADMIN_BASIC_*` |
| Ứng dụng Android | Client | Toàn bộ UI `com.unutrip` | |
| Backend Server | Node Express | REST `/api/*`, admin `/admin/*`, static `/uploads`, `/images` | |
| Cơ sở dữ liệu MySQL | Persistence | `users`, `app_places`, `favorites`, `reviews`, `itineraries`, … | |
| FastAPI RAG Service | AI/RAG | `/rag/*`, `/ai/*`, `/admin/*` (RAG) | Artifact local, không MySQL runtime |
| Open-Meteo | Thời tiết | Forecast API | Gọi **trực tiếp** từ `WeatherService.kt` |
| OSMDroid / OpenStreetMap | Bản đồ in-app | Tile MAPNIK | `MapFragment.kt` |
| Google Maps (intent) | Điều hướng ngoài app | `MapIntentHelper.kt` | |

---

## 1. Danh sách API thật

Base: `{BASE_URL}` = `http://<host>:3000/api/`. RAG nội bộ: `http://<host>:8001` (Node gọi, Android **không** gọi trực tiếp).

### 1.1. Auth / User / Destinations / Favorites / Reviews / Itineraries / AI (Node `/api`)

| Nhóm | Method | Endpoint | Auth? | Android gọi? | File backend route | File Android | Request chính | Response chính | Ghi chú |
|------|--------|----------|-------|--------------|-------------------|--------------|---------------|----------------|--------|
| Health | GET | `/health` | Không | Không | `modules/health/health.routes.js` | — | — | status | Ops only |
| Health | GET | `/health/ready` | Không | Không | same | — | — | DB + RAG probe | Ops only |
| Auth | POST | `/auth/register` | Không | Có | `modules/auth/auth.routes.js` | `ApiService.register`, `AuthRepository` | `RegisterRequest` | `AuthResponse` | |
| Auth | POST | `/auth/login` | Không | Có | same | `ApiService.login` | `LoginRequest` | `AuthResponse` | JWT |
| Auth | POST | `/auth/logout` | JWT | **Không** (chỉ clear local) | same | `ApiService.logout` (unused) | Bearer | `ApiResponse` | Mismatch: API có, app không gọi |
| User | GET | `/users/profile` | JWT | **Không** | `modules/users/users.routes.js` | `ApiService.getProfile` (unused) | Bearer | `User` | Session lưu local sau login |
| User | GET | `/users/stats` | JWT | Có | same | `ProfileFragment` | Bearer | `UserStats` | |
| User | PUT | `/users/profile` | JWT | Có | same | `ProfileFragment.updateProfile` | `User` | `User` | |
| User | PUT | `/users/preferences` | JWT | **Không** | same | `ApiService.updatePreferences` (unused) | `Map` prefs | `User` | |
| User | POST | `/users/avatar` | JWT + multipart | Có | same | `ProfileFragment.uploadAvatar` | `avatar` part | `User` | → `/uploads/avatars/` |
| Destinations | GET | `/destinations` | Optional JWT | Có | `modules/destinations/destinations.routes.js` | `DestinationRepository.getDestinations` | page, limit, category, province, search, sort | `DestinationResponse` | Query `app_places` |
| Destinations | GET | `/destinations/featured` | Optional JWT | Có | same | `HomeViewModel` | Bearer | list | |
| Destinations | GET | `/destinations/nearby` | Optional JWT | Có | same | `HomeViewModel` | lat, lng, radiusKm | list | |
| Destinations | GET | `/destinations/:id` | Optional JWT | Có | same | `getDestinationDetail` | id | detail + images | |
| Favorites | GET | `/users/favorites` | JWT | Có | `modules/favorites/favorites.routes.js` | `getFavorites` | Bearer | list | JOIN `app_places` |
| Favorites | POST | `/users/favorites` | JWT | Có | same | `addFavorite` | `destinationId` | ok | |
| Favorites | DELETE | `/users/favorites/:destinationId` | JWT | Có | same | `removeFavorite` | id | ok | |
| Reviews | GET | `/destinations/:id/reviews` | JWT | Có | `modules/reviews/reviews.routes.js` | `getReviews` | id | `List<Review>` | |
| Reviews | POST | `/reviews` | JWT + multipart ≤3 | Có | same | `postReview` / `postReviewWithImages` | `ReviewRequest` hoặc multipart | `Review` | Cập nhật `app_places.rating` |
| Itineraries | GET | `/itineraries` | JWT | Có | `modules/itineraries/itineraries.routes.js` | `ItineraryRepository` | Bearer | list | |
| Itineraries | GET | `/itineraries/:id` | JWT | Có | same | `getItineraryDetail` | id | `Itinerary` + days/items | |
| Itineraries | POST | `/itineraries` | JWT | Có | same | `createItinerary` | `CreateItineraryRequest` | `Itinerary` | |
| Itineraries | PUT | `/itineraries/:id` | JWT | Có | same | `updateItinerary` | meta | `Itinerary` | |
| Itineraries | DELETE | `/itineraries/:id` | JWT | Có | same | `deleteItinerary` | id | ok | |
| Itineraries | POST | `/itineraries/:id/days` | JWT | Có | same | `addItineraryDay` | — | ok | |
| Itineraries | DELETE | `/itineraries/:id/days/:dayId` | JWT | Có | same | `deleteItineraryDay` | — | ok | |
| Itineraries | POST | `/itineraries/:id/items` | JWT | Có | same | `addDestination` | `AddItineraryItemRequest` | ok | |
| Itineraries | PUT | `/itineraries/:id/items/:itemId` | JWT | Có | same | `updateItineraryItem` | times, note | ok | |
| Itineraries | DELETE | `/itineraries/:id/items/:itemId` | JWT | Có | same | `deleteItineraryItem` | — | ok | |
| Itineraries | POST | `/itineraries/save-ai` | JWT | Có | same | `saveAIItinerary` | `SaveAIItineraryRequest` | ok | Legacy `AISuggestFragment` |
| Itineraries | POST | `/itineraries/create-from-option` | JWT | Có | same + `placeIdMap.repository` | `createItineraryFromOption` | option JSON | ids | |
| Itineraries | POST | `/itineraries/create-from-selection` | JWT | **Không** (UI dead) | same | `ApiService` + repo only | selected places | ids | Chỉ gọi được nếu bật `preview` flow (cũng dead) |
| AI | POST | `/ai/itinerary-preview` | JWT | **Không** (repo/VM có, UI không) | `modules/ai/ai.routes.js` | `previewAIItinerary` unused | preview body | preview data | Proxy RAG |
| AI | POST | `/ai/itinerary-options` | JWT | Có | same | `getAIItineraryOptions` | `AIItineraryPreviewRequest` | options | Proxy RAG |
| AI | POST | `/ai/suggest-itinerary` | JWT | Có (legacy fragment) | same | `GeminiService.suggestItinerary` | `AISuggestRequest` | plan JSON | RAG/local fallback |
| AI | POST | `/ai/rag-chat` | Optional JWT | Có | same | `RagService.chat` | `ChatRequest` | `ChatResponse` | Proxy `/rag/chat/simple` |
| AI | POST | `/ai/chat` | Optional JWT | Có | same | `GeminiService.fallbackChat`, chatbot pipeline | `{message}` | `ChatResponse` | Chuẩn hóa/validate/repair |

### 1.2. Admin (Node `/admin` — không qua Retrofit Android)

| Nhóm | Method | Endpoint | Auth? | Android | File | Ghi chú |
|------|--------|----------|-------|---------|------|---------|
| Admin | GET | `/admin/dashboard` | Basic? | Không | `admin/dashboard.admin.routes.js` | HTML |
| Admin | GET/POST | `/admin/users`, `/admin/users/api/:id`, save, delete | Basic? | Không | `admin/users.admin.routes.js` | MySQL `users` |
| Admin | GET/POST | `/admin/destinations`, api, save, delete | Basic? | Không | `admin/destinations.admin.routes.js` | `app_places` |
| Admin | GET | `/admin/system` | Basic? | Không | `admin/system.admin.routes.js` | Count itineraries |
| Admin | GET/POST | `/admin/rag-ai`, reload, clear-cache, metrics, logs, debug-query | Basic? | Không | `admin/ragAi.admin.routes.js` | Proxy FastAPI |
| Admin | GET | `/admin/ai-report` | Basic? | Không | `admin/aiReport.admin.routes.js` | Stats + optional RAG |

### 1.3. RAG internal (FastAPI — Node proxy, Android không gọi trực tiếp)

| Nhóm | Method | Endpoint | Auth? | Gọi bởi | Ghi chú |
|------|--------|----------|-------|----------|---------|
| RAG | GET | `/health`, `/health/ready` | Exempt | Health checks | Có mirror `/v1/*` |
| RAG | POST | `/rag/chat/simple` | Internal key? | Node `/api/ai/rag-chat`, `/api/ai/chat` | Pipeline chính chatbot |
| RAG | POST | `/rag/chat` | Internal key? | Node suggest fallback, admin report | |
| RAG | POST | `/ai/itinerary-options` | Internal key? | Node `/api/ai/itinerary-options` | |
| RAG | POST | `/ai/itinerary-preview` | Internal key? | Node `/api/ai/itinerary-preview` | Android không dùng |
| RAG Admin | GET/POST | `/admin/ai/metrics`, `/admin/ai/logs`, `/admin/ai/debug-query`, … | Admin key? | Node `/admin/rag-ai/*` | `backend/rag/app/routers/admin/` |

**Ghi chú kỹ thuật AI (không vẽ làm nghiệp vụ chính):** `AI_RUNTIME_MODE` mặc định code `mock` (`backend/rag/core/config.py`); `.env.example` gợi ý `demo`. Fallback: template answer khi Gemini lỗi; `build_mock_answer()` khi mode=mock. RAG runtime **không** đọc MySQL.

---

## 2. Danh sách bảng CSDL thật

Nguồn: `database/migrations/*.sql` (v2 schema) + `backend/nodejs/database.sql` (legacy bootstrap, deprecated).

| Bảng | Vai trò nghiệp vụ | Khóa chính | Khóa ngoại/liên kết | API/flow | Repository / file | Ghi chú |
|------|-------------------|------------|---------------------|----------|-------------------|---------|
| `users` | Tài khoản | `id` | — | auth, profile, admin | `users.repository.js` | DDL trong `database.sql`, **không** trong migrations 001–011 |
| `destinations` | Địa điểm legacy | `id` | — | CHƯA dùng list API (runtime dùng `app_places`) | populate scripts | `database.sql`; fallback `placeIdMap` nếu `PLACE_ID_LEGACY_FALLBACK` |
| `app_places` | Địa điểm v2 | `id`, UNIQUE `place_key` | — | destinations, favorites JOIN, reviews, itineraries items | `destinations.repository.js` | `001_create_app_places.sql` |
| `place_images` | Ảnh địa điểm | `id` | `app_place_id` → `app_places` CASCADE | detail images | `destinationImages.repository.js` | `003_create_place_images.sql` |
| `place_id_map` | Map RAG/legacy → app_place | `id` | `new_app_place_id` → `app_places` | create-from-option/selection | `placeIdMap.repository.js` | `004_create_place_id_map.sql` |
| `rag_knowledge_base` | Corpus RAG DB (export) | `id` | `app_place_id` → `app_places` SET NULL | Offline export scripts | migrations `002` | FastAPI runtime dùng JSON, không SELECT bảng này |
| `favorites` | Yêu thích | (`user_id`, `destination_id`) | FK legacy → `users`, `destinations` | favorites API | `favorites.repository.js` | Runtime JOIN `app_places`; FK legacy có thể lệch nếu chỉ migrate v2 |
| `reviews` | Đánh giá | `id` | `user_id`, `destination_id` | reviews API | `reviews.repository.js` | Verify FK trỏ `destinations` hay `app_places` — code check `app_places.id` |
| `itineraries` | Lịch trình | `id` | `user_id` → `users` | itineraries CRUD | `itineraries.repository.js` | `011` + `database.sql` |
| `itinerary_days` | Ngày trong lịch | `id` | `itinerary_id` → `itineraries` | days API | same | |
| `itinerary_items` | Điểm trong ngày | `id` | `day_id`, `destination_id` → `app_places` (v2) | items API | same | Legacy FK → `destinations` trong `database.sql` |

---

## 3. Use Case tổng quát đề xuất

### 3.1. Người dùng

| Use Case | Có trong code? | API liên quan | Bảng liên quan | Ghi chú |
|----------|----------------|---------------|----------------|---------|
| Đăng ký | Có | POST `/auth/register` | `users` | `AuthActivity`, `AuthViewModel` |
| Đăng nhập | Có | POST `/auth/login` | `users` | JWT → `SessionManager` |
| Đăng xuất | Một phần | POST `/auth/logout` (không gọi) | — | Chỉ `SessionManager.clearSession()` |
| Xem/sửa hồ sơ, avatar | Có | PUT `/users/profile`, POST `/users/avatar`, GET `/users/stats` | `users` | Không refresh từ GET profile |
| Danh sách / tìm / lọc địa điểm | Có | GET `/destinations` | `app_places` | Category chips, search |
| Chi tiết địa điểm | Có | GET `/destinations/:id` | `app_places`, `place_images` | |
| Yêu thích (thêm/xóa/danh sách) | Có | favorites endpoints | `favorites`, `app_places` | |
| Đánh giá (gửi/xem) | Có | GET reviews, POST `/reviews` | `reviews`, `app_places` | |
| Bản đồ | Có | — (tọa độ từ detail) | — | OSMDroid + intents |
| Thời tiết | Có | — | — | Open-Meteo trực tiếp |
| Lịch trình thủ công | Có | itineraries CRUD | `itineraries`, `itinerary_days`, `itinerary_items` | Dialogs + detail |
| Gợi ý lịch trình AI | Có | `/ai/itinerary-options`, create-from-option, legacy suggest | `app_places`, `place_id_map`, itineraries | Nhiều nhánh UI |
| Chatbot | Có | `/ai/rag-chat`, `/ai/chat` | — (RAG artifacts) | Pipeline validate/repair |
| Cài đặt app | UI only | — | — | `SettingsFragment` toast "đang phát triển" |

### 3.2. Quản trị viên

| Use Case | Có trong code? | Route/Admin page | Bảng | Ghi chú |
|----------|----------------|------------------|------|---------|
| Đăng nhập admin | Có (HTTP Basic) | Mọi `/admin/*` | — | Không có trang login riêng; thiếu env → mở (dev warning) |
| Quản lý người dùng | Có | `/admin/users` | `users` | CRUD |
| Quản lý địa điểm | Có | `/admin/destinations` | `app_places` | |
| Quản lý đánh giá | **KHÔNG THẤY** | — | `reviews` | Chỉ API mobile |
| Dashboard | Có | `/admin/dashboard` | counts | + `GET /admin/ai-report` |
| Giám sát RAG | Có | `/admin/rag-ai` | — | Proxy metrics/logs |
| Debug truy vấn RAG | Có | POST `/admin/rag-ai/debug-query` | — | → FastAPI `/admin/ai/debug-query` |

### 3.3. AI/RAG/System

| Use Case | Trigger | Service | API | Ghi chú |
|----------|---------|---------|-----|---------|
| RAG chat đơn giản | User chatbot | `RagPipeline` | FastAPI `/rag/chat/simple` via Node | |
| Chuẩn hóa câu hỏi | Chatbot | `GeminiService.prepareRagQuery` | POST `/ai/chat` | JSON structured |
| Gợi ý tour (options) | User AI flow | FastAPI itinerary | `/ai/itinerary-options` | |
| Lưu lịch từ option | User | Node `itineraries.service` | `/itineraries/create-from-option` | `place_id_map` |
| Legacy suggest + save | `AISuggestFragment` (nav dead?) | Node + RAG | `/ai/suggest-itinerary`, `/itineraries/save-ai` | Nav action tồn tại, không thấy `navigate()` |
| Mock/template generation | RAG khi lỗi/mode | `generation_router.py` | — | Ghi chú kỹ thuật, không UC chính |

---

## 4. Đặc tả flow chi tiết để vẽ biểu đồ trình tự

### 4.1. Đăng ký tài khoản

#### 4.1.1. Thông tin tổng quan
- **Actor chính:** Người dùng
- **Màn hình:** `AuthActivity` (`app/src/main/java/com/unutrip/ui/auth/AuthActivity.kt`)
- **ViewModel/Repository:** `AuthViewModel` → `AuthRepository`
- **API:** POST `/api/auth/register`
- **Backend:** `auth.controller.register` → `users.repository.createUser`
- **Bảng:** `users`
- **Auth/JWT:** Không (trả token sau đăng ký)
- **Kết quả:** Vào `MainActivity`

#### 4.1.2. Luồng chính
1. Người dùng → `AuthActivity`: nhập fullName, email, password, phone; bấm Đăng ký
2. `AuthActivity` → `AuthViewModel.register()`
3. `AuthViewModel` → `AuthRepository.register()` → `ApiService.register` (`RegisterRequest`)
4. Retrofit → Node POST `/api/auth/register`
5. `auth.controller.register`: validate zod → kiểm tra email tồn tại → bcrypt hash → INSERT `users`
6. `signToken` → response `{ token, user }`
7. Android `SessionManager.saveSession` → `MainActivity`

#### 4.1.3. Luồng lỗi/rẽ nhánh
- **Thiếu/sai định dạng:** 400 `Invalid payload`
- **Email trùng:** 400 `Email đã tồn tại`
- **Lỗi mạng:** `Resource.Error` → Toast

#### 4.1.4. Participants
Người dùng → AuthActivity → AuthViewModel → AuthRepository → Backend API → users.repository → MySQL

#### 4.1.5. Ghi chú vẽ
- Alt: email đã tồn tại; request/response rõ trên HTTP

---

### 4.2. Đăng nhập

#### 4.2.1. Thông tin tổng quan
- **Màn hình:** `AuthActivity` (mode login)
- **API:** POST `/api/auth/login`
- **Backend:** `auth.controller.login` → `getUserByEmailWithPasswordHash` → bcrypt
- **Bảng:** `users`
- **Kết quả:** JWT + user → `MainActivity`; nếu đã login `onCreate` skip thẳng Main

#### 4.2.2. Luồng chính
1. User nhập email/password → `AuthViewModel.login()`
2. `AuthRepository.login` → POST `/api/auth/login`
3. Backend so khớp `password_hash` → `signToken`
4. `SessionManager.saveSession` → `MainActivity`

#### 4.2.3. Lỗi
- 401 Sai email/mật khẩu
- 400 Invalid payload
- Mạng: Toast lỗi

#### 4.2.4. Participants
Giống 4.1 (login thay register)

---

### 4.3. Đăng xuất

#### 4.3.1. Thông tin tổng quan
- **Màn hình:** `ProfileFragment.setupLogout()`
- **API khai báo:** POST `/api/auth/logout` — **Android không gọi**
- **Kết quả:** `SessionManager.clearSession()` → `AuthActivity` (CLEAR_TASK)

#### 4.3.2. Luồng chính (thực tế trong app)
1. User xác nhận đăng xuất
2. `SessionManager.clearSession()` (EncryptedSharedPreferences)
3. Start `AuthActivity` — **không** gọi backend

#### 4.3.3. Ghi chú
- Backend `logout` chỉ trả `apiOk` — stateless JWT

---

### 4.4. Xem danh sách địa điểm

#### 4.4.1. Thông tin tổng quan
- **Màn hình:** `DestinationListFragment`, `HomeFragment` (featured/nearby)
- **ViewModel:** `DestinationViewModel`, `HomeViewModel`
- **Repository:** `DestinationRepository`
- **API:** GET `/api/destinations`, `/destinations/featured`, `/destinations/nearby`
- **Backend:** `destinations.controller` → `destinations.service` → `destinations.repository` (`app_places`, `place_images`, optional `favorites`)
- **Auth:** Optional JWT (Android vẫn gửi Bearer nếu có)

#### 4.4.2. Luồng chính (tab Khám phá)
1. User mở tab → `DestinationListFragment`
2. `DestinationViewModel.loadDestinations(page=1)`
3. GET `/api/destinations?limit&page`
4. MySQL SELECT `app_places` (+ images, is_favorite nếu có user)
5. Hiển thị `DestinationAdapter`; scroll load more

---

### 4.5. Tìm kiếm/lọc địa điểm

#### 4.5.1. Thông tin tổng quan
- **Màn hình:** `DestinationListFragment.setupSearch()`, category chips
- **API:** GET `/api/destinations?search=` hoặc `?category=`
- **Backend:** `listDestinations` filter SQL

#### 4.5.2. Luồng chính
1. User gõ search → `viewModel.search(query)` → `loadDestinations(search=query)`
2. User chọn chip category → `loadDestinations(category=beach|mountain|...)`
3. Cùng endpoint list với query params khác nhau

#### 4.5.3. Ghi chú
- **Province filter:** param `province` có trên API — **CHƯA XÁC MINH** UI Android có gọi province hay không (chủ yếu category + search)

---

### 4.6. Xem chi tiết địa điểm

#### 4.6.1. Thông tin tổng quan
- **Màn hình:** `DestinationDetailFragment` (arg `destinationId`)
- **API:** GET `/api/destinations/:id`
- **Bảng:** `app_places`, `place_images`
- **Kết quả:** Mô tả, ảnh, rating, nút yêu thích, đánh giá, map, thời tiết, thêm vào lịch trình

#### 4.6.2. Luồng chính
1. Navigation từ list/home → `destinationDetailFragment`
2. `DestinationViewModel.loadDetail(id)`
3. GET detail → hiển thị; `loadReviews(id)`; `loadWeather(city)` (mục 4.13)

---

### 4.7. Thêm địa điểm yêu thích

- **Màn hình:** `HomeFragment`, `DestinationDetailFragment`
- **API:** POST `/api/users/favorites` body `{ destinationId }`
- **Bảng:** INSERT `favorites`
- **Luồng:** `toggleFavorite` / `addFavorite` → repository → backend `favorites.service` kiểm tra `app_places` tồn tại

---

### 4.8. Xóa địa điểm yêu thích

- **API:** DELETE `/api/users/favorites/:destinationId`
- **Bảng:** DELETE `favorites`

---

### 4.9. Xem danh sách yêu thích

- **Màn hình:** `DestinationListFragment` (`isFavoriteOnly=true`) từ Profile hoặc nav
- **API:** GET `/api/users/favorites`
- **SQL:** `favorites` JOIN `app_places`

---

### 4.10. Gửi đánh giá địa điểm

#### 4.10.1. Thông tin tổng quan
- **UI:** `ReviewDialog` trong `DestinationDetailFragment`
- **API:** POST `/api/reviews` (JSON hoặc multipart images)
- **Backend:** `reviews.controller.createReview` → `reviews.repository` → UPDATE `app_places.rating`, `review_count`
- **Auth:** JWT bắt buộc

#### 4.10.2. Luồng chính
1. User chọn sao + comment (+ ảnh) → `DestinationViewModel.postReview`
2. POST `/api/reviews`
3. INSERT `reviews`; recalc rating trên `app_places`
4. Reload reviews list

---

### 4.11. Xem đánh giá địa điểm

- **API:** GET `/api/destinations/:id/reviews` (JWT)
- **UI:** `ReviewAdapter` trên detail

---

### 4.12. Xem bản đồ/vị trí địa điểm

#### 4.12.1. Thông tin tổng quan
- **Màn hình:** `MapFragment` (args lat, lng, name)
- **Dịch vụ ngoài:** OSMDroid `TileSourceFactory.MAPNIK`; `MapIntentHelper` → Google Maps
- **API backend:** Không

#### 4.12.2. Luồng chính
1. Từ detail bấm bản đồ → navigate `mapFragment` với tọa độ từ `Destination`
2. `MapFragment` hiển thị marker + load OSM tiles
3. (Tuỳ chọn) intent mở Google Maps chỉ đường

---

### 4.13. Xem thời tiết

#### 4.13.1. Thông tin tổng quan
- **Màn hình:** `DestinationDetailFragment.loadWeather(city)`
- **Service:** `WeatherService.getWeather()` → `https://api.open-meteo.com/v1/forecast`
- **Backend:** **Không** — gọi trực tiếp từ Android
- **Tọa độ:** Map tĩnh `cityCoords` trong `WeatherService.kt` (không dùng Nominatim dù comment gợi ý)

#### 4.13.2. Luồng chính
1. Detail load → coroutine `WeatherService.getWeather(destination.city)`
2. HTTP Open-Meteo → parse JSON → hiển thị nhiệt độ + forecast 5 ngày

---

### 4.14. Tạo lịch trình thủ công

- **UI:** `CreateItineraryDialog` trên `ItineraryFragment`
- **ViewModel:** `ItineraryViewModel.createItinerary`
- **API:** POST `/api/itineraries` (`CreateItineraryRequest`)
- **Bảng:** INSERT `itineraries`, `itinerary_days` (theo service)

---

### 4.15. Xem danh sách lịch trình

- **UI:** `ItineraryFragment`, `profileItineraryListFragment`
- **API:** GET `/api/itineraries`
- **Bảng:** `itineraries` WHERE `user_id`

---

### 4.16. Xem chi tiết lịch trình

- **UI:** `ItineraryDetailFragment` (arg `itineraryId`)
- **API:** GET `/api/itineraries/:id`
- **Bảng:** `itineraries`, `itinerary_days`, `itinerary_items` JOIN `app_places`

---

### 4.17. Xóa/sửa lịch trình

| Thao tác | UI | API |
|----------|-----|-----|
| Sửa meta | `EditItineraryDialog` | PUT `/api/itineraries/:id` |
| Xóa lịch | swipe/list | DELETE `/api/itineraries/:id` |
| Thêm/sửa/xóa điểm | `AddItineraryStopBottomSheet`, detail UI | POST/PUT/DELETE items |
| Thêm/xóa ngày | detail UI | POST/DELETE days |

---

### 4.18. Gợi ý lịch trình bằng AI/RAG (luồng chính — màn hình riêng)

#### 4.18.1. Thông tin tổng quan
- **Luồng UI active:** `ItineraryFragment` btn AI → `AIItineraryRequestFragment` → `AIItineraryOptionsFragment` → `AIItineraryEditorFragment`
- **API:** POST `/api/ai/itinerary-options` → FastAPI `/ai/itinerary-options`
- **Files:** `AIItineraryRequestFragment.kt`, `ItineraryViewModel.getAIItineraryOptions`, `ai.service.requestItineraryOptions`

#### 4.18.2. Luồng chính
1. User điền title, dates, budget, province, preferences → gọi options
2. Android → Node → RAG sinh danh sách `AIItineraryOption`
3. `AIItineraryOptionsFragment` hiển thị cards → chọn tour → navigate editor

#### 4.18.3. Ghi chú kỹ thuật
- RAG có thể trả template/mock tùy `AI_RUNTIME_MODE` — ghi chú phụ trên diagram AI service

#### 4.18.4. Luồng phụ / legacy (trong code, khó reach)
- `ItineraryFragment.showAIPlannerDialog()` — **không có caller** (dead code)
- `AISuggestFragment` + nav `action_itineraryFragment_to_aiSuggestFragment` — **không thấy navigate()**
- Inline dialog `showAITourOptionsDialog` chỉ chạy nếu `getAIItineraryOptions` từ dead dialog

---

### 4.19. Tạo lịch trình từ option AI

#### 4.19.1. Thông tin tổng quan
- **Màn hình:** `AIItineraryEditorFragment.createItineraryFromEditedOption()`
- **API:** POST `/api/itineraries/create-from-option`
- **Backend:** `itineraries.service` + `placeIdMap.repository.resolvePlaceId` → INSERT itinerary structure
- **Bảng:** `place_id_map`, `app_places`, `itineraries`, `itinerary_days`, `itinerary_items`

#### 4.19.2. Luồng chính
1. User chỉnh checkbox địa điểm theo ngày → bấm tạo
2. `ItineraryViewModel.createItineraryFromOption`
3. Node map `rawPlaceId` → `app_places.id` → persist
4. Toast success → pop về `itineraryFragment`

**Chatbot shortcut:** `ChatbotFragment.openChatbotItineraryEditor` build `AIItineraryOption` từ RAG `places` → navigate thẳng `aiItineraryEditorFragment` → cùng API create-from-option.

---

### 4.20. Tạo lịch trình từ selection

#### 4.20.1. Thông tin tổng quan
- **API:** POST `/api/itineraries/create-from-selection` — **có** backend + `ItineraryRepository`
- **Android UI:** `ItineraryFragment.showAISuggestionsDialog` → `createItineraryFromSelection` — **CHƯA REACH** vì `previewAIItinerary()` không được gọi từ UI

**Kết luận:** Endpoint tồn tại; luồng nghiệp vụ trên app **KHÔNG THẤY TRONG CODE** (dead path) trừ khi tích hợp sau.

---

### 4.21. Chatbot tư vấn du lịch

#### 4.21.1. Thông tin tổng quan
- **Màn hình:** `ChatbotFragment`
- **ViewModel:** `ChatbotViewModel` (không repository)
- **Services:** `RagService`, `GeminiService`
- **API:** POST `/api/ai/rag-chat` (chính), POST `/api/ai/chat` (prepare, validate, repair, fallback)

#### 4.21.2. Luồng chính (rút gọn)
1. User gửi tin → `ChatbotViewModel.sendMessage`
2. `prepareRagQuery` → POST `/api/ai/chat` (chuẩn hóa JSON)
3. `RagService.chat` → POST `/api/ai/rag-chat` → Node → FastAPI `/rag/chat/simple`
4. Nếu province mismatch → gọi lại RAG strict query (opt loop)
5. `validateRagOutputFull` → có thể gọi lại RAG hoặc `repairRagAnswer` qua `/api/ai/chat`
6. Nếu RAG fail → `fallbackChat` → `/api/ai/chat`
7. Hiển thị `ChatMessage` + optional `places` → nút tạo lịch trình

#### 4.21.3. Lỗi
- 401: message phiên hết hạn (trong `GeminiService`)
- 502/RAG down: fallback hoặc thông báo kiểm tra port 8001
- Mạng: message lỗi trong chat

#### 4.21.4. Participants
User → ChatbotFragment → ChatbotViewModel → RagService/GeminiService → Node → FastAPI RAG → (file index) → Node → Android

#### 4.21.5. Ghi chú vẽ
- **Alt/loop:** retry RAG, validation branch, fallback
- Không vẽ mock/template như bước nghiệp vụ user-facing

---

### 4.22. Xem/cập nhật hồ sơ cá nhân

#### 4.22.1. Thông tin tổng quan
- **Màn hình:** `ProfileFragment`, `SettingsFragment` (placeholder)
- **API dùng:** GET `/users/stats`, PUT `/users/profile`, POST `/users/avatar`
- **Không dùng:** GET `/users/profile`, PUT `/users/preferences`

#### 4.22.2. Luồng cập nhật profile
1. Dialog edit name/phone → cập nhật local `SessionManager` trước
2. PUT `/users/profile` nền
3. Avatar: picker → multipart POST `/users/avatar` → cập nhật Glide + session

---

### 4.23. Admin đăng nhập

#### 4.23.1. Thông tin tổng quan
- **Không có** trang login HTML riêng
- **Cơ chế:** Browser HTTP Basic khi truy cập `/admin/*` nếu `ADMIN_BASIC_USER` + `ADMIN_BASIC_PASS` set (`adminAuth.middleware.js`)
- Nếu không set env → **passthrough** (cảnh báo dev)

---

### 4.24. Admin quản lý người dùng

- **Route:** GET `/admin/users`, GET `/admin/users/api/:id`, POST save, POST delete
- **Repository:** `users.repository.js` (admin methods)
- **Bảng:** `users`

---

### 4.25. Admin quản lý địa điểm

- **Route:** `/admin/destinations*`
- **Bảng:** `app_places` CRUD
- **Không** quản `place_images` riêng trên form admin — **CHƯA XÁC MINH** upload ảnh admin

---

### 4.26. Admin quản lý đánh giá

**KHÔNG THẤY TRONG CODE** — không có route/template admin cho `reviews`. Chỉ mobile API.

---

### 4.27. Admin quản lý dữ liệu RAG/AI

- **Trang:** `/admin/rag-ai` — hiển thị status, data quality (proxy)
- **Thao tác:** POST reload place-store, clear cache (proxy FastAPI)
- **Không** CRUD trực tiếp bảng `rag_knowledge_base` trên UI admin

---

### 4.28. Admin giám sát RAG AI

- **UI:** `/admin/rag-ai` SSR + fetch `/admin/rag-ai/ai-metrics`, `/admin/rag-ai/ai-logs`
- **Upstream:** FastAPI `GET /admin/ai/metrics`, `/admin/ai/logs` (file `ai_request_logs.jsonl`)

---

### 4.29. Admin debug truy vấn RAG

- **UI:** form debug trên `ragAi.content.html`
- **Route:** POST `/admin/rag-ai/debug-query` body `{ message }`
- **Proxy:** FastAPI `POST /admin/ai/debug-query` → full `RagPipeline.run` debug payload

---

## 5. Flow cho biểu đồ hoạt động

### 5.1. Đăng ký
- **Start:** Mở app chưa login
- **Activity:** `AuthActivity` register mode
- **Decision:** Email đã tồn tại?
  - Đúng: Toast lỗi → End (ở Auth)
  - Sai: Lưu session → **End:** `MainActivity`

### 5.2. Đăng nhập
- **Start:** Auth login mode
- **Decision:** Credentials OK?
  - Sai: Hiển thị lỗi
  - Đúng: Session → Main

### 5.3. Tìm kiếm địa điểm
- **Start:** `DestinationListFragment`
- **Activity:** Nhập search / chọn category
- **Activity:** Gọi API list
- **Decision:** Có kết quả?
  - Không: empty state
  - Có: hiển thị list → **End** hoặc tap → Detail

### 5.4. Xem chi tiết địa điểm
- **Start:** Tap card
- **Activity:** Load detail + reviews + weather (parallel)
- **End:** User back hoặc chuyển Map/Favorite/Review

### 5.5. Xem bản đồ
- **Start:** Detail → Map
- **Activity:** Render OSM
- **End:** Back

### 5.6. Xem thời tiết
- **Start:** Detail loaded
- **Activity:** Open-Meteo request
- **Decision:** City trong `cityCoords`?
  - Không rõ: default Hà Nội coords
- **End:** Hiển thị forecast

### 5.7. Quản lý lịch trình
- **Start:** Tab Lịch trình
- **Decision:** Tạo mới / Xem / Sửa / Xóa / AI?
- Nhánh thủ công: Dialog → POST create → refresh list
- Nhánh chi tiết: Detail → edit items/days

### 5.8. Gợi ý lịch trình AI/RAG
- **Start:** Btn AI trên `ItineraryFragment`
- **Activity:** Request form → options API
- **Decision:** Có options?
  - Không: Toast
  - Có: chọn option → editor → create-from-option
- **End:** Pop stack về list itineraries

### 5.9. Chatbot
- **Start:** Tab Chatbot
- **Activity:** Send message
- **Decision:** RAG OK?
  - Không: fallback chat
  - Có: validate → có thể retry
- **End:** Hiển thị reply; optional tạo lịch từ places

### 5.10. Đánh giá địa điểm
- **Start:** Detail → Review dialog
- **Decision:** Đã login?
  - Không: **CHƯA XÁC MINH** guard UI — API 401 nếu gọi
- **Activity:** POST review → reload

### 5.11. Quản trị dữ liệu admin
- **Start:** Browser `/admin`
- **Decision:** Basic auth OK?
- **Activity:** CRUD users/destinations HTML forms
- **End:** Redirect/list refresh

### 5.12. Giám sát/debug RAG
- **Start:** `/admin/rag-ai`
- **Activity:** Load metrics/logs; user POST debug query
- **End:** Hiển thị JSON debug response

---

## 6. Flow cho BPMN nghiệp vụ

### 6.1. Đăng ký/đăng nhập
**Swimlane:** Người dùng | Android | Backend | MySQL

1. Người dùng nhập thông tin đăng ký/đăng nhập  
2. Android gửi yêu cầu auth  
3. Backend xác thực / tạo user, phát JWT  
4. MySQL lưu/đọc `users`  
5. Android lưu token, vào trang chủ  

**Rẽ nhánh:** Email trùng / sai mật khẩu → thông báo lỗi

### 6.2. Tìm kiếm và xem thông tin địa điểm
1. Người dùng tìm/lọc/xem danh sách  
2. Android gọi GET destinations  
3. Backend truy vấn `app_places`  
4. Người dùng mở chi tiết → GET by id + reviews  

### 6.3. Xem bản đồ và thời tiết
1. Từ chi tiết, mở bản đồ → Android + OSM (không backend)  
2. Thời tiết → Android + Open-Meteo (không backend)  

### 6.4. Tạo/quản lý lịch trình
1. Người dùng tạo/sửa lịch  
2. Android gọi itineraries API (JWT)  
3. Backend ghi `itineraries` / days / items  
4. MySQL persist  

### 6.5. Gợi ý lịch trình bằng AI/RAG
1. Người dùng nhập yêu cầu tour  
2. Android → Backend → FastAPI sinh options  
3. Người dùng chọn phương án, chỉnh địa điểm  
4. Backend map place id + lưu lịch  

**Rẽ nhánh:** RAG lỗi → thông báo / không có option

### 6.6. Chatbot tư vấn du lịch
1. Người dùng chat  
2. Android chuẩn hóa câu hỏi (AI chat API)  
3. RAG trả lời + danh sách địa điểm  
4. (Tuỳ chọn) Tạo lịch từ gợi ý  

### 6.7. Đánh giá địa điểm
1. Người dùng gửi đánh giá  
2. Backend lưu `reviews`, cập nhật rating `app_places`  

### 6.8. Quản trị dữ liệu hệ thống
1. Admin đăng nhập Basic (nếu bật)  
2. Quản lý users / `app_places` qua web  
3. Không có BPMN reviews admin  

### 6.9. Giám sát/debug RAG
1. Admin mở trang RAG  
2. Backend proxy metrics/debug tới FastAPI  
3. Admin xem log / chạy debug query  

---

## 7. Các mismatch/rủi ro cần hỏi lại người dùng

| Vấn đề | File phát hiện | Mức độ | Cần hỏi |
|--------|----------------|--------|---------|
| Android không gọi `POST /auth/logout` | `ProfileFragment.kt`, `ApiService.kt` | Thấp | Có cần invalidate phía server không? |
| `GET/PUT users/profile`, `PUT preferences` khai báo nhưng không dùng | `ApiService.kt` | Thấp | Có bỏ hay implement refresh profile? |
| `POST /ai/itinerary-preview` + `create-from-selection` — UI dead | `ItineraryViewModel`, `ItineraryFragment` | Trung bình | Luồng báo cáo dùng Request→Options→Editor hay preview/selection? |
| `AISuggestFragment` trong nav nhưng không `navigate()` | `nav_graph.xml`, `ItineraryFragment.kt` | Trung bình | Còn hỗ trợ legacy suggest+save-ai không? |
| `favorites.destination_id` FK legacy `destinations` nhưng JOIN `app_places` | `database.sql`, `favorites.repository.js` | Trung bình | DB prod đã migrate FK sang `app_places` chưa? |
| Bảng `users` không có trong migrations 001–011 | `database/migrations/`, `011` FK | Cao (deploy) | Bootstrap chỉ `database.sql` hay full migrations? |
| `com.smarttravel` duplicate sources | `app/src/main/java/com/smarttravel/` | Thấp | Có exclude khỏi build không? |
| RAG `AI_RUNTIME_MODE` mock vs `.env.example` demo | `config.py`, `.env.example` | Cao (demo thesis) | Biểu đồ ghi rõ mode deploy thực tế? |
| Admin `/admin` mở nếu thiếu Basic auth | `adminAuth.middleware.js` | Cao (security) | Prod có bắt buộc ADMIN_BASIC_*? |
| Không có admin quản lý reviews | `admin/index.js` | Trung bình | Có cần thêm UC admin reviews? |
| Weather không qua backend | `WeatherService.kt` | Thấp | Chương 2 có cần API weather riêng? |
| `BuildConfig.GEMINI_API_KEY` không dùng trên device | `build.gradle` | Thấp | Chỉ RAG server cần `GEMINI_API_KEY` |

---

## 8. Kết luận dùng để vẽ biểu đồ Chương 2

### Biểu đồ trình tự nên vẽ (ưu tiên)
1. Đăng ký / Đăng nhập  
2. Xem danh sách + chi tiết địa điểm  
3. Thêm/xóa yêu thích + danh sách yêu thích  
4. Gửi và xem đánh giá  
5. Xem bản đồ (OSM)  
6. Xem thời tiết (Open-Meteo — tách participant ngoài)  
7. CRUD lịch trình thủ công (gộp hoặc tách create/detail)  
8. Gợi ý lịch trình AI: Request → Options → Editor → create-from-option  
9. Chatbot (RAG + fallback + optional tạo lịch)  
10. Cập nhật hồ sơ + avatar  
11. Admin: quản lý user/destination (Basic auth)  
12. Admin: debug/monitor RAG (proxy)  

**Không ưu tiên / ghi chú:** logout server, preview/selection dead paths, legacy AISuggestFragment.

### Biểu đồ hoạt động
- 5.1–5.12 tương ứng các nhánh trên (gộp đăng ký/đăng nhập nếu cần gọn).

### Use Case
- Actor: Người dùng, Quản trị viên, Hệ thống RAG  
- UC user: §3.1 (bỏ hoặc dashed: logout server, settings, selection preview)  
- UC admin: §3.2 (không reviews admin)  
- UC AI: §3.3  

### BPMN
- §6.1–6.9 (9 quy trình)  

### ERD (bảng đưa vào)
- **Core runtime:** `users`, `app_places`, `place_images`, `favorites`, `reviews`, `itineraries`, `itinerary_days`, `itinerary_items`  
- **Mapping/AI data:** `place_id_map`, `rag_knowledge_base` (offline/RAG export)  
- **Legacy (ghi chú / dashed):** `destinations` nếu vẫn tồn tại DB cũ  

---

## Phụ lục: File tham chiếu nhanh

| Layer | Path |
|-------|------|
| Android API | `app/src/main/java/com/unutrip/data/api/ApiService.kt` |
| Repositories | `app/src/main/java/com/unutrip/data/repository/Repositories.kt` |
| Navigation | `app/src/main/res/navigation/nav_graph.xml` |
| Node entry | `backend/nodejs/src/index.js`, `src/app.js` |
| Node API router | `backend/nodejs/src/api/router.js` |
| Node admin | `backend/nodejs/src/admin/index.js` |
| RAG entry | `backend/rag/app/main.py` |
| DB migrations | `database/migrations/` |
| Legacy schema | `backend/nodejs/database.sql` |
| Env template | `.env.example` |
