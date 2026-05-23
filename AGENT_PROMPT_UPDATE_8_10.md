# Prompt cho Agent mới — nâng UNUTrip v2 lên 8/10

Copy toàn bộ khối **PROMPT** bên dưới vào chat agent mới.

---

## PROMPT (copy từ đây)

```
Bạn là agent kỹ thuật làm việc trên repo UNUTrip v2 (monorepo du lịch Việt Nam).

## Mục tiêu duy nhất
Nâng chất lượng project từ ~6.2/10 lên **≥8.0/10** theo roadmap trong file:
  README_UPDATE_FINAL.md (ở root repo — ĐỌC FILE NÀY TRƯỚC, đây là source of truth cho task list)

KHÔNG dựa vào các file .md trong backup_suport_file/ hay luận văn — chúng có thể sai/lỗi thời.
KHÔNG dựa vào mô tả cũ kiểu "backend vẫn đọc bảng destinations" — runtime Node đã đọc app_places.

## Kiến trúc bắt buộc hiểu (đừng phá)

Luồng:
  Android (app/) → Node REST :3000/api/* → RAG FastAPI :8001/v1/*
  Node → MySQL (users, app_places, itineraries, place_id_map, …)
  RAG → BM25 index trên disk + Gemini (KHÔNG ghi DB app)

Quy tắc cứng:
- Android CHỈ gọi Node, KHÔNG gọi RAG trực tiếp
- Node persist itinerary/reviews/favorites; RAG chỉ gợi ý + chat
- API path giữ /api/destinations/* (contract Android); DB runtime = app_places
- Không commit: .env, .pkl, JSONL lớn, manifest chỉ đổi timestamp
- Không git push / không tạo commit trừ khi user yêu cầu rõ

## Thứ tự làm việc (bắt buộc theo phase)

Làm tuần tự Phase A → B → C → D trong README_UPDATE_FINAL.md.
Mỗi phase xong phải chạy verify của phase đó trước khi sang phase tiếp.
Tick checklist §3 trong README_UPDATE_FINAL.md khi hoàn thành mục.

### Phase A (P0) — làm trước
- Fix 2 RAG test fail: backend/rag/tests/pipelines/test_rag_pipeline_unit.py
- Fix 4 Node test fail: adminAuth, env.v2PlaceFlags, ai-rag-chat (stale guest auth)
- Docker fresh install: database/scripts/run_migrations.sh + compose RAG artifact + health ready
- Xóa/gate debug log: destinations.service.js [NEARBY], ai.service.js, RetrofitClient release logging

Verify Phase A:
  cd backend/rag && python -m pytest tests/ -q   # 0 fail
  cd backend/nodejs && npm test                    # 0 fail
  docker compose down -v && docker compose up -d --build
  curl http://localhost:8001/health/ready
  curl http://localhost:3000/api/health/ready

### Phase B (P1)
- Admin XSS: backend/nodejs/src/admin/dashboard.admin.routes.js → escapeHtml
- Admin auth prod: adminAuth.middleware.js + env.js assert
- Upload MIME validation + tests
- Password min 8, CORS prod, rate limit guest /ai/*
- CI: .github/workflows/stack-smoke.yml
- Node tests mở rộng (itineraries, destinations, upload)

### Phase C (P2) — Android
- Xóa dead code: AISuggestFragment, ~650 dòng AI dialog trong ItineraryFragment.kt
- Gỡ Room, Compose (unused), GEMINI_API_KEY buildConfigField
- AuthInterceptor + ProfileViewModel + ChatRepository
- ≥15 unit tests + 1 instrumented smoke

### Phase D (P3)
- RAG corpus staging ≥500 docs, golden eval
- schema_migrations table
- Tách fat files Node (itineraries.service.js, ai.controller.js)

## Definition of Done — 8/10

Tất cả pass:
  docker compose up -d --build (fresh volume OK)
  cd backend/rag && make quality
  cd backend/nodejs && npm test && npm run lint
  ./gradlew :app:testDevDebugUnitTest :app:lintDevDebug :app:assembleDevDebug
  bash scripts/smoke_staging_e2e.sh

## Quy tắc code

- Minimal diff — chỉ sửa đúng scope task, không refactor lan man
- Match conventions hiện có (ESM Node, Kotlin ViewBinding, RAG layered packages)
- Đọc file xung quanh trước khi sửa
- Sau sửa: chạy test/lint liên quan
- Cập nhật tick README_UPDATE_FINAL.md §3 nếu user yêu cầu doc sync

## Việc KHÔNG làm (trừ khi user yêu cầu)

- Đổi API path /api/destinations → /places (breaking Android)
- Viết lại Android bằng Compose
- Implement LoRA/Validator RAG — xóa flag nếu không dùng
- Sửa demo gốc e:\UNUtrip
- Over-engineer Hilt full graph — interceptor + factory đủ cho 8/10
- Tạo commit/push/PR tự ý

## File tham chiếu nhanh

| File | Mục đích |
|------|----------|
| README_UPDATE_FINAL.md | Task list chi tiết + checklist |
| backend/nodejs/src/api/router.js | API modules |
| backend/nodejs/src/repositories/destinations.repository.js | app_places reads |
| backend/rag/pipelines/rag_pipeline.py | RAG orchestration |
| app/src/main/java/com/unutrip/data/api/ApiService.kt | Android contract |
| docker-compose.yml | Stack local |
| .env.example | Env vars |

## Cách báo cáo cho user

Sau mỗi batch công việc, trả lời ngắn:
1. Phase / mục đã làm (vd: A1, A2.1)
2. File đã sửa
3. Kết quả verify (pass/fail + lệnh đã chạy)
4. Blocker nếu có
5. Mục tiếp theo đề xuất

Bắt đầu bằng: đọc README_UPDATE_FINAL.md, chạy test hiện trạng (RAG + Node), báo số fail, rồi implement Phase A từ mục A1.
```

---

## Biến thể prompt ngắn (1 phase)

```
Làm Phase A trong README_UPDATE_FINAL.md cho UNUtrip v2.
Đọc file đó + code thực tế (ignore backup_suport_file/*.md).
Fix all failing tests, Docker fresh bootstrap, RAG health ready, remove debug logs.
Verify: pytest 0 fail, npm test 0 fail, docker compose health ready 200.
Minimal diff, no commit unless asked. Báo cáo file đã sửa + lệnh verify.
```

## Biến thể prompt theo lớp

**Chỉ Android (Phase C):**
```
UNUtrip v2 — thực hiện Phase C trong README_UPDATE_FINAL.md.
Gỡ dead code ItineraryFragment/AISuggestFragment, unused deps, thêm AuthInterceptor + tests.
Không đổi API contract. Verify: ./gradlew :app:testDevDebugUnitTest :app:lintDevDebug
```

**Chỉ Node + CI (Phase A1 + B):**
```
UNUtrip v2 — Phase A1 + B trong README_UPDATE_FINAL.md.
Fix vitest, admin XSS, upload security, stack-smoke.yml.
Verify: npm test 0 fail, npm run lint pass.
```

**Chỉ RAG (Phase A1 RAG + D1):**
```
UNUtrip v2 — fix RAG tests + Phase D1 README_UPDATE_FINAL.md.
make quality 0 fail, document_count staging, golden eval pass.
```
