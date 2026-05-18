#!/bin/sh
set -e
cd /svc

if [ -n "${RAG_ARTIFACT_BUNDLE_URL:-}" ] || [ -n "${RAG_ARTIFACT_SOURCE_DIR:-}" ]; then
  python scripts/fetch_rag_artifacts.py
fi

exec "$@"
