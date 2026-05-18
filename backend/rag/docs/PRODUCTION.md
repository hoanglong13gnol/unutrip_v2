# Production hardening (Phase 6)

## Environment

Set on **both** Node and FastAPI RAG:

| Variable | Production |
|----------|------------|
| `NODE_ENV` / `RAG_ENV` | `production` |
| `JWT_SECRET` | >= 32 chars, not dev default |
| `RAG_INTERNAL_API_KEY` | >= 16 chars, shared Node ↔ RAG app routes |
| `RAG_ADMIN_API_KEY` | >= 16 chars, **different** from internal; admin routes |
| `RAG_DEBUG` | `false` |
| `RAG_LOG_JSON` | `true` (recommended) |
| `RAG_READY_REQUIRES_INDEX` | `true` (default) |
| `RAG_ENABLE_METRICS` | `true` when scraping Prometheus |

## Readiness

- RAG `GET /health` — liveness (process up).
- RAG `GET /health/ready` — pipeline loaded + BM25 index on disk (when `RAG_READY_REQUIRES_INDEX=true`) + production config valid.
- Node `GET /api/health/ready` — MySQL `SELECT 1` + RAG `/health/ready` (unless `HEALTHCHECK_SKIP_RAG=true`).

## Gemini

- Blocking SDK calls use a **shared** `ThreadPoolExecutor` (`RAG_GEMINI_EXECUTOR_WORKERS`, default 4).
- Pool shuts down on app lifespan exit.

## Metrics

```bash
# Enable
RAG_ENABLE_METRICS=true
curl http://localhost:8001/metrics
```

Counters/histograms: `rag_http_requests_total`, `rag_http_request_duration_seconds`, `rag_gemini_requests_total`.

## Startup

RAG fails fast on invalid production config (`assert_production_config` in lifespan).

Node fails fast via `assertSafeProductionConfig()` in `src/index.js`.
