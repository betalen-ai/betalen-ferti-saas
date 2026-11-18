<#
.SYNOPSIS  Bootstrap the betalen-ferti-saas repo in the current directory.
.USAGE     cd C:\Users\PC\betalen-ai\betalen-ferti-saas ; .\bootstrap-repo.ps1
#>
param(
    [string]$RepoPath = $PWD.Path
)

$ErrorActionPreference = "Stop"
Write-Host "Scaffolding into $RepoPath" -ForegroundColor Cyan
Set-Location $RepoPath

# Write files as UTF-8 WITHOUT BOM (a BOM breaks .env and can break YAML)
function New-File($path, $content) {
    $full = Join-Path (Get-Location).Path $path
    $dir = Split-Path -Parent $full
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $text = ($content -replace "`r`n", "`n")
    [System.IO.File]::WriteAllText($full, $text, (New-Object System.Text.UTF8Encoding($false)))
}

# ---------- root files ----------
New-File "README.md" @'
# Betalen Ferti SaaS

Multi-tenant fertilizer retail SaaS.
Offline-first POS (Angular), org backoffice (React), FastAPI microservices, PostgreSQL.

## Quick start
```powershell
.\deploy-local.ps1
.\run-tests.ps1
```
'@

New-File ".gitignore" @'
.env
__pycache__/
*.pyc
*.pyo
.venv/
venv/
node_modules/
dist/
build/
*.log
.pytest_cache/
.coverage
htmlcov/
.DS_Store
Thumbs.db
'@

New-File ".env.example" @'
POSTGRES_USER=betalen
POSTGRES_PASSWORD=betalen_dev_pw
POSTGRES_DB=betalen_db
DATABASE_URL=postgresql+asyncpg://betalen:betalen_dev_pw@postgres:5432/betalen_db
REDIS_URL=redis://redis:6379/0
JWT_SECRET=change_me_in_prod
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120
'@

# ---------- postgres init ----------
New-File "postgres/init/01-init.sql" @'
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE SCHEMA IF NOT EXISTS org;
CREATE SCHEMA IF NOT EXISTS billing;
CREATE SCHEMA IF NOT EXISTS inventory;
CREATE SCHEMA IF NOT EXISTS reports;
CREATE SCHEMA IF NOT EXISTS shared;

CREATE TABLE org.tenants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  subdomain TEXT UNIQUE,
  subscription_plan TEXT DEFAULT 'free',
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE org.roles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES org.tenants(id) ON DELETE CASCADE,
  name TEXT NOT NULL);

CREATE TABLE org.permissions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  resource TEXT NOT NULL, action TEXT NOT NULL, UNIQUE(resource, action));

CREATE TABLE org.role_permissions (
  role_id UUID REFERENCES org.roles(id) ON DELETE CASCADE,
  permission_id UUID REFERENCES org.permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id));

CREATE TABLE org.org_users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES org.tenants(id) ON DELETE CASCADE,
  email TEXT NOT NULL, password_hash TEXT NOT NULL, full_name TEXT,
  role_id UUID REFERENCES org.roles(id), status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(tenant_id, email));

CREATE TABLE org.subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID REFERENCES org.tenants(id) ON DELETE CASCADE,
  plan TEXT NOT NULL, status TEXT NOT NULL,
  valid_from DATE NOT NULL, valid_to DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE inventory.warehouses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  name TEXT NOT NULL, location TEXT, created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE inventory.products (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  name TEXT NOT NULL, batch_no TEXT, expiry_date DATE,
  unit_price NUMERIC(12,2) NOT NULL DEFAULT 0, gst_rate NUMERIC(5,2) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE inventory.stock (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  warehouse_id UUID REFERENCES inventory.warehouses(id),
  product_id UUID REFERENCES inventory.products(id),
  quantity_on_hand NUMERIC(12,2) NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(warehouse_id, product_id));

CREATE TABLE billing.customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  name TEXT NOT NULL, phone TEXT,
  credit_limit NUMERIC(12,2) DEFAULT 0, balance_due NUMERIC(12,2) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE billing.invoices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  invoice_number TEXT NOT NULL, customer_id UUID REFERENCES billing.customers(id),
  total_amount NUMERIC(12,2) NOT NULL, status TEXT NOT NULL DEFAULT 'DRAFT',
  created_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(tenant_id, invoice_number));

CREATE TABLE billing.invoice_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  invoice_id UUID REFERENCES billing.invoices(id) ON DELETE CASCADE,
  product_id UUID NOT NULL, quantity NUMERIC(12,2) NOT NULL,
  unit_price NUMERIC(12,2) NOT NULL);

CREATE TABLE billing.payments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  invoice_id UUID REFERENCES billing.invoices(id),
  amount NUMERIC(12,2) NOT NULL, method TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'RECORDED', created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE billing.credit_ledger (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL,
  customer_id UUID REFERENCES billing.customers(id), type TEXT NOT NULL,
  amount NUMERIC(12,2) NOT NULL, running_balance NUMERIC(12,2) NOT NULL,
  reference_id UUID, created_at TIMESTAMPTZ DEFAULT NOW());

CREATE TABLE shared.sync_outbox (
  id BIGSERIAL PRIMARY KEY, tenant_id UUID NOT NULL, terminal_id TEXT NOT NULL,
  doc_type TEXT NOT NULL, doc_id UUID NOT NULL, payload JSONB NOT NULL,
  processed BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(doc_type, doc_id));
'@

# ---------- compose ----------
New-File "docker-compose.yml" @'
networks:
  betalen-net:
    driver: bridge

volumes:
  pg_data: {}
  redis_data: {}

services:
  postgres:
    image: postgres:16-alpine
    container_name: betalen-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-betalen}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-betalen_dev_pw}
      POSTGRES_DB: ${POSTGRES_DB:-betalen_db}
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U betalen -d betalen_db"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - betalen-net

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - betalen-net

  api-gateway:
    build: ./services/api-gateway
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - betalen-net

  beta_organization:
    build: ./services/beta_organization
    env_file: .env
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - betalen-net

  beta_billing:
    build: ./services/beta_billing
    env_file: .env
    ports:
      - "8002:8002"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - betalen-net

  beta_inventory:
    build: ./services/beta_inventory
    env_file: .env
    ports:
      - "8003:8003"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - betalen-net

  beta_reports:
    build: ./services/beta_reports
    env_file: .env
    ports:
      - "8004:8004"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - betalen-net

  shop-pos-angular:
    build: ./frontends/shop-pos-angular
    ports:
      - "4200:80"
    depends_on:
      - api-gateway
    networks:
      - betalen-net

  backoffice-react:
    build: ./frontends/backoffice-react
    ports:
      - "3000:80"
    depends_on:
      - api-gateway
    networks:
      - betalen-net
'@

New-File "docker-compose.test.yml" @'
services:
  postgres-test:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: betalen_test
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data

  beta_billing_tests:
    build: ./services/beta_billing
    command: pytest tests/ -v --cov=app
    environment:
      DATABASE_URL: postgresql+asyncpg://test:test@postgres-test:5432/betalen_test
    depends_on:
      - postgres-test

  beta_organization_tests:
    build: ./services/beta_organization
    command: pytest tests/ -v --cov=app
    environment:
      DATABASE_URL: postgresql+asyncpg://test:test@postgres-test:5432/betalen_test
    depends_on:
      - postgres-test

  beta_inventory_tests:
    build: ./services/beta_inventory
    command: pytest tests/ -v --cov=app
    environment:
      DATABASE_URL: postgresql+asyncpg://test:test@postgres-test:5432/betalen_test
    depends_on:
      - postgres-test
'@

# ---------- deploy / test scripts ----------
New-File "deploy-local.ps1" @'
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
'@

New-File "run-tests.ps1" @'
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from beta_billing_tests
$code = $LASTEXITCODE
docker compose -f docker-compose.test.yml down -v
exit $code
'@

# ---------- backend services ----------
$services = [ordered]@{
    "api-gateway"       = @{ port = 8000; routes = @("auth", "proxy"); desc = "Auth & routing" }
    "beta_organization" = @{ port = 8001; routes = @("tenants", "org_users", "roles", "subscriptions"); desc = "Org, users, roles, subscriptions" }
    "beta_billing"      = @{ port = 8002; routes = @("invoices", "payments", "credit_ledger"); desc = "Invoices, payments, credit ledger" }
    "beta_inventory"    = @{ port = 8003; routes = @("products", "warehouses", "stock"); desc = "Products, warehouses, stock" }
    "beta_reports"      = @{ port = 8004; routes = @("dashboards", "exports"); desc = "Dashboards & exports" }
}

$requirements = @'
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
pydantic-settings==2.5.2
sqlalchemy==2.0.35
asyncpg==0.29.0
alembic==1.13.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.2
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
psycopg2-binary==2.9.9
'@

$dockerTpl = @'
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE __PORT__
HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD curl -f http://localhost:__PORT__/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "__PORT__"]
'@

$mainTpl = @'
from fastapi import FastAPI
__IMPORTS__

app = FastAPI(title="__NAME__", version="0.1.0")

__INCLUDES__


@app.get("/health")
def health():
    return {"status": "ok", "service": "__NAME__"}
'@

$routeTpl = @'
from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_items():
    return {"items": [], "resource": "__R__"}
'@

$configPy = @'
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://betalen:betalen_dev_pw@postgres:5432/betalen_db"
    JWT_SECRET: str = "change_me_in_prod"
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
'@

$dbPy = @'
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as s:
        yield s
'@

$testTpl = @'
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "__NAME__"
'@

$pytestIni = @'
[pytest]
asyncio_mode = auto
pythonpath = .
'@

foreach ($name in $services.Keys) {
    $info = $services[$name]
    $base = "services/$name"

    New-File "$base/Dockerfile" ($dockerTpl.Replace("__PORT__", [string]$info.port))
    New-File "$base/requirements.txt" $requirements
    New-File "$base/pytest.ini" $pytestIni

    $imports = ($info.routes | ForEach-Object { "from app.routes import $_" }) -join "`n"
    $includes = ($info.routes | ForEach-Object { "app.include_router($_.router, prefix=`"/$_`", tags=[`"$_`"])" }) -join "`n"
    $main = $mainTpl.Replace("__IMPORTS__", $imports).Replace("__INCLUDES__", $includes).Replace("__NAME__", $name)
    New-File "$base/app/main.py" $main
    New-File "$base/app/__init__.py" ""
    New-File "$base/app/routes/__init__.py" ""

    foreach ($r in $info.routes) {
        New-File "$base/app/routes/$r.py" ($routeTpl.Replace("__R__", $r))
    }
    foreach ($f in @("models", "schemas", "services")) {
        New-File "$base/app/$f/__init__.py" ""
    }

    New-File "$base/app/config.py" $configPy
    New-File "$base/app/db.py" $dbPy
    New-File "$base/tests/__init__.py" ""
    New-File "$base/tests/test_health.py" ($testTpl.Replace("__NAME__", $name))

    $readme = @'
# __NAME__

__DESC__

Port: __PORT__

## Run
```
docker compose up __NAME__
```
'@
    New-File "$base/README.md" ($readme.Replace("__NAME__", $name).Replace("__DESC__", $info.desc).Replace("__PORT__", [string]$info.port))
}

# ---------- frontends (placeholders: static page served by nginx) ----------
$nginxConf = @'
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    location / { try_files $uri $uri/ /index.html; }
    location /api/ { proxy_pass http://api-gateway:8000/; }
}
'@

$feDocker = @'
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
'@

$frontends = @(
    @{ dir = "shop-pos-angular"; title = "Fertilizer Shop POS (Angular) - offline-capable"; pkg = "shop-pos" },
    @{ dir = "backoffice-react"; title = "Organization Backoffice (React) - tenant management"; pkg = "backoffice" }
)
foreach ($fe in $frontends) {
    $d = "frontends/$($fe.dir)"
    New-File "$d/README.md" "# $($fe.title)`n`nPlaceholder page. Replace with the real app and update the Dockerfile to build it."
    New-File "$d/package.json" ('{ "name": "' + $fe.pkg + '", "version": "0.1.0" }')
    New-File "$d/Dockerfile" $feDocker
    New-File "$d/nginx.conf" $nginxConf
    New-File "$d/index.html" ("<!doctype html><html><head><meta charset=`"utf-8`"><title>$($fe.title)</title></head><body><h1>$($fe.title)</h1><p>Placeholder.</p></body></html>")
}

Write-Host ""
Write-Host "Repo scaffolded at $RepoPath" -ForegroundColor Green
Write-Host "Next: .\deploy-local.ps1" -ForegroundColor Cyan