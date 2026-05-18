# RAG deploy checklist (Phase D + E)

## Pre-deploy (artifact)

1. On a machine with MySQL + v2 schema populated:
   ```bash
   cd backend/rag
   pip install -e .
   python jobs/build_rag_artifacts.py --from-db --export-places
   python scripts/verify_rag_artifacts.py --strict
   ```
2. Package release (example):
   ```bash
   cd data
   zip -r ../unutrip-rag-artifacts.zip processed/places_rag_documents.jsonl processed/places_app.json indexes/
   ```
3. Upload `unutrip-rag-artifacts.zip` to object storage or GitHub Release asset.
4. Commit **only** `indexes/rag_artifacts_manifest.json` when checksums change (optional, for audit).

## Runtime (container / VM)

| Variable | Purpose |
|----------|---------|
| `RAG_ENV=production` | Fail-fast on weak secrets |
| `RAG_INTERNAL_API_KEY` | Node ↔ RAG app routes (≥16 chars) |
| `RAG_ADMIN_API_KEY` | Admin routes (different from internal) |
| `RAG_DEBUG=false` | Hide stack traces |
| `RAG_LOG_JSON=true` | Structured logs |
| `RAG_READY_REQUIRES_INDEX=true` | `/health/ready` needs BM25 |
| `RAG_ENABLE_METRICS=true` | Prometheus `/metrics` |
| `RAG_ARTIFACT_BUNDLE_URL` | HTTPS `.zip` fetched in Docker entrypoint |
| `RAG_ARTIFACT_SOURCE_DIR` | Host/volume path with `processed/` + `indexes/` |
| `GEMINI_API_KEY` | When `ENABLE_GEMINI=true` |

**Option A — volume mount (recommended staging):**

```yaml
# docker-compose override
services:
  rag:
    volumes:
      - /opt/unutrip/rag-data:/svc/data
```

**Option B — bundle URL (recommended prod replicas):**

```env
RAG_ARTIFACT_BUNDLE_URL=https://releases.example/unutrip-rag-artifacts.zip
```

Entrypoint runs `scripts/fetch_rag_artifacts.py` when URL or source dir is set.

## Health & alerting

| Check | Expected |
|-------|----------|
| `GET /health` | 200 always when process up |
| `GET /health/ready` | 200 when index + prod config OK; **503** otherwise |
| `GET /metrics` | 200 when `RAG_ENABLE_METRICS=true` |
| Node `GET /api/health/ready` | 200 when MySQL + RAG ready |

Alert on: ready probe failures > 2 min, `rag_gemini_requests_total{outcome="error"}` spike, p95 `rag_http_request_duration_seconds` > SLA.

## Staging E2E (Node ↔ RAG)

1. `docker compose up -d --build` with artifacts mounted or fetched.
2. `curl -s http://localhost:8001/health/ready | jq`
3. `curl -s http://localhost:3000/api/health/ready | jq`
4. Smoke: `POST /v1/rag/chat/simple` via Node proxy with `X-RAG-Internal-Key`.

## CI gate (repo)

- Workflow: `.github/workflows/rag-ci.yml` (fixture build, 70% coverage, eval golden).
- Require status check on `main` before merge (branch protection on GitHub).
