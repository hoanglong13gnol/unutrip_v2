# One-shot local staging: build RAG artifacts from DB, probe DB, print start commands.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Write-Error "Missing .env — copy .env.example and set DB_NAME (e.g. unudata_v2_test)"
}

Write-Host "== DB probe =="
python scripts/probe_mysql_rag.py

Write-Host "`n== Build RAG artifacts (--from-db) =="
Set-Location backend/rag
python jobs/build_rag_artifacts.py --from-db --export-places
python scripts/verify_rag_artifacts.py --strict
Set-Location $Root

Write-Host "`n== Done. Start stack (two terminals): =="
Write-Host "  Terminal 1: cd backend/rag && uvicorn app.main:app --reload --port 8001"
Write-Host "  Terminal 2: cd backend/nodejs && npm start"
Write-Host "`nThen: .\scripts\smoke_staging_e2e.ps1"
