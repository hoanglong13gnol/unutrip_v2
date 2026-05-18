# Phase 7 — Node / Android parity

## Scope

- **Node** reads/writes `app_places`, `place_images`, `place_id_map` (v2 tables).
- **RAG** returns recommendations; Node resolves `rawPlaceId` → `app_places.id` before persistence.
- **Android** keeps stable JSON shapes (`toDestinationDto`, itinerary DTOs) — no breaking field renames.

## Feature flags

| Env | Default | Effect |
|-----|---------|--------|
| `USE_V2_PLACE_TABLES` | `false` (local); `true` in Docker Compose | When `true`, disables legacy `destinations` fallback in place-id resolution |
| `PLACE_ID_LEGACY_FALLBACK` | `true` (local); `false` in Docker Compose | Lookup `destinations` / `rag_place_id` when v2 map misses (ignored if `USE_V2_PLACE_TABLES=true`) |

## Contract E2E

Shared fixture: `docs/v2/fixtures/rag_chat_simple_sample.json`

- Node: `tests/ragContractParity.test.js` (Zod)
- RAG: `tests/contracts/test_rag_node_fixture.py` (Pydantic)

## Resolution order (`placeIdMap.repository`)

1. `place_id_map` (rag_place_id / place_key / RAG_ALIAS_)
2. Numeric id → `app_places.id`
3. `MANUAL_{n}` → `app_places.id`
4. `app_places.place_key`
5. `rag_knowledge_base.app_place_id`
6. Legacy `destinations` (only when legacy fallback enabled)

## Android API (unchanged)

`GET /api/destinations/*` still returns:

`id`, `name`, `description`, `address`, `city`, `province`, `latitude`, `longitude`, `category`, `images`, `rating`, `reviewCount`, `openTime`, `closeTime`, `entryFee`, `tags`, `isFavorite`

## Verification

```bash
cd backend/nodejs && npm test
cd backend/rag && python -m pytest tests/contracts/ -q
```
