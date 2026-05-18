# RAG deploy checklist (Phase D + E)

## Pre-deploy (artifact)

1. On a machine with MySQL + v2 schema populated:
   ```bash
   cd backend/rag
   pip install -e .
   python jobs/build_rag_artifacts.py --from-db --export-places
   python scripts/verify_rag_artifacts.py --strict
   ```
2. Package release:
   ```bash
   cd backend/rag
   python jobs/package_rag_artifacts.py -o dist/unutrip-rag-artifacts-prod.zip
   # emits .zip.sha256 and .zip.RELEASE.json (checksums for deploy audit)
   ```
   Or one-shot from repo root (build + package + local stage):
   ```powershell
   .\scripts\publish_rag_bundle.ps1
   # staged dir → RAG_ARTIFACT_SOURCE_DIR=deploy/staging-rag-data
   ```
3. Upload `unutrip-rag-artifacts-prod.zip` to S3 or GitHub Release.

   **GitHub (local, PAT):**
   ```powershell
   $env:GITHUB_TOKEN = "ghp_..."   # repo: Contents read/write
   python scripts/upload_rag_bundle_github.py
   # prints browser_download_url -> RAG_ARTIFACT_BUNDLE_URL
   ```

   **GitHub (CLI):**
   ```powershell
   gh auth login
   gh release create rag-artifacts-2026-05-19 backend/rag/dist/unutrip-rag-artifacts-prod.zip --prerelease
   ```

   **GitHub Actions (team DB):** workflow `RAG artifact release (production DB)` — secrets `RAG_DB_HOST`, `RAG_DB_PORT`, `RAG_DB_USER`, `RAG_DB_PASSWORD`, `RAG_DB_NAME`.

   **S3:**
   ```powershell
   $env:RAG_ARTIFACT_S3_URI = "s3://YOUR-BUCKET/releases/unutrip-rag-artifacts-prod.zip"
   .\scripts\publish_rag_bundle.ps1 -SkipBuild
   ```

   Set `RAG_ARTIFACT_BUNDLE_URL` to the **HTTPS** URL (must end with `.zip`).
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

Example rules: `deploy/prometheus/unutrip-rag-alerts.yml` (see `deploy/prometheus/README.md`).

**CI bundle (fixture, no DB):** GitHub Actions → workflow `RAG artifact package (manual)` → download artifact → set `RAG_ARTIFACT_BUNDLE_URL` or mount volume.

## Staging E2E (Node ↔ RAG)

1. `docker compose up -d --build` with artifacts mounted or fetched.
2. `curl -s http://localhost:8001/health/ready | jq`
3. `curl -s http://localhost:3000/api/health/ready | jq`
4. Smoke: `POST /v1/rag/chat/simple` via Node proxy with `X-RAG-Internal-Key`.

Automated (from repo root, stack running):

```bash
export RAG_INTERNAL_API_KEY=your-key
bash scripts/smoke_staging_e2e.sh
```

Windows (local MySQL, no Docker): set `DB_NAME` in `.env` (e.g. `unudata_v2_test` after import), then:

```powershell
.\scripts\staging_local.ps1
# two terminals: uvicorn (8001) + npm start (3000)
$env:RAG_INTERNAL_API_KEY = "your-key"
.\scripts\smoke_staging_e2e.ps1
```

Discover DB name: `python scripts/probe_mysql_rag.py` (lists DBs with `rag_knowledge_base`).

## CI gate (repo)

- Workflow: `.github/workflows/rag-ci.yml` (fixture build, 70% coverage, eval golden).
- Require status check on `main` before merge (branch protection on GitHub).
