# UNUtrip v2 — Làm sạch & nâng cấp RAG (v2 roadmap)

Tài liệu theo dõi **Phase A → C** (refactor kiến trúc + chất lượệ) trên `backend/rag/`.  
Bản trước: `README_UPDATING_CLEAN.md` (Phase 0–7). Demo gốc `e:\UNUtrip` **không** bị sửa.

**Cập nhật:** sau commit Phase A–C trên `master`.

---

## Tóm tắt nhanh

| Hạng mục | Trạng thái |
|----------|------------|
| Phase A — Hygiene & deps | ✅ Xong |
| Phase B — Tách pipeline / scoring / providers | ✅ Xong |
| Phase C — Mypy, coverage 70%, CI Docker | ✅ Xong |
| Phase D — Dữ liệu & artifact production | 🟡 Một phần (fetch/package/entrypoint) |
| Phase E — Deploy / observability | 🟡 Một phần (`docs/DEPLOY_CHECKLIST.md`) |
| Phase 8 — Android polish | ⏳ Chưa |

**Chất lượệ hiện tại:** 75 pytest pass · ruff sạch · mypy (5 package) sạch · coverage gate **≥70%** (phạm vi đã `omit` trong `pyproject.toml`).

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
- [ ] Alerting rules thực tế (Prometheus/Grafana) theo checklist
- [ ] Branch protection + bắt buộc `rag-ci` / `backend-ci` trên remote

### Chất lượng code (trung bình)

- [ ] Mở rộng coverage: bỏ dần `omit` — test `rag_pipeline` E2E, `place_store`, `data_quality_service`
- [ ] `travel_rules.py` (~50% coverage) — golden tests theo interest/province
- [ ] Mypy mở rộng: `retrieval/`, `services/`, `app/` (hiện `follow_imports=skip`)
- [x] `repositories/artifact_store.py` — artifact loader (align `RAG_ARCHITECTURE.md`)

### Retrieval & sản phẩm (trung bình)

- [ ] Golden production: `relevant_place_ids` trên full index (`eval/golden_queries.json`)
- [ ] Cross-encoder prod (`pip install -e ".[rerank]"`, `RAG_ENABLE_CROSS_ENCODER`)
- [ ] Vector index / embedding (nếu scale)

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
| `README_UPDATING_CLEAN.md` | Phase 0–7 (trước A–C) |
| `docs/v2/RAG_ARCHITECTURE.md` | Kiến trúc mục tiêu |
| `backend/rag/README.md` | Setup + quality |
| `backend/rag/docs/ARTIFACT_POLICY.md` | Manifest / rebuild |
| `backend/rag/pyproject.toml` | deps, pytest-cov omit, mypy |
