# D1 — Build RAG corpus from staging/production MySQL (rag_knowledge_base).
# Requires: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME in environment or .env
#
# Usage (repo root):
#   $env:DB_HOST="127.0.0.1"; $env:DB_USER="..."; $env:DB_PASSWORD="..."; $env:DB_NAME="unudata"
#   powershell -ExecutionPolicy Bypass -File .\scripts\build_rag_staging_corpus.ps1

param(
    [int]$MinRagDocs = $(if ($env:MIN_RAG_DOCS) { [int]$env:MIN_RAG_DOCS } else { 500 }),
    [switch]$Package,
    [switch]$SkipEval
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Rag = Join-Path $Root "backend\rag"

foreach ($name in @("DB_HOST", "DB_USER", "DB_NAME")) {
    if (-not (Get-Item -Path "Env:$name" -ErrorAction SilentlyContinue)) {
        Write-Error "Set $name before running D1 build (MySQL connection)."
    }
}

Write-Host "+ D1 build from DB: $env:DB_HOST / $env:DB_NAME (min docs: $MinRagDocs)"
Push-Location $Rag
try {
    python jobs/build_rag_artifacts.py --from-db --export-places
    if ($LASTEXITCODE -ne 0) { throw "build_rag_artifacts failed" }

    python scripts/verify_rag_artifacts.py --strict
    if ($LASTEXITCODE -ne 0) { throw "verify_rag_artifacts failed" }

    $manifestPath = Join-Path $Rag "data\indexes\rag_artifacts_manifest.json"
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    $count = [int]$manifest.document_count
    Write-Host "document_count=$count"
    if ($count -lt $MinRagDocs) {
        throw "D1 FAIL: document_count $count < $MinRagDocs"
    }
    Write-Host "OK document_count >= $MinRagDocs"

    if (-not $SkipEval) {
        Write-Host "+ golden eval (province accuracy)"
        python scripts/eval_rag_retrieval.py `
            --golden eval/golden_queries.json `
            --ci `
            --min-province-accuracy 1.0 `
            --min-hit-at5 0.75
        if ($LASTEXITCODE -ne 0) { throw "eval_rag_retrieval failed" }
    }

    if ($Package) {
        Write-Host "+ package zip"
        python jobs/package_rag_artifacts.py
        if ($LASTEXITCODE -ne 0) { throw "package_rag_artifacts failed" }
    }

    Write-Host "D1 staging corpus build OK"
}
finally {
    Pop-Location
}
