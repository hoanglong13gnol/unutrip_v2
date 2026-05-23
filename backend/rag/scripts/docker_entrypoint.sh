#!/bin/sh
set -e
cd /svc

if [ ! -f data/indexes/bm25_index.pkl ]; then
  echo "+ BM25 index missing; building from fixture..."
  python jobs/build_rag_artifacts.py --from-fixture
fi

if [ -n "${RAG_ARTIFACT_BUNDLE_URL:-}" ] || [ -n "${RAG_ARTIFACT_SOURCE_DIR:-}" ]; then
  python scripts/fetch_rag_artifacts.py
fi

exec "$@"
