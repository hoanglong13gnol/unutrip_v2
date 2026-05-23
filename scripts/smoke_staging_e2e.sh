#!/usr/bin/env bash
# Phase E — quick staging smoke (Node ↔ RAG). Requires stack up: docker compose up -d
set -euo pipefail

RAG_BASE="${RAG_BASE_URL:-http://127.0.0.1:8001}"
NODE_BASE="${NODE_BASE_URL:-http://127.0.0.1:3000}"
RAG_KEY="${RAG_INTERNAL_API_KEY:-}"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "OK: $*"; }

curl -sf "$RAG_BASE/health" >/dev/null || fail "RAG /health"
ok "RAG /health"

curl -sf "$RAG_BASE/health/ready" >/dev/null || fail "RAG /health/ready (index + config)"
ok "RAG /health/ready"

curl -sf "$NODE_BASE/api/health" >/dev/null || fail "Node /api/health"
ok "Node /api/health"

curl -sf "$NODE_BASE/api/health/ready" >/dev/null || fail "Node /api/health/ready"
ok "Node /api/health/ready"

dest_count=$(curl -sf "$NODE_BASE/api/destinations?limit=1" | python -c "import json,sys; d=json.load(sys.stdin); print(d.get('total',0))" 2>/dev/null || echo 0)
if [[ "${dest_count:-0}" -gt 0 ]]; then
  ok "Node destinations total=$dest_count"
else
  echo "WARN: app_places empty or list failed (total=$dest_count)"
fi

if [[ -n "$RAG_KEY" ]]; then
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "X-RAG-Internal-Key: $RAG_KEY" \
    -H "Content-Type: application/json" \
    -d '{"message":"điểm tham quan Hà Giang","top_k":3}' \
    "$RAG_BASE/v1/rag/chat/simple")
  [[ "$code" == "200" ]] || fail "RAG chat/simple HTTP $code"
  ok "RAG /v1/rag/chat/simple"
else
  echo "SKIP: RAG chat (set RAG_INTERNAL_API_KEY)"
fi

echo "Smoke staging E2E passed."
