# Phase E - staging smoke (Node <-> RAG). Stack must be running locally.
$ErrorActionPreference = "Stop"

$RagBase = if ($env:RAG_BASE_URL) { $env:RAG_BASE_URL } else { "http://127.0.0.1:8001" }
$NodeBase = if ($env:NODE_BASE_URL) { $env:NODE_BASE_URL } else { "http://127.0.0.1:3000" }
$RagKey = $env:RAG_INTERNAL_API_KEY

function Fail($msg) { Write-Error "FAIL: $msg"; exit 1 }
function Ok($msg) { Write-Host "OK: $msg" }

try { Invoke-WebRequest -Uri "$RagBase/health" -UseBasicParsing | Out-Null } catch { Fail "RAG /health" }
Ok "RAG /health"

try { Invoke-WebRequest -Uri "$RagBase/health/ready" -UseBasicParsing | Out-Null } catch { Fail "RAG /health/ready" }
Ok "RAG /health/ready"

try { Invoke-WebRequest -Uri "$NodeBase/api/health" -UseBasicParsing | Out-Null } catch { Fail "Node /api/health" }
Ok "Node /api/health"

try { Invoke-WebRequest -Uri "$NodeBase/api/health/ready" -UseBasicParsing | Out-Null } catch { Fail "Node /api/health/ready" }
Ok "Node /api/health/ready"

try {
    $dest = Invoke-RestMethod -Uri "$NodeBase/api/destinations?limit=1" -UseBasicParsing
    $total = [int]$dest.total
    if ($total -gt 0) { Ok "Node destinations total=$total" }
    else { Write-Host "WARN: app_places empty or list failed (total=$total)" }
} catch {
    Write-Host "WARN: could not fetch destinations list"
}

if ($RagKey) {
    $body = '{"message":"diem tham quan Ha Giang","top_k":3}'
    $headers = @{
        "X-RAG-Internal-Key" = $RagKey
        "Content-Type"       = "application/json"
    }
    try {
        $resp = Invoke-WebRequest -Uri "$RagBase/v1/rag/chat/simple" -Method POST -Headers $headers -Body $body -UseBasicParsing
        if ($resp.StatusCode -ne 200) { Fail "RAG chat/simple HTTP $($resp.StatusCode)" }
    } catch {
        Fail "RAG /v1/rag/chat/simple: $($_.Exception.Message)"
    }
    Ok "RAG /v1/rag/chat/simple"
} else {
    Write-Host "SKIP: RAG chat (set RAG_INTERNAL_API_KEY)"
}

Write-Host "Smoke staging E2E passed."
