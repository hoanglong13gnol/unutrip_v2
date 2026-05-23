# UNUTrip / SmartTravel — Actors & Use Case (bám sát code)

> Tài liệu xác định **actor hợp lệ** và **use case** cho biểu đồ Use Case tổng quát và phân rã.  
> Nguồn: code thật, route thật, module thật trong repo `UNUtrip_v2`.  
> Ứng dụng đang chạy: `com.unutrip` (`AndroidManifest.xml`, `nav_graph.xml`). Package `com.smarttravel` không dùng trong manifest/nav.

---

## A. Phạm vi hệ thống nên chọn cho báo cáo

| Hạng mục | Nội dung |
|----------|----------|
| **Tên hệ thống** | **Hệ thống phần mềm UNUTrip (SmartTravel)** — nền tảng gợi ý du lịch end-to-end |
| **Thành phần bên trong phạm vi hệ thống** | **Ứng dụng Android** (`app/`, `com.unutrip`): Activity/Fragment, ViewModel, Repository, Retrofit `ApiService`, `WeatherService`, OSMDroid UI, `SessionManager`. **Backend Node.js/Express** (`backend/nodejs`): `/api/*`, `/admin/*`, middleware JWT/Basic, service/repository, proxy RAG. **Dịch vụ RAG FastAPI** (`backend/rag`): `/rag/*`, `/ai/*`, `/admin/*` (monitoring) — triển khai cùng stack (`docker-compose.yml`). **MySQL** (`unudata`, migrations `database/migrations/`). **Redis** (cache RAG, nếu bật trong compose). **Lưu trữ file** (`uploads/`, `public/images/`). |
| **Thành phần bên ngoài phạm vi hệ thống** | **Người dùng cuối** (tương tác qua Android). **Quản trị viên** (trình duyệt → `/admin/*`). **Open-Meteo** (HTTP từ Android). **Máy chủ tile OpenStreetMap** (OSMDroid). **Google Maps** (intent / URL ngoài app). **Dịch vụ vị trí thiết bị** (Google Play Services `FusedLocationProviderClient`). **Google Gemini API** (chỉ FastAPI RAG gọi qua `GeminiProvider` / `gemini_generator.py`). |

### Phạm vi đề xuất

Một **biên hệ thống duy nhất**: Android + Node + RAG + MySQL (như `docker-compose.yml`). Không tách Android hay Backend thành “hệ thống” riêng trên sơ đồ Use Case tổng quát.

### FastAPI RAG — actor hay phân hệ nội bộ?

**→ Phân hệ nội bộ, không vẽ actor.**

- Android **không** gọi cổng 8001; mọi AI đi qua Node (`RagService.kt` → `POST /api/ai/*`; `ragUpstream.js` → `RAG_BASE_URL`).
- Admin proxy qua Node (`admin/ragAi.admin.routes.js` → `fetchRagJson`).
- RAG và Node cùng sản phẩm triển khai (`docker-compose.yml` service `rag`).

### Gemini

- **Ngoài biên** hệ thống (API Google).
- **Không bắt buộc** trên Use Case tổng quát (ẩn sau UC Chatbot / Gợi ý AI).
- Chỉ thêm actor **API Gemini** ở biểu đồ **phân rã AI** nếu cần thể hiện phụ thuộc LLM.

---

## B. Danh sách actor hợp lệ

### 1. Người dùng (Khách du lịch)

| | |
|--|--|
| **Dùng trong UC tổng quát** | **Có** |
| **Lý do** | Thực thể người thật; tương tác nghiệp vụ mobile qua `AuthActivity`, `MainActivity`, Fragment trong `nav_graph.xml`. |
| **Bằng chứng** | `app/src/main/res/navigation/nav_graph.xml`; `AuthActivity.kt`; `HomeFragment.kt`, `ProfileFragment.kt`, `ChatbotFragment.kt`, `ItineraryFragment.kt`; `SessionManager.kt`; `backend/nodejs/src/modules/*/*.routes.js`. |

### 2. Quản trị viên

| | |
|--|--|
| **Dùng trong UC tổng quát** | **Có** |
| **Lý do** | Vai trò khác người dùng: HTML `/admin/*`, HTTP Basic (`ADMIN_BASIC_USER` / `ADMIN_BASIC_PASS`), không dùng app Android. |
| **Bằng chứng** | `backend/nodejs/src/app.js`; `middlewares/adminAuth.middleware.js`; `admin/dashboard.admin.routes.js`, `users.admin.routes.js`, `destinations.admin.routes.js`, `ragAi.admin.routes.js`. |

### 3. Dịch vụ thời tiết (Open-Meteo)

| | |
|--|--|
| **Dùng trong UC tổng quát** | **Có** (actor phụ / secondary) — khi sơ đồ có UC “Xem thời tiết địa điểm” |
| **Lý do** | Android gọi HTTP trực tiếp ra ngoài, không qua backend. |
| **Bằng chứng** | `app/src/main/java/com/unutrip/utils/WeatherService.kt` (`https://api.open-meteo.com/v1/forecast`); `DestinationDetailFragment.kt`; `ApiService.kt` (weather đã bỏ khỏi API). |

### 4. Dịch vụ bản đồ OpenStreetMap (tile server)

| | |
|--|--|
| **Dùng trong UC tổng quát** | **Có** (secondary) — khi có UC “Xem bản đồ địa điểm (trong app)” |
| **Lý do** | OSMDroid tải tile MAPNIK từ OSM. |
| **Bằng chứng** | `MapFragment.kt` (`TileSourceFactory.MAPNIK`); `fragment_map.xml`; `app/build.gradle` (`osmdroid-android`). |

### 5. Ứng dụng / dịch vụ Google Maps

| | |
|--|--|
| **Dùng trong UC tổng quát** | **Có** (secondary) — khi có UC “Mở địa điểm / chỉ đường trên Google Maps” |
| **Lý do** | `MapIntentHelper` khởi chạy intent/URL ra app hoặc web Google Maps. |
| **Bằng chứng** | `MapIntentHelper.kt`; `MapFragment.kt` (`btnOpenGoogleMap`, `btnDirection`). |

### 6. Dịch vụ vị trí thiết bị (GPS / Fused Location)

| | |
|--|--|
| **Dùng trong UC tổng quát** | **Có** (secondary) — khi có UC “Xem địa điểm gần bạn” hoặc “Hiển thị vị trí hiện tại trên bản đồ” |
| **Lý do** | Tọa độ từ Google Play Services / quyền location, không phải logic nghiệp vụ thuần nội bộ. |
| **Bằng chứng** | `AndroidManifest.xml`; `HomeFragment.kt` (`FusedLocationProviderClient`, `getNearby`); `MapFragment.kt` (`lastLocation`). |

### 7. API Gemini (Google)

| | |
|--|--|
| **Dùng trong UC tổng quát** | **Không** (mặc định) / **Có** (chỉ biểu đồ phân rã AI) |
| **Lý do** | Chỉ RAG nội bộ gọi; người dùng/admin không gọi trực tiếp. |
| **Bằng chứng** | `backend/rag/providers/gemini_provider.py`; `GEMINI_API_KEY` trong `.env.example` / `docker-compose.yml`; Android `GeminiService.kt` chỉ gọi Node (`/api/ai/chat`). |

### 8. Dịch vụ AI/RAG (FastAPI) — nếu muốn vẽ riêng

| | |
|--|--|
| **Dùng trong UC tổng quát** | **Không** |
| **Lý do** | Thuộc cùng sản phẩm; chỉ Node gọi nội bộ. |
| **Bằng chứng** | `docker-compose.yml`; `backend/nodejs/src/lib/ragUpstream.js`; không có `RAG_BASE_URL` trong Android. |

---

## C. Những actor KHÔNG nên dùng

| Không dùng | Vì sao | Nên chuyển thành |
|------------|--------|------------------|
| **Hệ thống** | Actor phải ngoài biên; “hệ thống” là khối đang mô tả. | Boundary + use case bên trong. |
| **Backend Server / Node.js** | Thành phần triển khai nội bộ. | Gói «Backend API» trong biên; lifeline sequence. |
| **Android App / Ứng dụng di động** | Client của cùng hệ thống. | Gói «Ứng dụng Android» trong biên; actor ngoài là **Người dùng**. |
| **MySQL / Database / Repository** | Persistence nội bộ. | Lifeline «CSDL» trong sequence / component diagram. |
| **FastAPI RAG Service** (là actor) | Microservice nội bộ, proxy từ Node. | Phân hệ «Dịch vụ RAG» trong biên. |
| **ViewModel / Fragment / Controller** | Lớp kiến trúc trong app/backend. | Class / sequence diagram. |
| **Retrofit / ApiService** | Chi tiết triển khai. | Không trên Use Case. |
| **Redis** | Hạ tầng nội bộ. | Infrastructure. |
| **Tailwind CDN / Font Awesome** | CDN admin UI. | Bỏ qua hoặc ghi chú kỹ thuật. |

> **Lưu ý:** `ALL_SYSTEM_FLOWS_UNUTRIP.md` mục 0.3 liệt kê Android/Backend/MySQL/RAG là “actor” — **không phù hợp chuẩn Use Case UML**; dùng tài liệu này khi vẽ báo cáo.

---

## D. Use Case tổng quát đề xuất

Mỗi dòng = **một** use case (không gộp).

### Người dùng — Xác thực & hồ sơ

1. Đăng ký tài khoản  
2. Đăng nhập  
3. Đăng xuất *(chỉ xóa session local; API logout có nhưng app không gọi)*  
4. Xem thống kê hồ sơ cá nhân  
5. Cập nhật thông tin hồ sơ  
6. Tải lên ảnh đại diện  

### Người dùng — Địa điểm

7. Xem danh sách địa điểm  
8. Tìm kiếm địa điểm *(query `search`)*  
9. Lọc địa điểm theo danh mục / tỉnh  
10. Xem địa điểm nổi bật  
11. Xem địa điểm gần vị trí hiện tại  
12. Xem chi tiết địa điểm  
13. Thêm địa điểm vào yêu thích  
14. Xóa địa điểm khỏi yêu thích  
15. Xem danh sách địa điểm yêu thích  
16. Xem danh sách đánh giá của địa điểm  
17. Gửi đánh giá địa điểm *(kèm tối đa 3 ảnh)*  
18. Xem bản đồ địa điểm trong ứng dụng  
19. Mở địa điểm trên Google Maps  
20. Chỉ đường trên Google Maps  
21. Xem thời tiết địa điểm  

### Người dùng — Lịch trình (thủ công)

22. Tạo lịch trình  
23. Xem danh sách lịch trình  
24. Xem chi tiết lịch trình  
25. Cập nhật thông tin lịch trình  
26. Xóa lịch trình  
27. Thêm ngày vào lịch trình  
28. Xóa ngày khỏi lịch trình  
29. Thêm địa điểm vào lịch trình *(item)*  
30. Cập nhật mục lịch trình *(giờ, ghi chú)*  
31. Xóa mục khỏi lịch trình  

### Người dùng — AI / RAG

32. Yêu cầu gợi ý tour AI *(form → danh sách option)*  
33. Chọn và chỉnh sửa phương án tour AI  
34. Tạo lịch trình từ phương án AI đã chọn  
35. Tạo lịch trình từ danh sách địa điểm AI gợi ý *(dialog `create-from-selection`)*  
36. Gợi ý lịch trình AI kiểu legacy *(suggest + save-ai — code còn, UI nav tới `AISuggestFragment` không thấy `navigate()`)*  
37. Chatbot tư vấn du lịch  

### Người dùng — Khác

38. Mở màn hình cài đặt *(ngôn ngữ / thông báo / giao diện: toast “đang phát triển”)*  

### Quản trị viên

39. Truy cập khu vực quản trị *(HTTP Basic)*  
40. Xem bảng điều khiển thống kê  
41. Quản lý người dùng *(xem / tìm / sửa / xóa)*  
42. Quản lý địa điểm *(xem / tìm / thêm / sửa / xóa `app_places`)*  
43. Xem thông tin hệ thống  
44. Xem báo cáo AI tổng hợp  
45. Giám sát trạng thái RAG / AI  
46. Tải lại kho dữ liệu địa điểm RAG *(reload place store)*  
47. Xóa cache RAG  
48. Debug truy vấn RAG  
49. Xem log / metrics AI *(qua trang RAG admin)*  

### Không có trong code (không đưa vào UC chính)

- Quản lý đánh giá / hình ảnh đánh giá trên admin *(không route `/admin/reviews`)*  
- Quản lý ảnh địa điểm riêng trên admin *(admin destinations chỉ CRUD metadata `app_places`, không upload `place_images`)*  
- Cập nhật sở thích người dùng trên UI *(API `PUT /users/preferences` có, Android không gọi)*  
- Xem trước lịch trình AI `itinerary-preview` trên UI *(repo/VM có, không thấy UI gọi)*  

---

## E. Bảng mapping Actor — Use Case

**Chú thích cột Code:** `Có` = route/UI/logic đầy đủ; `Một phần` = API hoặc UI thiếu một đầu; `Legacy` = code còn, luồng UI chính không dùng.

### Actor: Người dùng

| Use Case | Code | File / route chứng minh | Ghi chú |
|----------|------|---------------------------|---------|
| Đăng ký | Có | `POST /api/auth/register` — `auth.routes.js`; `AuthActivity.kt`, `AuthRepository` | |
| Đăng nhập | Có | `POST /api/auth/login`; `AuthActivity.kt` | JWT → `SessionManager` |
| Đăng xuất | Một phần | `ProfileFragment.kt` (`clearSession`); `POST /api/auth/logout` — `ApiService.logout` không gọi | Chỉ local |
| Xem thống kê hồ sơ | Có | `GET /api/users/stats`; `ProfileFragment.kt` | |
| Cập nhật hồ sơ | Có | `PUT /api/users/profile`; `ProfileFragment.kt` | `GET /users/profile` không dùng |
| Tải avatar | Có | `POST /api/users/avatar`; `ProfileFragment.kt` | |
| Xem danh sách địa điểm | Có | `GET /api/destinations`; `DestinationListFragment.kt` | |
| Tìm kiếm địa điểm | Có | Query `search` — `destinations.routes.js` | |
| Lọc theo danh mục/tỉnh | Có | Query `category`, `province`; `HomeFragment` | |
| Địa điểm nổi bật | Có | `GET /api/destinations/featured`; `HomeViewModel.kt` | |
| Địa điểm gần bạn | Có | `GET /api/destinations/nearby`; `HomeFragment.kt` + GPS | Actor phụ: vị trí |
| Chi tiết địa điểm | Có | `GET /api/destinations/:id`; `DestinationDetailFragment.kt` | |
| Thêm yêu thích | Có | `POST /api/users/favorites`; `favorites.routes.js` | |
| Xóa yêu thích | Có | `DELETE /api/users/favorites/:id` | |
| Xem danh sách yêu thích | Có | `GET /api/users/favorites`; list `isFavoriteOnly=true` | |
| Xem đánh giá | Có | `GET /api/destinations/:id/reviews` | |
| Gửi đánh giá | Có | `POST /api/reviews` (multipart ≤3 ảnh) | |
| Bản đồ in-app | Có | `MapFragment.kt`; `nav_graph` detail→map | Actor phụ: OSM |
| Mở Google Maps | Có | `MapIntentHelper.openPlace` | |
| Chỉ đường Google Maps | Có | `MapIntentHelper.openRoute` / `openNavigation` | |
| Thời tiết | Có | `WeatherService.kt`; `DestinationDetailFragment.kt` | Actor phụ: Open-Meteo |
| Tạo lịch trình | Có | `POST /api/itineraries`; `ItineraryFragment` dialog | |
| Xem danh sách lịch trình | Có | `GET /api/itineraries`; `ItineraryFragment` | |
| Xem chi tiết lịch trình | Có | `GET /api/itineraries/:id`; `ItineraryDetailFragment` | |
| Cập nhật lịch trình | Có | `PUT /api/itineraries/:id`; `ItineraryViewModel.updateItineraryMeta` | |
| Xóa lịch trình | Có | `DELETE /api/itineraries/:id` | |
| Thêm ngày | Có | `POST /api/itineraries/:id/days` | |
| Xóa ngày | Có | `DELETE /api/itineraries/:id/days/:dayId` | |
| Thêm mục lịch trình | Có | `POST /api/itineraries/:id/items` | |
| Cập nhật mục | Có | `PUT /api/itineraries/:id/items/:itemId` | |
| Xóa mục | Có | `DELETE /api/itineraries/:id/items/:itemId` | |
| Gợi ý tour AI (32) | Có | `AIItineraryRequestFragment`; `POST /api/ai/itinerary-options` | |
| Chỉnh tour AI (33) | Có | `AIItineraryEditorFragment` | |
| Tạo lịch từ option (34) | Có | `POST /api/itineraries/create-from-option` | |
| Tạo từ selection (35) | Có | `ItineraryFragment` dialog; `POST /api/itineraries/create-from-selection` | |
| Legacy suggest (36) | Legacy | `AISuggestFragment` trong `nav_graph`; `suggestItinerary` + `save-ai`; không `navigate()` tới fragment | |
| Chatbot (37) | Có | `ChatbotFragment`; `POST /api/ai/rag-chat`, `/api/ai/chat` | |
| Cài đặt (38) | Một phần | `SettingsFragment.kt` | Placeholder toast |

### Actor: Quản trị viên

| Use Case | Code | File / route | Ghi chú |
|----------|------|--------------|---------|
| Truy cập admin | Có | `adminAuth.middleware.js`; `app.js` `/admin` | Không env → mở (dev) |
| Dashboard (40) | Có | `GET /admin/dashboard` — `dashboard.admin.routes.js` | |
| Quản lý users (41) | Có | `users.admin.routes.js` — list, api, save, delete | |
| Quản lý địa điểm (42) | Có | `destinations.admin.routes.js` | Không `place_images` |
| System (43) | Có | `GET /admin/system` — `system.admin.routes.js` | |
| Báo cáo AI (44) | Có | `GET /admin/ai-report` — `aiReport.admin.routes.js` | |
| Giám sát RAG (45) | Có | `GET /admin/rag-ai` — `ragAi.admin.routes.js` | |
| Reload place store (46) | Có | `POST /admin/rag-ai/reload-place-store` | |
| Xóa cache (47) | Có | `POST /admin/rag-ai/clear-cache` | |
| Debug query (48) | Có | `POST /admin/rag-ai/debug-query` | |
| Log / metrics (49) | Có | `GET /admin/rag-ai/ai-logs`, `ai-metrics` | |

### Actor phụ (secondary)

| Use Case | Actor phụ | Bằng chứng |
|----------|-----------|------------|
| 21 — Thời tiết | Open-Meteo | `WeatherService.kt` |
| 18 — Bản đồ in-app | OpenStreetMap | `MapFragment.kt` MAPNIK |
| 19–20 — Google Maps | Google Maps | `MapIntentHelper.kt` |
| 11, 18 — Vị trí | Dịch vụ vị trí thiết bị | `HomeFragment.kt`, `MapFragment.kt` |
| 32–37 — LLM | Gemini *(phân rã AI)* | `gemini_provider.py` |

### API Node `/api` (tham chiếu nhanh)

| Nhóm | Routes | File |
|------|--------|------|
| Health | `GET /health`, `/health/ready` | `health.routes.js` |
| Auth | `POST /auth/register`, `/login`, `/logout` | `auth.routes.js` |
| User | `GET/PUT /users/profile`, `/stats`, `/preferences`, `POST /avatar` | `users.routes.js` |
| Favorites | `GET/POST /users/favorites`, `DELETE .../:id` | `favorites.routes.js` |
| Destinations | `GET /destinations`, `/featured`, `/nearby`, `/:id` | `destinations.routes.js` |
| Reviews | `GET /destinations/:id/reviews`, `POST /reviews` | `reviews.routes.js` |
| Itineraries | CRUD + days/items + `save-ai` | `itineraries.routes.js` |
| AI | `/ai/suggest-itinerary`, `/rag-chat`, `/chat`, `/itinerary-preview`, `/itinerary-options`, `create-from-option`, `create-from-selection` | `ai.routes.js` |

### RAG FastAPI (nội bộ — Node proxy, Android không gọi trực tiếp)

| Endpoint | Gọi bởi |
|----------|---------|
| `POST /rag/chat/simple` | Node `/api/ai/rag-chat`, `/api/ai/chat` |
| `POST /ai/itinerary-options` | Node `/api/ai/itinerary-options` |
| `GET/POST /admin/ai/*`, `/admin/rag/*` | Node `/admin/rag-ai/*` |

---

## F. Kết luận cuối

### Danh sách actor nên dùng

#### Biểu đồ Use Case **tổng quát** (khuyến nghị)

| Loại | Actor |
|------|--------|
| **Chính (bắt buộc)** | **Người dùng**, **Quản trị viên** |
| **Phụ (khi sơ đồ có UC 11, 18–21)** | **Dịch vụ thời tiết (Open-Meteo)**; **Dịch vụ bản đồ (OpenStreetMap)**; **Google Maps**; **Dịch vụ vị trí thiết bị** |

#### Không dùng trên tổng quát

Hệ thống, Backend, Android App, MySQL, FastAPI RAG, Redis, ViewModel, Repository.

#### Chỉ 2 actor User + Admin?

- **Đủ** cho nghiệp vụ chính (auth, địa điểm, lịch trình, AI, admin).
- **Nên bổ sung actor phụ** cho UC bản đồ / thời tiết / GPS vì code gọi **trực tiếp ra ngoài**, không qua Node API.

#### Dịch vụ AI/RAG

- **Không** làm actor trên tổng quát → phân hệ **nội bộ**.
- Người dùng kích hoạt UC **Chatbot** / **Gợi ý tour AI**.

#### Gemini

- Actor **ngoài** thật; **ẩn** ở tổng quát; vẽ ở **phân rã module AI** nếu cần.

### Gợi ý phân rã biểu đồ

| Biểu đồ phân rã | Actor |
|-----------------|--------|
| Mobile (Android) | Người dùng + Open-Meteo + OSM + Google Maps + Vị trí |
| REST API (Node) | Người dùng *(qua app)* + Quản trị viên; RAG = lifeline nội bộ |
| Admin web | Chỉ **Quản trị viên** |
| AI/RAG | **Người dùng** *(qua Node)* + tùy chọn **Gemini** |

---

## Phụ lục — Kiến trúc tham chiếu (từ code)

```
Người dùng ──► Android (com.unutrip) ──HTTP──► Node /api/* ──► MySQL
                              │                    │
                              │                    └──proxy──► FastAPI RAG ──► Gemini API
                              ├──HTTP──► Open-Meteo
                              ├──HTTP──► OSM tiles
                              ├──Intent► Google Maps
                              └──GPS───► Fused Location (Play Services)

Quản trị viên ──Browser──► Node /admin/* ──proxy──► FastAPI /admin/*
```

| Thành phần | Port / URL mặc định | Nguồn |
|------------|---------------------|--------|
| Android API | `http://10.0.2.2:3000/api/` (emulator) | `RetrofitClient.kt`, `build.gradle` |
| Backend | `:3000` | `backend/nodejs/src/index.js` |
| RAG | `:8001` | `docker-compose.yml`, `RAG_BASE_URL` |
| Admin | `http://host:3000/admin/` | `dashboard.admin.routes.js` |
| DB | `unudata` | `.env.example`, migrations |

---

*Tài liệu sinh từ phân tích codebase UNUtrip_v2. Cập nhật khi thêm route/UI mới.*
