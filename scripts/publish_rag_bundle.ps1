# Task 1-2: build production RAG artifacts from DB, package zip, stage for deploy / optional S3 upload.
param(
    [switch]$SkipBuild,
    [string]$ZipOut = "backend/rag/dist/unutrip-rag-artifacts-prod.zip",
    [string]$StageDir = "deploy/staging-rag-data",
    [string]$S3Uri = $env:RAG_ARTIFACT_S3_URI
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Write-Error "Missing .env - set DB_NAME (e.g. unudata_v2_test). Run: python scripts/probe_mysql_rag.py"
}

Write-Host "== DB probe =="
python scripts/probe_mysql_rag.py

if (-not $SkipBuild) {
    Write-Host "`n== Task 1: build from DB =="
    Set-Location backend/rag
    python jobs/build_rag_artifacts.py --from-db --export-places
    Set-Location $Root
}

Write-Host "`n== Task 2: package zip =="
Set-Location backend/rag
python jobs/package_rag_artifacts.py -o (Join-Path $Root $ZipOut)
Set-Location $Root

$zipPath = Join-Path $Root $ZipOut
if (-not (Test-Path $zipPath)) {
    Write-Error "Zip not found: $zipPath"
}

Write-Host "`n== Stage for RAG_ARTIFACT_SOURCE_DIR =="
$stage = Join-Path $Root $StageDir
if (Test-Path $stage) {
    Remove-Item -Recurse -Force $stage
}
New-Item -ItemType Directory -Path $stage | Out-Null

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $stage)

# Zip layout is data/processed + data/indexes — flatten to stage root for artifact_store
$dataDir = Join-Path $stage "data"
if (Test-Path $dataDir) {
    Get-ChildItem $dataDir | ForEach-Object {
        Move-Item $_.FullName (Join-Path $stage $_.Name) -Force
    }
    Remove-Item -Recurse -Force $dataDir
}

$stageAbs = (Resolve-Path $stage).Path
Write-Host "Staged artifacts: $stageAbs"
Write-Host "  RAG_ARTIFACT_SOURCE_DIR=$stageAbs"

if ($S3Uri) {
    $aws = Get-Command aws -ErrorAction SilentlyContinue
    if (-not $aws) {
        Write-Warning "RAG_ARTIFACT_S3_URI set but aws CLI not found - upload manually:"
        Write-Host "  aws s3 cp `"$zipPath`" `"$S3Uri`""
    } else {
        Write-Host "`n== Upload to S3 =="
        & aws s3 cp $zipPath $S3Uri
        $publicUrl = $S3Uri -replace '^s3://([^/]+)/(.+)$', 'https://$1.s3.amazonaws.com/$2'
        Write-Host "Set deploy env: RAG_ARTIFACT_BUNDLE_URL=$publicUrl"
        Write-Host "(Adjust URL if using CloudFront or path-style endpoint.)"
    }
} else {
    Write-Host "`nOptional S3 upload:"
    Write-Host '  $env:RAG_ARTIFACT_S3_URI = "s3://your-bucket/releases/unutrip-rag-artifacts-prod.zip"'
    Write-Host "  .\scripts\publish_rag_bundle.ps1 -SkipBuild"
    Write-Host "`nGitHub Release (manual): upload $zipPath as release asset, then set RAG_ARTIFACT_BUNDLE_URL to the asset URL."
}

$meta = "$zipPath.RELEASE.json"
if (Test-Path $meta) {
    Write-Host "`nRelease metadata:"
    Get-Content $meta
}

Write-Host "`nDone. Commit manifest only if intentional: backend/rag/data/indexes/rag_artifacts_manifest.json"
