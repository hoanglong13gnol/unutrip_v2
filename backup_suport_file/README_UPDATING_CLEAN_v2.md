# UNUtrip v2 — Làm sạch & nâng cấp RAG (v2 roadmap)

Tài liệu theo dõi refactor **Phase A–E** và **P0–P3b** trên monorepo v2.  
**Bàn giao agent:** [`docs/v2/AGENT_GUIDE.md`](docs/v2/AGENT_GUIDE.md) (tóm tắt + checklist PR).  
Bản trước: `README_UPDATING_CLEAN.md` (Phase 0–7). Demo gốc `e:\UNUtrip` **không** bị sửa.

---

## Tóm tắt nhanh

| Hạng mục | Trạng thái |
|----------|------------|
| Phase A — Hygiene & deps | ✅ Xong |
| Phase B — Tách pipeline / scoring / providers | ✅ Xong |
| Phase C — Mypy, coverage 70%, CI Docker | ✅ Xong |
| Phase D — Dữ liệu & artifact production | 🟡 Một phần (fetch/package/entrypoint) |
| Phase E — Deploy / observability | 🟡 Một phần (checklist + Prometheus rules mẫu) |
| Phase 8 — Android polish | ⏳ Chưa |

**Chất lượệ hiện tại:** 110 pytest pass · coverage **~79%** · ruff sạch · mypy (`core`, `domain`, `generation`, `providers`, `pipelines`, `repositories`, `retrieval.scoring`) · gate **≥70%**.

---

## Đã làm

### Phase A — Dọn nhanh (hygiene)

| Hạng mục | Chi tiết |
|----------|----------|
| Dead code | Xóa `retrieval/normalizer.py` (~381 dòng), `retrieval/rerank_stub.py` |
| Text normalization | `core/text_normalization.py` — nguồn chuẩn; `retrieval/text_utils.py` re-export; xóa `services/itinerary/text_utils.py` |
| `targetCity` | Filter thật trong pipeline (`LocationFilter` sau Phase B); test `test_pipeline_city_match.py` |
| Dependencies | Runtime trong `pyproject.toml`; `pip install -e ".[dev]"` |
| Dev hygiene | `scripts/clean_dev_artifacts.py`, `Makefile` (`clean`, `install-dev`, `lint`, `test`, `quality`) |

### Phase B — Refactor kiến trúc

| Hạng mục | Chi tiết |
|----------|----------|
| `pipelines/rag_pipeline.py` | ~615 → ~129 dòng — chỉ orchestration |
| `pipelines/policies/` | `location_filter.py`, `generation_router.py` |
| `pipelines/` | `response_builder.py`, `request_logger.py` |
| `providers/` | `protocol.py`, `gemini_provider.py`, `template_provider.py` (wrap `llm/`) |
| `retrieval/scoring/` | `travel_rules.py`, `dedup.py` — `hybrid_retriever.py` gọn (~140 dòng) |
| Docs | `backend/rag/README.md` — bảng package cập nhật |

### Phase C — Chất lượng & CI

| Hạng mục | Chi tiết |
|----------|----------|
| Mypy | `core`, `domain`, `generation`, `providers`, `pipelines` — CI + `make typecheck` |
| Pytest-cov | Gate **70%**; 26+ test mới (generation, router, providers, scoring, gemini unit) |
| Pre-commit | `backend/rag/.pre-commit-config.yaml` (ruff, mypy, pytest pre-push) |
| CI `rag-ci.yml` | Mypy, coverage, upload `.coverage`, `docker build` |
| Coverage omit | Admin/itinerary nặng, `rag_pipeline` integration, BM25/hybrid — xem `pyproject.toml` |

### P3b — Retrieval coverage (mới)

| Hạng mục | Chi tiết |
|----------|----------|
| Tests | `test_place_store`, `test_bm25_retriever`, `test_hybrid_retriever_edges`, `test_ai_request_logger`, `test_rerank_edges` |
| Coverage omit | Bỏ toàn bộ `retrieval/*` khỏi omit (trừ phần đã gộp vào scoring) |
| Tổng | 110 tests, ~79% cov |

### P3 — Coverage & mypy mở rộng (mới)

| Hạng mục | Chi tiết |
|----------|----------|
| Tests | `test_rag_pipeline_unit.py`, `test_request_logger.py` |
| Coverage omit | Bỏ `rag_pipeline`, `request_logger`, `intent_parser` khỏi omit |
| Mypy | Thêm `repositories`, `retrieval.scoring` |
| Staging smoke | `scripts/smoke_staging_e2e.sh` |

### P2 — CI & ops (mới)

| Hạng mục | Chi tiết |
|----------|----------|
| `backend-ci.yml` | Chỉ trigger `backend/nodejs` + `database/` (không trùng RAG) |
| Backend CI | `docker build` Node + `bash -n` migration script |
| `rag-artifact-release.yml` | Manual workflow: package fixture zip → Actions artifact |
| `deploy/prometheus/` | Example alert rules + blackbox ready probe doc |

### P1 — Schema v2 & Compose migrate (mới)

| Hạng mục | Chi tiết |
|----------|----------|
| `database/scripts/run_migrations.sh` | Apply migrations; optional legacy bootstrap |
| `docker-compose.yml` | Service `db-migrate`; backend `USE_V2_PLACE_TABLES=true` |
| `database/README.md` | Canonical DB path; deprecate `database.sql` |
| `backend/nodejs/DATABASE_LEGACY.md` | Hướng dẫn chuyển sang migrations |
| Tests | `backend/nodejs/tests/env.v2PlaceFlags.test.js` |

### P0 — Hygiene manifest & gitignore (mới)

| Hạng mục | Chi tiết |
|----------|----------|
| `.gitignore` | `data/raw/`, `backend/rag/dist/`, Node `uploads/`, `.vscode/`, `Thumbs.db` |
| `core/artifacts.py` | `artifact_path_for_manifest`, `resolve_artifact_path`, `manifest_path_issues` |
| CI verify | `--strict` từ chối path tuyệt đối trong manifest |
| Manifest tracked | Paths dạng `data/processed/...`, `data/indexes/...` |

### Phase D — Artifact production & deploy (mới)

| Hạng mục | Chi tiết |
|----------|----------|
| `repositories/artifact_store.py` | Copy từ volume dir hoặc giải nén bundle `.zip` |
| `scripts/fetch_rag_artifacts.py` | CLI + Docker entrypoint khi có `RAG_ARTIFACT_*` |
| `jobs/package_rag_artifacts.py` | Zip `data/` sau build DB để upload release |
| `scripts/docker_entrypoint.sh` | Fetch trước `uvicorn` trong image |
| Docs | `docs/DEPLOY_CHECKLIST.md`, cập nhật `ARTIFACT_POLICY.md` |
| Còn lại | Build full corpus `--from-db` + upload release (cần MySQL prod) |

### Test mới (Phase A–C)

```text
tests/generation/test_builders.py
tests/pipelines/test_generation_router.py
tests/pipelines/test_response_builder.py
tests/pipelines/test_location_filter_fallback.py
tests/providers/test_template_provider.py
tests/providers/test_gemini_provider.py
tests/llm/test_gemini_generator_unit.py
tests/retrieval/test_scoring.py
tests/test_pipeline_city_match.py
```

---

## Cần làm (ưu tiên)

### Dữ liệu & artifact (cao)

- [ ] Production corpus full: `build_rag_artifacts.py --from-db` → cập nhật manifest (local; không commit `.pkl` / JSONL lớn)
- [x] Chiến lược deploy artifact: zip URL + volume + `package_rag_artifacts.py` / `fetch_rag_artifacts.py`
- [ ] Upload bundle lên S3/GitHub Release và gắn `RAG_ARTIFACT_BUNDLE_URL` staging/prod
- [ ] `places_app_reviewed.json` (human review) — tùy chọn

### Production & vận hành (cao)

- [x] Deploy checklist: `backend/rag/docs/DEPLOY_CHECKLIST.md`
- [x] Prometheus alert rules mẫu: `deploy/prometheus/unutrip-rag-alerts.yml`
- [x] Manual CI package fixture bundle: `.github/workflows/rag-artifact-release.yml`
- [ ] Branch protection + bắt buộc `rag-ci` / `backend-ci` trên remote (GitHub repo settings)

### Chất lượng code (trung bình)

- [x] Test `rag_pipeline` unit (mocked) + `request_logger`
- [x] Bỏ omit retrieval: `place_store`, `bm25`, `hybrid`, `fusion`, `logger`, `rerank`
- [ ] Tiếp: admin/itinerary services, `travel_rules` branch coverage
- [x] `travel_rules` golden tests (`test_travel_rules_golden.py`)
- [x] Mypy: `repositories`, `retrieval.scoring` (chưa full `retrieval/` / `app/`)
- [x] `repositories/artifact_store.py` — artifact loader (align `RAG_ARCHITECTURE.md`)

### Retrieval & sản phẩm (trung bình)

- [ ] Golden production: `relevant_place_ids` trên full index (`eval/golden_queries.json`)
- [ ] Cross-encoder prod (`pip install -e ".[rerank]"`, `RAG_ENABLE_CROSS_ENCODER`)
- [x] Vector index / embedding — `07_build_embedding_index.py`, RRF với BM25+TF-IDF (`RAG_ENABLE_VECTOR`)
- [ ] Golden eval với vector bật trên full index

### Kiến trúc & API (thấp–trung bình)

- [ ] Tách `services/itinerary/category.py` (rule table / config)
- [ ] Deprecate route legacy — timeline chỉ `/v1`
- [ ] `ENABLE_LORA` / `ENABLE_VALIDATOR`: implement hoặc bỏ flag

---

## Sẽ làm tiếp theo (đề xuất thứ tự)

```text
Phase D — Artifact production + golden full index
    ↓
Phase E — Deploy checklist, alerting, staging E2E Node ↔ RAG
    ↓
Phase F — Coverage/mypy mở rộng; repositories layer
    ↓
Phase 8 — Android polish (sau API ổn trên staging)
```

---

## Lệnh dev (RAG)

```bash
cd backend/rag
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev]"

uvicorn app.main:app --reload --port 8001

make clean          # xóa .pytest_cache, egg-info, reports
make quality        # ruff + mypy + pytest (≥70%) + verify artifacts
make test-fast      # pytest không coverage
make typecheck      # mypy 5 package
```

**CI local (tương đương `rag-ci.yml`):**

```bash
ruff check app core domain generation llm pipelines providers retrieval services tests scripts
python -m mypy --explicit-package-bases -p core -p domain -p generation -p providers -p pipelines
python jobs/build_rag_artifacts.py --from-fixture
python -m pytest tests/ -q
python scripts/verify_rag_artifacts.py --strict
python scripts/eval_rag_retrieval.py --golden eval/golden_queries_ci.json --ci \
  --require-labels --min-province-accuracy 1.0 --min-hit-at5 0.75
docker build -t unutrip-rag:local .
```

---

## Cấu trúc package (sau Phase B)

```text
backend/rag/
  app/                    # FastAPI routers
  core/                   # config, artifacts, text_normalization, security
  domain/                 # models, contracts
  generation/             # context + prompt builders
  pipelines/
    rag_pipeline.py       # orchestration
    policies/             # location_filter, generation_router
    response_builder.py
  providers/              # gemini + template adapters
  repositories/           # artifact_store (Phase D)
  retrieval/
    hybrid_retriever.py
    scoring/              # travel_rules, dedup
  llm/                    # Gemini client, cache, executor
  services/
  tests/
```

---

## Tham chiếu

| Tài liệu | Nội dung |
|----------|----------|
| **`docs/v2/AGENT_GUIDE.md`** | **Handoff agent: đã làm / cần làm / lệnh / pitfalls** |
| `README_UPDATING_CLEAN.md` | Phase 0–7 (trước A–C) |
| `docs/v2/RAG_ARCHITECTURE.md` | Kiến trúc mục tiêu |
| `backend/rag/README.md` | Setup + quality |
| `backend/rag/docs/ARTIFACT_POLICY.md` | Manifest / rebuild |
| `backend/rag/pyproject.toml` | deps, pytest-cov omit, mypy |
