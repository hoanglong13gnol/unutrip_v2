# Deploy — UNUTrip v2 stack

Hướng dẫn ngắn gọn triển khai stack đầy đủ. Chi tiết RAG: [`backend/rag/docs/DEPLOY_CHECKLIST.md`](../backend/rag/docs/DEPLOY_CHECKLIST.md).

## Thành phần & port

| Service | Port mặc định | Health |
|---------|---------------|--------|
| Node backend | 3000 | `GET /api/health` |
| RAG FastAPI | 8001 | `GET /health/ready` |
| MySQL | 3306 | `db-migrate` exit 0 |
| Redis | 6379 (internal) | optional rate limit / cache |

## Thứ tự khởi động (Docker Compose)

```text
mysql (healthy)
  → db-migrate (completed)
  → redis (healthy)
  → rag (started — index cần artifact)
  → backend (depends db + mysql + rag)
```

**Lưu ý:** Backend hiện `depends_on rag: service_started` — RAG có thể chưa ready index; first requests có thể 502 cho đến khi `/health/ready` 200.

## Chuẩn bị env

```bash
cp .env.example .env
```

Tối thiểu:

```env
GEMINI_API_KEY=...
JWT_SECRET=<strong-32+>
MYSQL_ROOT_PASSWORD=...
MYSQL_PASSWORD=...
```

Production thêm: `RAG_INTERNAL_API_KEY`, `RAG_ADMIN_API_KEY`, `ADMIN_BASIC_USER/PASS`, `NODE_ENV=production`.

## RAG artifacts

Runtime cần BM25 index. Một trong:

1. **Build local** rồi mount volume (uncomment trong `docker-compose.yml`)
2. **`RAG_ARTIFACT_BUNDLE_URL`** — zip release; entrypoint fetch
3. **CI fixture** — chỉ dev (`build_rag_artifacts.py --from-fixture`)

Verify:

```bash
curl http://localhost:8001/health/ready
```

## Smoke test

```bash
# Linux / Git Bash
bash scripts/smoke_staging_e2e.sh

# Windows
.\scripts\smoke_staging_e2e.ps1
```

## Redis riêng (optional)

```bash
docker compose -f deploy/redis-compose.yml up -d
# .env: REDIS_URL=redis://127.0.0.1:6379/0
```

## Monitoring

- Prometheus rules: [`prometheus/unutrip-rag-alerts.yml`](prometheus/unutrip-rag-alerts.yml)
- Hướng dẫn: [`prometheus/README.md`](prometheus/README.md)
- Bật metrics RAG: `RAG_ENABLE_METRICS=true`

## Reverse proxy (gợi ý)

| Path public | Upstream |
|-------------|----------|
| `/api/*` | Node :3000 |
| `/admin/*` | Node :3000 |
| `/v1/*` hoặc internal | RAG :8001 (không expose public nếu có thể) |

Android chỉ cần reach Node `/api/*`.

## Rollback RAG

1. Đổi `RAG_ARTIFACT_BUNDLE_URL` sang release trước
2. `docker compose restart rag`
3. Verify `/health/ready` + smoke chat

## Liên kết

- [`../README.md`](../README.md)
- [`../docs/v2/AGENT_GUIDE.md`](../docs/v2/AGENT_GUIDE.md)
- [`../database/README.md`](../database/README.md)
