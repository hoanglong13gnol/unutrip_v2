# Tài liệu kỹ thuật UNUTrip v2

Thư mục này chứa **tài liệu vận hành và kiến trúc** cho dev/agent.  
Tài liệu luận văn / use case / BPMN nằm ở [`backup_suport_file/`](../../backup_suport_file/) (không phải nguồn sự thật về code).

## Đọc theo thứ tự

| # | File | Khi nào đọc |
|---|------|-------------|
| 1 | [`AGENT_GUIDE.md`](AGENT_GUIDE.md) | Onboarding: kiến trúc, lệnh, CI, pitfalls |
| 2 | [`BACKEND_RAG_BOUNDARY.md`](BACKEND_RAG_BOUNDARY.md) | Ranh giới Node ↔ RAG (bắt buộc trước khi sửa AI) |
| 3 | [`NAMING.md`](NAMING.md) | Tra cứu tên product / DB / package |
| 4 | [`PHASE7_NODE_ANDROID_PARITY.md`](PHASE7_NODE_ANDROID_PARITY.md) | Flags v2, resolve `rawPlaceId`, contract JSON |
| 5 | [`README_TOTAL_GUIDE.md`](README_TOTAL_GUIDE.md) | Backlog kỹ thuật P0–P3 (nợ còn lại) |

## Kiến trúc & kế hoạch (reference)

| File | Nội dung |
|------|----------|
| [`BACKEND_ARCHITECTURE.md`](BACKEND_ARCHITECTURE.md) | Node: layers, module ownership, trạng thái migration v2 |
| [`RAG_ARCHITECTURE.md`](RAG_ARCHITECTURE.md) | FastAPI RAG: layers, corpus, artifacts |
| [`REFACTOR_PHASE_PLAN.md`](REFACTOR_PHASE_PLAN.md) | Lịch sử phase 1–8 + trạng thái hoàn thành |

## Fixture dùng chung

- [`fixtures/rag_chat_simple_sample.json`](fixtures/rag_chat_simple_sample.json) — mẫu response `/rag/chat/simple` cho test parity Node + RAG.

## Tài liệu liên quan (ngoài `docs/v2/`)

| Path | Nội dung |
|------|----------|
| [`../../README.md`](../../README.md) | Tổng quan monorepo |
| [`../../database/README.md`](../../database/README.md) | Migrations, bootstrap Docker |
| [`../../backend/rag/README.md`](../../backend/rag/README.md) | Setup RAG local |
| [`../../backend/rag/docs/`](../../backend/rag/docs/) | Artifact, deploy, retrieval, production |
| [`../../deploy/README.md`](../../deploy/README.md) | Port stack, thứ tự khởi động |
| [`../../backup_suport_file/README_UPDATING_CLEAN_v2.md`](../../backup_suport_file/README_UPDATING_CLEAN_v2.md) | Lịch sử phase (archive) |

## Stack (tóm tắt)

```
Android (app/)  →  Node :3000/api/*  →  RAG :8001/v1/*
                      ↓
                   MySQL (app_places, itineraries, …)
RAG đọc BM25 index trên disk; Gemini qua RAG only.
```
