# Complete README with Architecture & Local Deployment Guide

Replace your current `README.md` at `C:\Users\PC\betalen-ai\betalen-ferti-saas\README.md` with the full version below.

---

## How to Save

**Option A — Notepad (recommended for long files):**

```powershell
notepad C:\Users\PC\betalen-ai\betalen-ferti-saas\README.md
```

Paste the entire block below, `Ctrl+S`, close.

**Option B — VS Code:**

```powershell
code C:\Users\PC\betalen-ai\betalen-ferti-saas\README.md
```

**Verify after saving:**

```powershell
(Get-Item .\README.md).Length
# expect: 12000+ bytes (not a tiny stub)
```

---

## Full `README.md` Content

```markdown
# Betalen Ferti SaaS

Multi-tenant SaaS platform for fertilizer retail shops.

**Offline-first POS (Angular) · Org backoffice (React) · FastAPI microservices · PostgreSQL**

Betalen Ferti SaaS lets any fertilizer shop sign up, bill farmers (including credit/Udhaar),
manage inventory with batch + expiry tracking, record cash and UPI payments, and reconcile
everything even when the network drops.

---

## Table of Contents

1. [What This System Does](#1-what-this-system-does)
2. [Architecture Overview](#2-architecture-overview)
3. [Services & Ports](#3-services--ports)
4. [Repository Structure](#4-repository-structure)
5. [Database Design](#5-database-design)
6. [Offline-First & Sync Model](#6-offline-first--sync-model)
7. [Prerequisites](#7-prerequisites)
8. [Local Deployment — Step by Step](#8-local-deployment--step-by-step)
9. [Running Tests](#9-running-tests)
10. [Common Commands](#10-common-commands)
11. [Troubleshooting](#11-troubleshooting)
12. [Roadmap](#12-roadmap)

---

## 1. What This System Does

| Capability | Description |
|---|---|
| **Billing / Invoicing** | GST/non-GST invoices with batch number + expiry, thermal print or WhatsApp PDF |
| **Customer Credit (Udhaar)** | Per-farmer ledger with running balance, credit limit checks, offline recording |
| **Inventory** | Products, warehouses, batch/expiry, multi-terminal stock aggregation |
| **Payments** | Cash, UPI (record-only or link-generated), credit settlement |
| **Offline-first** | POS keeps billing, inventory deduction, and credit ledger working without network |
| **Multi-tenant SaaS** | Each shop is a tenant; shop owner self-signs, no manual onboarding |
| **Roles & Permissions** | Owner, Manager, Cashier — resource/action based |
| **Subscriptions** | Free / Paid plans per tenant |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENTS (Browsers)                          │
│  ┌──────────────────────┐          ┌──────────────────────────┐     │
│  │  Shop POS (Angular)  │          │ Backoffice (React)       │     │
│  │  Fertilizer Retail   │          │ Org / Tenant Management  │     │
│  └──────────┬───────────┘          └────────────┬─────────────┘     │
└─────────────┼───────────────────────────────────┼───────────────────┘
              │ HTTPS                             │ HTTPS
              ▼                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     API GATEWAY (FastAPI) :8000                     │
│             Auth (JWT) • Routing • Rate Limit • CORS                │
└───────┬──────────────┬──────────────┬──────────────┬────────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│beta_org      ││beta_billing  ││beta_inventory││beta_reports  │
│:8001         ││:8002         ││:8003         ││:8004         │
│Tenants/Users ││Invoices/     ││Products/     ││Dashboards/   │
│Roles/Subs    ││Payments/     ││Warehouses/   ││Exports       │
│              ││Credit Ledger ││Stock         ││              │
└──────┬───────┘└──────┬───────┘└──────┬───────┘└──────┬───────┘
       │               │               │               │
       └───────────────┴───────┬───────┴───────────────┘
                               ▼
                  ┌──────────────────────────┐
                  │  PostgreSQL 16 :5432     │
                  │  betalen_db              │
                  │  Schemas: org, billing,  │
                  │  inventory, reports,     │
                  │  shared (outbox)         │
                  └──────────────────────────┘
                               ▲
                  ┌────────────┴─────────────┐
                  │  Redis 7 :6379 (optional)│
                  │  Cache / Session / Queue │
                  └──────────────────────────┘
```

**Design principles**

- **Service independence** — every backend service has its own `Dockerfile`, `requirements.txt`,
  `app/routes`, `app/schemas`, `app/services`, `tests`. Can be built, tested, deployed alone.
- **Single database** — one PostgreSQL instance; each service owns a schema. Cross-schema
  joins avoided in code; services talk via HTTP or shared tables (`shared.sync_outbox`).
- **Tenant isolation** — `tenant_id` column on every business row. Enforced in service layer.
- **Idempotency** — invoices use `UNIQUE(tenant_id, invoice_number)`; outbox uses
  `UNIQUE(doc_type, doc_id)` so offline replays can't duplicate.
- **Offline-first POS** — Angular caches master data locally, writes invoices to IndexedDB +
  outbox, syncs when online.

---

## 3. Services & Ports

| Service | Tech | Port | Purpose |
|---|---|---|---|
| `shop-pos-angular` | Angular 17 | **4200** | Fertilizer shop POS (offline-capable) |
| `backoffice-react` | React 18 + Vite | **3000** | Tenant / org admin UI |
| `api-gateway` | FastAPI | **8000** | Auth (JWT), routing, CORS |
| `beta_organization` | FastAPI | **8001** | Tenants, users, roles, permissions, subscriptions |
| `beta_billing` | FastAPI | **8002** | Invoices, payments, customer credit ledger |
| `beta_inventory` | FastAPI | **8003** | Products, warehouses, stock |
| `beta_reports` | FastAPI | **8004** | Dashboards, exports |
| `postgres` | PostgreSQL 16 | **5432** | Single shared database |
| `redis` | Redis 7 | **6379** | Cache / queue (optional) |

Every backend service exposes:

- `GET /health` → `{"status":"ok","service":"<name>"}`
- `GET /docs` → Swagger UI
- `GET /openapi.json` → OpenAPI spec

---

## 4. Repository Structure

```
betalen-ferti-saas/
├── README.md                       # this file
├── .env.example                    # copy to .env before deploy
├── .gitignore
├── docker-compose.yml              # dev stack (all services + DB)
├── docker-compose.test.yml         # isolated test stack (tmpfs Postgres)
├── deploy-local.ps1                # one-command local deploy
├── run-tests.ps1                   # one-command test runner
├── bootstrap-repo.ps1              # scaffolding script (already run)
│
├── postgres/
│   └── init/
│       └── 01-init.sql             # schemas + tables created at first boot
│
├── services/
│   ├── api-gateway/
│   │   ├── app/
│   │   │   ├── main.py             # FastAPI app + /health
│   │   │   ├── config.py           # pydantic-settings
│   │   │   ├── db.py               # async SQLAlchemy engine
│   │   │   └── routes/
│   │   │       ├── auth.py
│   │   │       └── proxy.py
│   │   ├── tests/
│   │   │   └── test_health.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   │
│   ├── beta_organization/          # same layout, routes:
│   │   └── app/routes/             # tenants.py, org_users.py,
│   │                               # roles.py, subscriptions.py
│   │
│   ├── beta_billing/               # routes:
│   │   └── app/routes/             # invoices.py, payments.py,
│   │                               # credit_ledger.py
│   │
│   ├── beta_inventory/             # routes:
│   │   └── app/routes/             # products.py, warehouses.py, stock.py
│   │
│   └── beta_reports/               # routes:
│       └── app/routes/             # dashboards.py, exports.py
│
└── frontends/
    ├── shop-pos-angular/
    │   ├── Dockerfile
    │   ├── nginx.conf
    │   ├── package.json
    │   └── README.md
    └── backoffice-react/
        ├── Dockerfile
        ├── nginx.conf
        ├── package.json
        └── README.md
```

Every backend service follows the **identical internal structure**:

```
<service>/
├── app/
│   ├── main.py          # FastAPI entry, includes routers + /health
│   ├── config.py        # settings (DATABASE_URL, JWT_SECRET, ...)
│   ├── db.py            # async engine + session dependency
│   ├── routes/          # HTTP endpoints (thin — delegate to services)
│   ├── schemas/         # Pydantic request/response models
│   ├── services/        # business logic (credit checks, idempotency)
│   ├── validations/     # custom validators
│   ├── integrations/    # UPI, WhatsApp, GST external calls
│   └── models/          # SQLAlchemy ORM (added in later steps)
├── tests/               # pytest suite
├── publishing/          # Docker push scripts
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 5. Database Design

**One PostgreSQL database (`betalen_db`) with five schemas.**

| Schema | Owner service | Tables |
|---|---|---|
| `org` | `beta_organization` | `tenants`, `org_users`, `roles`, `permissions`, `role_permissions`, `subscriptions` |
| `inventory` | `beta_inventory` | `warehouses`, `products`, `stock` |
| `billing` | `beta_billing` | `customers`, `invoices`, `invoice_items`, `payments`, `credit_ledger` |
| `reports` | `beta_reports` | (materialized views added later) |
| `shared` | all | `sync_outbox` (offline replay dedup) |

**Key constraints**

- `org.org_users` → `UNIQUE(tenant_id, email)`
- `billing.invoices` → `UNIQUE(tenant_id, invoice_number)` ← idempotency key
- `shared.sync_outbox` → `UNIQUE(doc_type, doc_id)` ← offline replay safety
- `inventory.stock` → `UNIQUE(warehouse_id, product_id)`

Full DDL lives in `postgres/init/01-init.sql` and runs automatically on first Postgres start
(the `docker-entrypoint-initdb.d` convention).

---

## 6. Offline-First & Sync Model

```
POS (Angular)                    Server (FastAPI + PG)
─────────────                    ─────────────────────
1. Cashier bills offline
   ├─ write invoice to IndexedDB
   ├─ write to outbox queue
   └─ print receipt

2. Network returns
   ├─ sync engine POSTs outbox →  beta_billing
   │                              ├─ try INSERT invoice
   │                              ├─ ON CONFLICT (tenant_id, invoice_number)
   │                              │  → return {duplicate: true}
   │                              └─ return {ok: true}
   ├─ on 2xx / duplicate → mark outbox synced
   └─ on error → retry with backoff

3. Master data pull
   ← GET /sync?since=<seq>        server returns delta
```

**Guarantees**

- Exactly-once effect (server idempotency by natural key)
- No data loss on crash (outbox written in same local transaction as business row)
- No clock skew (server sequence number, not timestamp)

This is fully wired in **Step 4+** of the roadmap; the schema (`shared.sync_outbox`) and
route stubs already exist.

---

## 7. Prerequisites

| Tool | Version | Check |
|---|---|---|
| **Docker Desktop** | 24+ | `docker --version` |
| **Docker Compose** | 2.20+ | `docker compose version` |
| **Git** | 2.40+ | `git --version` |
| **PowerShell** | 7+ (Windows PowerShell 5.1 works) | `$PSVersionTable.PSVersion` |

Optional (only if you edit frontends locally):

- **Node.js** 20+ (`node --version`)
- **Python** 3.11+ (`python --version`)

Install via winget if missing:

```powershell
winget install Docker.DockerDesktop
winget install Git.Git
winget install OpenJS.NodeJS.LTS
winget install Python.Python.3.11
```

Reboot after Docker install; ensure Docker Desktop is **running** before deploy.

---

## 8. Local Deployment — Step by Step

### Step 0 — Confirm repo is present

```powershell
cd C:\Users\PC\betalen-ai\betalen-ferti-saas
git remote -v
# origin  https://github.com/betalen-ai/betalen-ferti-saas.git (fetch)
# origin  https://github.com/betalen-ai/betalen-ferti-saas.git (push)

Get-ChildItem -Force | Select-Object Name
# should list: frontends, postgres, services, *.ps1, docker-compose*.yml, README.md
```

### Step 1 — Create `.env`

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Get-Content .env
```

Expected keys: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL`,
`REDIS_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`.

`.env` is gitignored — never committed.

### Step 2 — Build & start the stack

```powershell
.\deploy-local.ps1
```

First run: **3–5 minutes** (pulls Python 3.11 + Node 20 + Postgres 16 base images,
pip-installs requirements in 5 containers, builds 2 frontends).

Expected tail:

```
=== Betalen Ferti SaaS - Local Deploy ===
Waiting for Postgres...
  OK  http://localhost:8000/health (200)
  OK  http://localhost:8001/health (200)
  OK  http://localhost:8002/health (200)
  OK  http://localhost:8003/health (200)
  OK  http://localhost:8004/health (200)

POS:        http://localhost:4200
Backoffice: http://localhost:3000
Gateway:    http://localhost:8000/docs
```

### Step 3 — Verify in browser

| URL | Expected |
|---|---|
| http://localhost:8000/health | `{"status":"ok","service":"api-gateway"}` |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8001/docs | Swagger UI — tenants, org_users, roles, subscriptions |
| http://localhost:8002/docs | Swagger UI — invoices, payments, credit_ledger |
| http://localhost:8003/docs | Swagger UI — products, warehouses, stock |
| http://localhost:8004/docs | Swagger UI — dashboards, exports |
| http://localhost:4200 | Angular POS shell |
| http://localhost:3000 | React backoffice shell |

### Step 4 — Inspect the database

```powershell
# Schemas
docker exec -it betalen-postgres psql -U betalen -d betalen_db -c "\dn"

# Tables per schema
docker exec -it betalen-postgres psql -U betalen -d betalen_db -c "\dt org.*"
docker exec -it betalen-postgres psql -U betalen -d betalen_db -c "\dt billing.*"
docker exec -it betalen-postgres psql -U betalen -d betalen_db -c "\dt inventory.*"
docker exec -it betalen-postgres psql -U betalen -d betalen_db -c "\dt shared.*"
```

Expected: 5 schemas; 6 org tables; 5 billing tables; 3 inventory tables; 1 shared table.

### Step 5 — Run the test suite

```powershell
.\run-tests.ps1
```

Spins up an **isolated** Postgres (tmpfs, discarded after run), runs pytest in each
backend container, tears down.

Expected tail:

```
beta_billing_tests  ... 1 passed
beta_organization_tests ... 1 passed
beta_inventory_tests ... 1 passed
ALL TESTS PASSED
```

### Step 6 — Push first commit

```powershell
git add .
git commit -m "chore(init): bootstrap monorepo

- 5 FastAPI services with /health + stub routes
- Postgres schema: org, billing, inventory, reports, shared
- Docker Compose dev + test stacks
- PowerShell deploy + test scripts
- Angular POS + React backoffice stubs"

git push -u origin main
```

If rejected (remote has auto-README):

```powershell
git pull --rebase origin main
git push -u origin main
```

### Step 7 — Stop the stack

```powershell
docker compose down
```

Keep database data (default):

```powershell
# volume pg_data survives — safe
```

Reset database entirely (destructive):

```powershell
docker compose down -v
```

---

## 9. Running Tests

**All tests, isolated DB:**

```powershell
.\run-tests.ps1
```

**One service only:**

```powershell
docker compose -f docker-compose.test.yml run --rm beta_billing_tests pytest tests/ -v
docker compose -f docker-compose.test.yml run --rm beta_organization_tests pytest tests/ -v
docker compose -f docker-compose.test.yml run --rm beta_inventory_tests pytest tests/ -v
```

**With coverage report:**

```powershell
docker compose -f docker-compose.test.yml run --rm beta_billing_tests pytest tests/ -v --cov=app --cov-report=term-missing
```

**Directly inside a running service container:**

```powershell
docker compose exec beta_billing pytest tests/ -v
```

Test DB isolation:

- Test stack uses **port 5433** (not 5432) — doesn't touch dev DB
- Postgres test data is on **tmpfs** — disappears on `down -v`
- Tests assume clean state; do not commit test data seeds

---

## 10. Common Commands

```powershell
# Start (detached)
docker compose up -d

# Rebuild one service after code change
docker compose up -d --build beta_billing

# Rebuild all with no cache (last resort)
.\deploy-local.ps1 -Rebuild

# Tail logs
docker compose logs -f beta_billing

# Shell into a container
docker compose exec beta_billing bash

# List running containers
docker compose ps

# Postgres shell
docker exec -it betalen-postgres psql -U betalen -d betalen_db

# Redis shell
docker exec -it betalen-redis redis-cli

# Stop
docker compose down

# Stop + wipe DB
docker compose down -v
```

---

## 11. Troubleshooting

### `deploy-local.ps1` reports FAIL for a service

```powershell
docker compose ps
docker compose logs <service-name> --tail 100
```

Common causes:

| Symptom | Cause | Fix |
|---|---|---|
| `connection refused` on Postgres | Postgres still starting | Re-run `.\deploy-local.ps1` (wait loop handles it) |
| `ModuleNotFoundError` | `requirements.txt` edited without rebuild | `docker compose up -d --build <service>` |
| Port already in use | Another process on 8000–8004 | `netstat -ano \| findstr :8000` → kill PID |
| Container exits immediately | Syntax error in `app/main.py` | `docker compose logs <svc>` |

### `.\deploy-local.ps1` blocked by execution policy

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\deploy-local.ps1
```

### Docker daemon not running

```
Cannot connect to the Docker daemon
```

Start **Docker Desktop** from the Start menu, wait for the whale icon to turn green,
then re-run.

### Postgres data looks empty after `docker compose down -v`

`-v` **deletes the volume** — that's intentional (full reset). Use plain
`docker compose down` to preserve data.

### `git push` rejected

```powershell
git pull --rebase origin main
git push -u origin main
```

### Port 5432 already in use (local Postgres installed)

Edit `docker-compose.yml`:

```yaml
postgres:
  ports: ["5433:5432"]   # host 5433 → container 5432
```

Then update `DATABASE_URL` in `.env` to `...@postgres:5432/...` (still internal 5432)
— the host port mapping only affects external connections (your psql client), not
inter-container traffic.

---

## 12. Roadmap

| Step | Scope | Status |
|---|---|---|
| **1** | Repo creation, naming, GitHub config | ✅ Done |
| **2** | Monorepo scaffold, Docker, Postgres schema, deploy + test scripts | ✅ Done |
| **3** | `beta_organization` domain: SQLAlchemy models, Alembic migrations, tenant creation, JWT auth in `api-gateway`, role/permission seeding | ⏳ Next |
| **4** | `beta_billing` domain: invoice creation, credit-limit check, payment recording, credit ledger | Pending |
| **5** | `beta_inventory`: products, warehouses, stock movements, batch/expiry | Pending |
| **6** | Angular POS: offline IndexedDB + outbox sync | Pending |
| **7** | React backoffice: tenant onboarding, user management, subscription | Pending |
| **8** | `beta_reports`: dashboards, GST exports, WhatsApp invoice delivery | Pending |
| **9** | CI/CD: GitHub Actions build + push + deploy | Pending |

---

## License

Proprietary — © Betalen AI. All rights reserved.
```

---

## After Saving — Verify & Push

```powershell
cd C:\Users\PC\betalen-ai\betalen-ferti-saas

# 1. Confirm the file is real (not 90 bytes)
(Get-Item .\README.md).Length           # expect 12000+
(Get-Content .\README.md | Measure-Object -Line).Lines   # expect 400+

# 2. Optional — preview on GitHub after push
git add README.md
git commit -m "docs: add complete README with architecture + deployment guide"
git push

# 3. View
gh repo view betalen-ai/betalen-ferti-saas --web
```

GitHub renders the Mermaid-free ASCII architecture diagram fine in a code block, and
the Table of Contents auto-links to each `##` heading.

---

## ✅ Done When

- [ ] `README.md` is 12000+ bytes (not the 90-byte stub)
- [ ] All 12 sections present (`Select-String -Path README.md -Pattern "^## "`)
- [ ] `git push` succeeded — README renders on GitHub with TOC
- [ ] Architecture diagram displays correctly in the code block

Paste the output of the two `Measure-Object` lines if the size looks wrong, and I'll
diagnose. Once this is on GitHub, say **"Step 3"** and I'll deliver the full
`beta_organization` implementation (SQLAlchemy models, Alembic setup, tenant-creation
endpoint, JWT login flow in `api-gateway`, and role/permission seeding).