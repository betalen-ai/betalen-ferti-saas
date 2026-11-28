param([switch]$Rebuild)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "=== Betalen Ferti SaaS - Local Deploy ===" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Write-Error "Docker missing"; exit 1 }
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

if ($Rebuild) { docker compose build --no-cache }
docker compose up -d --build

Write-Host "Waiting for Postgres..." -ForegroundColor Yellow
$t = 0
while ($t -lt 30) {
    $s = docker inspect --format='{{.State.Health.Status}}' betalen-postgres 2>$null
    if ($s -eq 'healthy') { break }
    Start-Sleep 2
    $t++
}

Start-Sleep 5
$urls = @(
    "http://localhost:8000/health",
    "http://localhost:8001/health",
    "http://localhost:8002/health",
    "http://localhost:8003/health",
    "http://localhost:8004/health"
)
foreach ($u in $urls) {
    try {
        $r = Invoke-WebRequest $u -UseBasicParsing -TimeoutSec 5
        Write-Host "OK   $u ($($r.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "FAIL $u" -ForegroundColor Red
    }
}
Write-Host ""
Write-Host "POS:        http://localhost:4200" -ForegroundColor Green
Write-Host "Backoffice: http://localhost:3000" -ForegroundColor Green
Write-Host "Gateway:    http://localhost:8000/docs" -ForegroundColor Green