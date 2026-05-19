# Naming conventions (UNUtrip v2 monorepo)

Một bảng tra cứu để tránh lẫn tên giữa product, package và database.

| Tên | Ý nghĩa | Ví dụ |
|-----|---------|--------|
| **UNUtrip** | Tên sản phẩm / repo | `UNUtrip_v2`, Docker image `unutrip-rag` |
| **com.unutrip** | Android `applicationId` & package Kotlin | `app/src/main/java/com/unutrip/` |
| **unutrip-rag** | Python package (`pyproject.toml`) | `pip install -e backend/rag` |
| **unutrip-backend** | npm package Node | `backend/nodejs/package.json` |
| **unudata** | Database mặc định (Compose + `.env.example`) | `DB_NAME=unudata` |
| **unudata_v2_test** | DB test / dump local (không commit) | Đặt file trong `database/dumps/` |

## Quy tắc

- Tài liệu và UI: dùng **UNUtrip** (không dùng SmartTravel).
- Biến môi trường: `DB_NAME` là nguồn sự thật; không hardcode tên DB trong code Node/RAG.
- SQL dump lớn: **không** để ở root repo — dùng `database/dumps/` (gitignored).
- RAG manifest: commit chỉ khi `corpus_sha256` / `bm25_sha256` / `document_count` thay đổi có chủ đích (xem `backend/rag/docs/ARTIFACT_POLICY.md`).
- Session Android: prefs mới `UNUtripSession_secure`; vẫn migrate từ `SmartTravelSession*` nếu có.

## API paths

- Android → Node: `/api/*` (Retrofit `BASE_URL`)
- Node → RAG: `/v1/rag/chat/simple` (khuyến nghị; mirror không prefix vẫn tồn tại để tương thích)
