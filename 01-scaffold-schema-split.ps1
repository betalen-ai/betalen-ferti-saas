# 01-scaffold-schema-split.ps1 — creates directories only
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "Creating directories..." -ForegroundColor Cyan

$dirs = @(
    "services\beta_billing\app\models",
    "services\beta_inventory\app\models",
    "services\beta_organization\app\services",
    "services\beta_billing\alembic\versions",
    "services\beta_inventory\alembic\versions"
)
foreach ($d in $dirs) {
    $p = Join-Path $root $d
    if (-not (Test-Path $p)) {
        New-Item -ItemType Directory -Force -Path $p | Out-Null
        Write-Host "  + $d" -ForegroundColor Green
    } else {
        Write-Host "  = $d (exists)" -ForegroundColor DarkGray
    }
}

Write-Host "`nDone. Next: run 02-write-db-files.ps1" -ForegroundColor Green