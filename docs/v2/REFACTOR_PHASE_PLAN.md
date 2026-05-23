# V2 Refactor Phase Plan

## Strategy

Strangler pattern: giữ endpoint + contract Android; thay internals từng lớp; parity test sau mỗi phase.

**Lưu ý đặt tên:** *Phase 7* trong tài liệu parity ([`PHASE7_NODE_ANDROID_PARITY.md`](PHASE7_NODE_ANDROID_PARITY.md)) = place tables + contract E2E.  
*Phase 7* bên dưới (admin shell) = refactor admin — **hai mục khác nhau**.

---

## Trạng thái tổng quan

| Phase | Mô tả | Trạng thái |
|-------|--------|------------|
| 1 | Repository/service extraction | ✅ Done |
| 2 | Read paths → `app_places` / `place_images` | ✅ Done |
| 3 | `place_id_map` resolution | ✅ Done |
| 4 | Review aggregates → `app_places` | ✅ Done |
| 5 | RAG export/index từ `rag_knowledge_base` | ✅ Done (artifact pipeline + jobs) |
| 6 | Node↔RAG contract + itinerary parity tests | ✅ Mostly (Zod/Pydantic fixtures; E2E smoke manual) |
| 7 | Admin modular shell | ✅ Done (`admin/*.admin.routes.js`) |
| 8 | Android polish (DI, test, tách fragment) | ✅ Done (Phase C roadmap) |

---

## Phase 1 — Backend repository/service extraction

**Mục tiêu:** SQL ra khỏi routes; services orchestrate.

**Exit criteria:** ✅ API contract unchanged; Vitest smoke green (trừ known failures cần fix).

**Hiện trạng:** `modules/*`, `services/*`, `repositories/*`, `shared/dto/*` đã có.

---

## Phase 2 — Place/image read paths → v2 tables

**Mục tiêu:**

- `destinations` → `app_places`
- `destination_images` → `place_images`

**Exit criteria:** ✅ `/destinations`, featured, nearby, detail dùng `app_places`; DTO không đổi.

---

## Phase 3 — rawPlaceId → `place_id_map`

**Mục tiêu:** Thay mapping `rag_places` runtime bằng `place_id_map` + flags.

**Exit criteria:** ✅ `placeIdMap.repository.js`, `USE_V2_PLACE_TABLES`, tests `placeIdMap.service.test.js`.

---

## Phase 4 — Review aggregates → `app_places`

**Mục tiêu:** `UPDATE app_places SET rating, review_count`.

**Exit criteria:** ✅ `reviews.repository.js` join/update `app_places`.

---

## Phase 5 — RAG corpus từ `rag_knowledge_base`

**Mục tiêu:** Export JSONL → build BM25 (+ optional embeddings); runtime từ artifacts.

**Exit criteria:** ✅ `jobs/build_rag_artifacts.py`, manifest, verify script, CI fixture build.

---

## Phase 6 — AI chat + itinerary parity

**Mục tiêu:** Contract Node↔RAG; save flow resolve id an toàn.

**Exit criteria:**

- ✅ `docs/v2/fixtures/rag_chat_simple_sample.json`
- ✅ `ragContractParity.test.js`, `tests/contracts/`
- ⏳ Full staging E2E automated trong CI (`stack-smoke` workflow — chưa có)

---

## Phase 7 — Admin cleanup (Node admin shell)

**Mục tiêu:** Tách monolith `admin.js` (~2000 dòng) thành module routes.

**Exit criteria:** ✅ `admin/index.js` + per-section routes; behavior giữ nguyên.

**Parity Phase 7 (place tables):** xem [`PHASE7_NODE_ANDROID_PARITY.md`](PHASE7_NODE_ANDROID_PARITY.md).

---

## Phase 8 — Android polish (sau API ổn định)

**Mục tiêu:**

- Hilt/Koin DI; OkHttp Bearer interceptor + 401 handler
- Test ViewModel/Repository (MockWebServer)
- Tách god fragments (`ItineraryDetailFragment` chứa `AISuggestFragment`)
- Xóa `GEMINI_API_KEY` khỏi `build.gradle` (AI chỉ qua Node)
- Wire hoặc gỡ legacy `AISuggestFragment` (nav dead)

**Exit criteria:** ⏳ `testDevDebugUnitTest` + ≥1 instrumented smoke; không fragment >400 dòng.

---

## Open questions (cập nhật 2026-05)

| Câu hỏi | Trạng thái |
|---------|------------|
| Node gọi `AI_MODEL_URL` hay chỉ RAG? | RAG là gateway chính; `AI_MODEL_URL` optional fallback `/ai/chat` |
| `USE_V2_PLACE_TABLES` rollout? | ✅ Compose `true`; local XAMPP legacy vẫn `false` |
| Admin migration data source? | Admin CRUD dùng `app_places`; legacy bootstrap SQL vẫn tồn tại |
| RAG artifact vs DB online retrieval? | Artifact-first; DB online retrieval deferred |

---

## Cross-phase safeguards (luôn áp dụng)

- Không rewrite một lần toàn bộ module.
- Contract test sau thay đổi API shape.
- Feature flag cho cutover DB khi cần.
- Cập nhật [`AGENT_GUIDE.md`](AGENT_GUIDE.md) khi đóng phase.
