# Phase 7 — Node / Android parity (place tables)

> **Không nhầm với** Phase 7 admin shell trong [`REFACTOR_PHASE_PLAN.md`](REFACTOR_PHASE_PLAN.md).

## Scope

- **Node** đọc/ghi địa điểm qua `app_places`, `place_images`, `place_id_map`.
- **RAG** trả recommendation metadata; Node resolve `rawPlaceId` → `app_places.id` trước persist.
- **Android** giữ JSON shape ổn định (`toDestinationDto`, itinerary DTOs).

## Runtime data sources (Node)

| API | SQL source |
|-----|------------|
| `GET /api/destinations*` | `app_places` + `place_images` |
| Favorites / reviews check | `app_places.id` |
| Review aggregates | `UPDATE app_places` |
| Itinerary items FK | `app_places.id` (migration 011) |
| AI save itinerary | `place_id_map` → `app_places.id` |

Legacy `destinations` chỉ còn trong:

- `placeIdMap.repository.js` khi `PLACE_ID_LEGACY_FALLBACK=true`
- `seed.js` / `database.sql` bootstrap

## Feature flags

| Env | Default local | Docker Compose | Effect |
|-----|---------------|----------------|--------|
| `USE_V2_PLACE_TABLES` | `false` | `true` | Khi `true`, tắt legacy fallback trong place-id resolution |
| `PLACE_ID_LEGACY_FALLBACK` | `true`* | `false` | Lookup `destinations` khi map miss (*ignored if v2 flag true) |

Định nghĩa: `backend/nodejs/src/config/env.js`.

**Khuyến nghị:**

- Docker / staging / prod: `USE_V2_PLACE_TABLES=true`, `PLACE_ID_LEGACY_FALLBACK=false`
- XAMPP chỉ có legacy dump: `USE_V2_PLACE_TABLES=false`, `PLACE_ID_LEGACY_FALLBACK=true` + chạy migrations

## Resolution order (`placeIdMap.repository`)

1. `place_id_map` (rag_place_id / place_key / `RAG_ALIAS_`)
2. Numeric id → `app_places.id`
3. `MANUAL_{n}` → `app_places.id`
4. `app_places.place_key`
5. `rag_knowledge_base.app_place_id`
6. Legacy `destinations` (chỉ khi legacy fallback enabled)

Batch API: `services/placeIdMap.service.js` → `resolveRawPlaceIdsFromItems`.

## Contract E2E (RAG chat)

Shared fixture: [`fixtures/rag_chat_simple_sample.json`](fixtures/rag_chat_simple_sample.json)

| Side | Test |
|------|------|
| Node | `tests/ragContractParity.test.js` (Zod) |
| RAG | `tests/contracts/test_rag_node_fixture.py` (Pydantic) |

## Android API (unchanged paths & fields)

`GET /api/destinations/*` vẫn trả:

`id`, `name`, `description`, `address`, `city`, `province`, `latitude`, `longitude`, `category`, `images`, `rating`, `reviewCount`, `openTime`, `closeTime`, `entryFee`, `tags`, `isFavorite`, (`distanceKm` cho nearby)

Category codes: `beach`, `mountain`, `city`, `heritage`, `nature`, `checkin`, `food`, `culture`, `religious` (+ `other` trong DB enum).

## Verification

```bash
cd backend/nodejs && npm test
cd backend/rag && python -m pytest tests/contracts/ -q
```

Sau migrate full legacy → v2:

```bash
mysql ... unudata < database/migrations/010_v2_validation_queries.sql
```

## Known gaps

- Android vẫn có `GEMINI_API_KEY` trong `buildConfigField` — không dùng cho chat runtime (AI qua Node); nên xóa ở Phase 8.
- `AISuggestFragment` trong nav graph — legacy UI, không có `navigate()` từ app; flow AI mới: `AIItineraryRequest` → `Options` → `Editor`.
