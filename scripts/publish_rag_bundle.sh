#!/usr/bin/env bash
# Task 1-2: build production RAG artifacts, package zip, stage for deploy / optional S3.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ZIP_OUT="${ZIP_OUT:-backend/rag/dist/unutrip-rag-artifacts-prod.zip}"
STAGE_DIR="${STAGE_DIR:-deploy/staging-rag-data}"
SKIP_BUILD="${SKIP_BUILD:-0}"

[[ -f .env ]] || { echo "Missing .env"; exit 1; }

echo "== DB probe =="
python scripts/probe_mysql_rag.py

if [[ "$SKIP_BUILD" != "1" ]]; then
  echo "== Task 1: build from DB =="
  (cd backend/rag && python jobs/build_rag_artifacts.py --from-db --export-places)
fi

echo "== Task 2: package zip =="
(cd backend/rag && python jobs/package_rag_artifacts.py -o "$ROOT/$ZIP_OUT")

STAGE="$ROOT/$STAGE_DIR"
rm -rf "$STAGE"
mkdir -p "$STAGE"
unzip -q "$ROOT/$ZIP_OUT" -d "$STAGE"
if [[ -d "$STAGE/data" ]]; then
  mv "$STAGE"/data/* "$STAGE/"
  rmdir "$STAGE/data"
fi

echo "Staged: $STAGE"
echo "  export RAG_ARTIFACT_SOURCE_DIR=$STAGE"

if [[ -n "${RAG_ARTIFACT_S3_URI:-}" ]]; then
  aws s3 cp "$ROOT/$ZIP_OUT" "$RAG_ARTIFACT_S3_URI"
  echo "Uploaded. Set RAG_ARTIFACT_BUNDLE_URL to your public HTTPS URL for the object."
fi

echo "Done."
