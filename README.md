# UNUtrip v2 (core tree)

Bản thư mục này chỉ giữ **mã nguồn và cấu hình vận hành** được tách từ demo v1: Android (`app/`), API Node (`backend/nodejs/`), dịch vụ RAG (`backend/rag/`), migration MySQL (`database/migrations/`), Docker Compose ở root.

**Agent / dev mới:** đọc [`docs/v2/AGENT_GUIDE.md`](docs/v2/AGENT_GUIDE.md) (đã làm / cần làm / lệnh / pitfalls).  
**Khắc phục điểm yếu / roadmap đầy đủ:** [`docs/v2/README_TOTAL_GUIDE.md`](docs/v2/README_TOTAL_GUIDE.md).  
**Đặt tên / DB dump:** [`docs/v2/NAMING.md`](docs/v2/NAMING.md) · SQL lớn → `database/dumps/` (gitignored).

## Đã cố ý loại bỏ

- Báo cáo / luận văn (`docx_doan/`, `CHUONG_*.md`, `*_REPORT_INPUT.md`, …)
- Nhật ký refactor rải rác (`README_FIX_ALL*.md`, …)
- Ảnh – sơ đồ flow ở root / `docs/diagrams/`
- Hầu hết `backend/rag/scripts/` (pipeline một lần); giữ tối thiểu: export corpus, build BM25, verify manifest, eval CI
- File thử nghiệm Node (`server.py`, `test_ai.js`) và gói `backend/rag/tools/`
- `backend/rag/data/image_pipeline/`, cache Gemini, v.v.

## Database (v2)

- **Canonical:** `database/migrations/` — chạy bằng `database/scripts/run_migrations.sh` hoặc `docker compose` (service `db-migrate`).
- **Deprecated:** `backend/nodejs/database.sql` (chỉ bootstrap Docker khi DB trống).
- Chi tiết: `database/README.md`.

## Dữ liệu RAG

- `backend/rag/data/indexes/rag_artifacts_manifest.json` — tracked trong git (checksum corpus + index).
- `backend/rag/data/indexes/bm25_index.pkl` và `data/processed/places_rag_documents.jsonl` — **không commit** (`.gitignore`); tạo local bằng `python backend/rag/jobs/build_rag_artifacts.py --from-db` hoặc export + `scripts/06_build_bm25_index.py`.
- `backend/rag/data/raw/dataset_vip_fixed.xlsx` — nguồn rebuild pipeline khi cần (có thể giữ local).
- Kiểm tra: `python backend/rag/scripts/verify_rag_artifacts.py` (trong thư mục `backend/rag`).

## Chạy nhanh

Giống monorepo gốc: copy `.env.example` → `.env`, `npm ci` trong `backend/nodejs`, venv + `pip install -e ".[dev]"` trong `backend/rag` (xem `backend/rag/README.md`), Gradle/Android như cũ.

Demo gốc (`e:\UNUtrip`) **không bị sửa**; mọi thay đổi v2 làm trên thư mục này.
