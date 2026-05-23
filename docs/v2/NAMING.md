# Naming conventions (UNUtrip v2 monorepo)

Tra cứu nhanh để tránh lẫn tên product, package và database.

| Tên | Ý nghĩa | Ví dụ |
|-----|---------|--------|
| **UNUtrip** | Tên sản phẩm / repo | `UNUtrip_v2`, Docker image `unutrip-rag` |
| **com.unutrip** | Android `applicationId` & package Kotlin | `app/src/main/java/com/unutrip/` |
| **unutrip-rag** | Python package (`pyproject.toml`) | `pip install -e backend/rag` |
| **unutrip-backend** | npm package Node | `backend/nodejs/package.json` |
| **unudata** | Database mặc định (Compose + `.env.example`) | `DB_NAME=unudata` |
| **unudata_v2_test** | DB test / dump local (không commit) | File trong `database/dumps/` |

## Quy tắc

- Tài liệu và UI: dùng **UNUtrip** (không dùng SmartTravel).
- Biến môi trường: `DB_NAME` là nguồn sự thật; không hardcode tên DB trong code Node/RAG.
- SQL dump lớn: **không** để ở root repo — dùng `database/dumps/` (gitignored).
- RAG manifest: commit chỉ khi `corpus_sha256` / `bm25_sha256` / `document_count` thay đổi có chủ đích — xem `backend/rag/docs/ARTIFACT_POLICY.md`.
- Session Android: prefs `UNUtripSession_secure`; vẫn migrate từ `SmartTravelSession*` nếu có.
- Tài liệu luận văn / use case: `backup_suport_file/` — không phải spec runtime.

## API paths

| Hop | Path | Ghi chú |
|-----|------|---------|
| Android → Node | `/api/*` | Retrofit `BASE_URL` (phải kết thúc `/`) |
| Node → RAG | `/v1/rag/chat/simple` | Khuyến nghị; mirror không prefix vẫn tồn tại |
| Node → RAG admin | `/admin/*` on RAG base URL | Header `X-RAG-Internal-Key` |
| Admin web | `/admin/*` on Node | Basic auth |

## Tên API vs bảng DB

| API (Android-facing) | Bảng runtime v2 |
|----------------------|-----------------|
| `/api/destinations/*` | `app_places` + `place_images` |
| `destinationId` trong JSON | `app_places.id` |
| RAG `rawPlaceId` | Resolve qua `place_id_map` |

Giữ tên API `destinations` vì contract Android — không đổi path khi đã migrate bảng.

## Thư mục tài liệu

| Path | Nội dung |
|------|----------|
| `docs/v2/` | Tài liệu kỹ thuật vận hành (index: `docs/v2/README.md`) |
| `backend/rag/docs/` | RAG artifact, deploy, retrieval |
| `backup_suport_file/` | Luận văn, use case, BPMN, lịch sử phase archive |
