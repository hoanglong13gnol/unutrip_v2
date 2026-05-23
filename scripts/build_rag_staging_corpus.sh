#!/usr/bin/env bash
# D1 — Build RAG corpus from staging/production MySQL (rag_knowledge_base).
#
# Prerequisites:
#   - MySQL reachable; DB_* env set (same as Node .env)
#   - rag_knowledge_base populated (migration 009 or manual import)
#
# Usage (repo root):
#   export DB_HOST=127.0.0.1 DB_USER=... DB_PASSWORD=... DB_NAME=unudata
#   bash scripts/build_rag_staging_corpus.sh
#
# Optional:
#   MIN_RAG_DOCS=500          — fail if document_count below threshold (default 500)
#   PACKAGE=1                 — run jobs/package_rag_artifacts.py after verify
#   SKIP_EVAL=1             — skip golden province eval

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAG="$ROOT/backend/rag"
MIN_DOCS="${MIN_RAG_DOCS:-500}"

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "ERROR: set $name (DB connection for --from-db export)" >&2
    exit 1
  fi
}

require_env DB_HOST
require_env DB_USER
require_env DB_NAME

echo "+ D1 build from DB: $DB_HOST / $DB_NAME (min docs: $MIN_DOCS)"
cd "$RAG"

python jobs/build_rag_artifacts.py --from-db --export-places
python scripts/verify_rag_artifacts.py --strict

python - <<PY
import json
import os
import sys
from pathlib import Path

manifest = Path("data/indexes/rag_artifacts_manifest.json")
if not manifest.is_file():
    print("ERROR: manifest missing after build", file=sys.stderr)
    sys.exit(1)
data = json.loads(manifest.read_text(encoding="utf-8"))
count = int(data.get("document_count") or 0)
min_docs = int(os.environ.get("MIN_RAG_DOCS", "500"))
print(f"document_count={count}")
if count < min_docs:
    print(f"D1 FAIL: document_count {count} < {min_docs}", file=sys.stderr)
    sys.exit(1)
print(f"OK document_count >= {min_docs}")
PY

if [[ "${SKIP_EVAL:-0}" != "1" ]]; then
  echo "+ golden eval (province accuracy)"
  python scripts/eval_rag_retrieval.py \
    --golden eval/golden_queries.json \
    --ci \
    --min-province-accuracy 1.0 \
    --min-hit-at5 0.75
fi

if [[ "${PACKAGE:-0}" == "1" ]]; then
  echo "+ package zip"
  python jobs/package_rag_artifacts.py
fi

echo "D1 staging corpus build OK"
