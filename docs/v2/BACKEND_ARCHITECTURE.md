# Backend Architecture (Node.js — V2)

## Purpose

Mô tả kiến trúc **Node Express backend** thực tế và hướng mục tiêu, trong khi giữ **contract Android** ổn định (`/api/destinations/*`, `/api/itineraries/*`, …).

## Trạng thái hiện tại (đối chiếu code)

### Đã migration sang v2

| Concern | Bảng runtime | Repository / module |
|---------|--------------|---------------------|
| Danh sách / chi tiết / nearby địa điểm | `app_places` | `repositories/destinations.repository.js` |
| Ảnh địa điểm | `place_images` | `repositories/destinationImages.repository.js` |
| Favorites existence check | `app_places` | `repositories/favorites.repository.js` |
| Reviews + aggregate rating | `app_places` | `repositories/reviews.repository.js` |
| Resolve RAG → app id | `place_id_map` (+ optional legacy) | `repositories/placeIdMap.repository.js` |
| Admin stats | `app_places` | `admin/dashboard.admin.routes.js` |

### Legacy còn lại (có chủ đích)

| Path | Ghi chú |
|------|---------|
| `placeIdMap.repository.js` | Fallback `destinations` khi `PLACE_ID_LEGACY_FALLBACK=true` |
| `seed.js` | Dev seed vẫn tham chiếu `destinations` — chỉ dùng bootstrap cũ |
| `backend/nodejs/database.sql` | Bootstrap Docker DB trống; không phải schema runtime v2 |

### API surface (giữ tên cũ cho Android)

- Route path: `/api/destinations/*` (không đổi).
- DTO: `shared/dto/destinationDto.js` — field names Android (`reviewCount`, `openTime`, …).
- Nguồn dữ liệu: **app-domain** (`app_places` + `place_images`), **không** đọc `rag_knowledge_base` cho API app.

## Kiến trúc layered (target — phần lớn đã áp dụng)

```
HTTP Request
    ↓
modules/*/*.routes.js + *.controller.js   ← parse, auth, status code
    ↓
services/*.service.js                     ← business logic, orchestration
    ↓
repositories/*.repository.js              ← SQL only
    ↓
shared/dto/*.js                           ← Android contract mapping
```

**Quy tắc:**

- Routes/controllers: không SQL inline (trừ admin HTML helpers nhỏ).
- Services: không format HTTP response trực tiếp nếu có thể tách.
- Repositories: không biết JWT / Android DTO.

## Module ownership

| Module | Trách nhiệm |
|--------|-------------|
| `modules/auth`, `modules/users` | JWT, profile, avatar, preferences |
| `modules/destinations` | CRUD/list/featured/nearby (app_places) |
| `modules/favorites` | Yêu thích user |
| `modules/reviews` | Review + cập nhật rating aggregate |
| `modules/itineraries` | Lịch trình transactional |
| `modules/ai` | Proxy RAG; resolve `rawPlaceId` trước persist |
| `modules/health` | Liveness / readiness (optional RAG probe) |
| `admin/*` | Admin web HTML — tách file theo section (Phase 4 admin shell) |

Registry API: `src/api/router.js` (không còn monolith `routes.js` shim lớn).

## AI / itinerary flow

1. Android → `POST /api/ai/*` hoặc `/api/itineraries/create-from-*`
2. Controller validate + auth
3. `services/ai.service.js` → HTTP tới RAG (`lib/ragUpstream.js`)
4. RAG trả `rawPlaceId` / metadata
5. `services/placeIdMap.service.js` → `app_places.id`
6. `services/itineraries.service.js` persist (transaction)

Chi tiết boundary: [`BACKEND_RAG_BOUNDARY.md`](BACKEND_RAG_BOUNDARY.md).  
Chi tiết flags v2: [`PHASE7_NODE_ANDROID_PARITY.md`](PHASE7_NODE_ANDROID_PARITY.md).

## Feature flags (place resolution)

| Env | Local default | Docker Compose |
|-----|---------------|----------------|
| `USE_V2_PLACE_TABLES` | `false` | `true` |
| `PLACE_ID_LEGACY_FALLBACK` | `true` (nếu v2 flag false) | `false` |

Khi `USE_V2_PLACE_TABLES=true`: legacy `destinations` fallback bị tắt trong place-id resolution.

## Hướng cải tiến còn lại

- Gom naming module `destinations` → logical `places` (chỉ rename nội bộ, giữ route path).
- `AuthService` / tách fat `ai.controller` nếu phình thêm.
- Production guard: bắt buộc `ADMIN_BASIC_*`, harden upload static.
- Xóa `console.log` debug (ví dụ `[NEARBY]` trong `destinations.service.js`).
- Vitest: mở rộng integration destinations + upload security.

## Target folder pattern (tham khảo — chưa rename hết)

```text
backend/nodejs/src/
  api/router.js
  modules/
    destinations/    # logical "places" — giữ tên file hiện tại
    favorites/
    reviews/
    itineraries/
    ai/
    auth/
    users/
    health/
  admin/             # đã modular (dashboard, users, ragAi, …)
  services/
  repositories/
  shared/dto/
  lib/ragUpstream.js
  config/env.js
```

Không bắt buộc rename ngay — ưu tiên contract Android và test parity.
