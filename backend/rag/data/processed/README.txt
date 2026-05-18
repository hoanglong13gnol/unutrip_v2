This directory holds generated RAG corpora (e.g. places_rag_documents.jsonl).

Not committed (see .gitignore). For CI/offline builds without DB:
  python jobs/build_rag_artifacts.py --from-fixture

For production export from MySQL:
  python jobs/build_rag_artifacts.py --from-db --export-places

See backend/rag/docs/ARTIFACT_POLICY.md.
