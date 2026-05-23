#!/bin/sh
set -e
cd /svc
export PYTHONPATH=/svc

if [ ! -f data/indexes/bm25_index.pkl ]; then
  echo "+ BM25 index missing; building from fixture (in-process)..."
  python jobs/build_rag_artifacts.py --from-fixture
fi

if [ -n "${RAG_ARTIFACT_BUNDLE_URL:-}" ] || [ -n "${RAG_ARTIFACT_SOURCE_DIR:-}" ]; then
  if ! python scripts/fetch_rag_artifacts.py; then
    echo "WARN: fetch_rag_artifacts failed; continuing if index exists" >&2
    if [ ! -f data/indexes/bm25_index.pkl ]; then
      echo "ERROR: no BM25 index after fetch failure" >&2
      exit 1
    fi
  fi
fi

exec "$@"
