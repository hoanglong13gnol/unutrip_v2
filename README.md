# UNUtrip v2

Monorepo **mã nguồn vận hành** (tách từ demo v1 `e:\UNUtrip` — demo gốc không bị sửa):

| Thành phần | Path | Vai trò |
|------------|------|---------|
| Android | `app/` | App mobile — gọi Node API, không gọi RAG trực tiếp |
| Node API | `backend/nodejs/` | Express, JWT, MySQL, proxy RAG, admin web |
| RAG / AI | `backend/rag/` | FastAPI, BM25/hybrid retrieval, Gemini |
| Database | `database/migrations/` | Schema v2 canonical |
| Docker | `docker-compose.yml` | MySQL + Redis + RAG + Node + `db-migrate` |

## Tài liệu

| Đọc trước | Mục đích |
|-----------|----------|
| [`docs/v2/README.md`](docs/v2/README.md) | **Index** toàn bộ tài liệu kỹ thuật |
| [`docs/v2/AGENT_GUIDE.md`](docs/v2/AGENT_GUIDE.md) | Onboarding dev/agent: lệnh, CI, pitfalls |
| [`docs/v2/README_TOTAL_GUIDE.md`](docs/v2/README_TOTAL_GUIDE.md) | Backlog khắc phục điểm yếu (P0–P3) |
| [`docs/v2/NAMING.md`](docs/v2/NAMING.md) | Quy ước tên DB / package / API |

Tài liệu luận văn, use case, BPMN: [`backup_suport_file/`](backup_suport_file/) (không phản ánh code runtime).

## Kiến trúc runtime

```
Android  ──HTTP──►  Node :3000/api/*
                       │
                       ├──► MySQL (users, app_places, itineraries, …)
                       └──► RAG :8001/v1/*  ──► BM25 index + Gemini
```

- **Boundary:** RAG gợi ý + retrieval; Node persist + JWT + contract Android. Chi tiết: [`docs/v2/BACKEND_RAG_BOUNDARY.md`](docs/v2/BACKEND_RAG_BOUNDARY.md).
- **DB v2:** API `/destinations/*` đọc bảng `app_places` (không còn `destinations` ở runtime read path).

## Chạy nhanh

```bash
# 1. Env
cp .env.example .env
# Chỉnh tối thiểu: GEMINI_API_KEY, JWT_SECRET

# 2. Stack Docker (khuyến nghị)
docker compose up -d --build
# Node:  http://localhost:3000/api/health
# RAG:   http://localhost:8001/docs

# 3. Hoặc chạy rời
cd backend/nodejs && npm ci && npm run dev
cd backend/rag && pip install -e ".[dev]" && uvicorn app.main:app --reload --port 8001

# 4. Android — local.properties (gitignored)
# API_BASE_URL=http://10.0.2.2:3000/api/
```

Chi tiết DB: [`database/README.md`](database/README.md). Chi tiết RAG artifacts: [`backend/rag/README.md`](backend/rag/README.md).

## Database (v2)

- **Canonical:** `database/migrations/` — `database/scripts/run_migrations.sh` hoặc service `db-migrate` trong Compose.
- **Deprecated:** `backend/nodejs/database.sql` — bootstrap Docker khi DB trống (`DATABASE_BOOTSTRAP_LEGACY=true`).
- Dump lớn: `database/dumps/` (gitignored).

## Dữ liệu RAG

- **Tracked:** `backend/rag/data/indexes/rag_artifacts_manifest.json`
- **Không commit:** `bm25_index.pkl`, `places_rag_documents.jsonl` — build local:
  ```bash
  cd backend/rag
  python jobs/build_rag_artifacts.py --from-db   # cần MySQL có rag_knowledge_base
  # hoặc CI/local không DB:
  python jobs/build_rag_artifacts.py --from-fixture
  python scripts/verify_rag_artifacts.py
  ```

## CI

| Workflow | Trigger |
|----------|---------|
| `rag-ci.yml` | `backend/rag/**` |
| `backend-ci.yml` | `backend/nodejs/**`, `database/**` |
| `android-ci.yml` | `app/**` |

## Đã cố ý loại bỏ khỏi tree chính

- Báo cáo / luận văn → `backup_suport_file/`
- Pipeline RAG một lần (giữ tối thiểu trong `backend/rag/scripts/`, `jobs/`)
- Dead code v1 (`server.py`, `test_ai.js`, …)
