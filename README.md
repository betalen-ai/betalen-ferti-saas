# Ferti+ (Betalen Ferti SaaS): README with Goal, Business Model, Architecture, Workflow and Local Install

Nov 21, 2026 · @Prasad

This is the updated project README. It keeps your FastAPI + PostgreSQL + Docker monorepo, adds the product goal, business model and workflows, aligns the design with the Ferti+ specifications (brands, packs, farmers, khata, seasons, spot discount and credit interest), and ends with a step-by-step local install guide. Save it as `README.md` in the repo root.

Related documents (store them in the repo under `docs/`): Corporate Website Build Specification, Shop Owner Application Functional Specification, Backend API Specification, SaaS Platform Expectations and Readiness Specification.

## 1. Goal

**Ferti+ is a free, modern business manager for fertilizer and agri-input shops.** A shop owner signs up on their own, then runs the whole shop from one place: products, brands, stock, farmers, bills, and the credit account book (khata).

**Goals**

1. Replace paper bills and paper khata with a fast, simple POS that works even with weak internet
2. Make selling on credit safe: every farmer has a clear ledger, due dates and optional interest
3. Give the owner prices that fit the season: a cash discount for spot payment (for example ₹1,000 becomes ₹950) or interest for payment later (for example 1% per month, so ₹1,000 for 6 months becomes ₹1,060)
4. Know the stock at all times, including pack sizes (5 kg, 50 kg bags, 500 ml, 5 L), batch and expiry
5. Reach hundreds of shops with self-service sign-up and almost no manual onboarding

**Not goals (for now):** farmer-facing app or login, marketplace, e-commerce, manufacturer ERP.

**Success measures:** first bill within 3 days of sign-up, weekly active shops, bills per shop per week, 90-day retention, share of credit bills with recorded payments.

## 2. Business Model

| Stage | Model |
| --- | --- |
| Launch | **Free for shop owners.** Goal is adoption, daily habit and data on how shops sell on credit |
| Soon after | Paid add-ons: SMS and WhatsApp reminder credits, extra storage and reports |
| Growth | Paid plans: multi-user staff (manager, cashier), multi-branch, advanced reports, GST and accounting integrations |
| Partnerships | Clearly labelled promotions from input brands, UPI and payment partners, and credit or finance partners (only with the owner's consent) |

**Customers:** fertilizer, pesticide, seed and small-machinery retailers in India, starting in one state.

**Value to the shop owner:** fewer errors, no lost credit records, faster billing, never running out of stock in season, better recovery of dues.

**Cost drivers to watch:** SMS and WhatsApp messages, hosting, support. Plans, usage limits and feature flags are built into the tenant model from day one so paid plans can be switched on without a rewrite.

## 3. Users and Scope

- **Shop owner** is the only user type at launch: one account, one shop (tenant)
- **Farmers are records**, not users. The owner keeps their khata
- **Staff roles** (Manager, Cashier, Stock keeper, Accountant) exist in the database design but are switched on in a later paid plan
- **Ferti+ team** uses a separate internal Operations Console (tenants, plans, support, metrics); it is not a customer login

## 4. Architecture

### 4.1 System diagram

```
+--------------------------------------------------------------------+
|                          CLIENTS (Browsers)                          |
|  +---------------------------------+   +-------------------------+ |
|  | Shop Web App (Angular)  :4200   |   | Operations Console      | |
|  | Website + Sign in/up + POS app  |   | (internal) :3000        | |
|  | PWA, offline billing            |   |                         | |
|  +----------------+----------------+   +------------+------------+ |
+-------------------|---------------------------------|--------------+
                    | HTTPS                           | HTTPS
                    v                                 v
+--------------------------------------------------------------------+
|                    API GATEWAY (FastAPI) :8000                       |
|   Auth (JWT/cookies, OTP, OAuth) | Routing | Rate limit | CORS       |
+--------+---------------+----------------+---------------+----------+
         |               |                |               |
         v               v                v               v
  +-------------+ +--------------+ +--------------+ +-------------+
  | beta_org    | | beta_billing | | beta_inventory| | beta_reports|
  | :8001       | | :8002        | | :8003         | | :8004       |
  | tenants,    | | farmers,     | | brands,       | | dashboard,  |
  | users,      | | seasons,     | | categories,   | | reports,    |
  | plans,      | | bills,       | | products,     | | exports     |
  | settings    | | payments,    | | packs, stock, |             |
  |             | | khata,       | | batches       |             |
  |             | | interest     | |               |             |
  +------+------+ +------+-------+ +-------+-------+ +------+------+
         |               |                 |                |
         +---------------+--------+--------+----------------+
                                  v
                    +-----------------------------+
                    | PostgreSQL 16 :5432         |
                    | betalen_db                  |
                    | schemas: org, billing,      |
                    | inventory, reports, shared  |
                    +-----------------------------+
                                  ^
                    +-----------------------------+
                    | Redis 7 :6379 (optional)    |
                    | cache, OTP, rate limits,    |
                    | background jobs             |
                    +-----------------------------+
```

### 4.2 Services and ports

| Service | Tech | Port | Responsibility |
| --- | --- | --- | --- |
| `shop-web-angular` | Angular (latest stable), Bootstrap 5.3, ng-bootstrap | 4200 | Public website, sign in and sign up, POS-style shop app (PWA) |
| `backoffice-react` | React 18 + Vite (internal) | 3000 | Ferti+ Operations Console. May move to Angular later for one stack |
| `api-gateway` | FastAPI | 8000 | Sign-in methods, sessions, routing, CORS, rate limits |
| `beta_organization` | FastAPI | 8001 | Tenants, owner profile, plans, settings, (later) staff and roles |
| `beta_billing` | FastAPI | 8002 | Farmers, seasons, bills, payments, khata ledger, interest and discount engine |
| `beta_inventory` | FastAPI | 8003 | Brands, categories, products, packs, stock, batch and expiry |
| `beta_reports` | FastAPI | 8004 | Dashboard numbers, reports, Excel and PDF exports |
| `postgres` | PostgreSQL 16 | 5432 | One database, one schema per service |
| `redis` | Redis 7 | 6379 | Cache, OTP storage, rate limits (optional at first) |

Every backend service exposes `GET /health`, `GET /docs` (Swagger) and `GET /openapi.json`.

### 4.3 Design principles

- **Service independence:** each service has its own Dockerfile, requirements, routes, schemas, services and tests
- **One database, schema per service:** no cross-schema joins in code; services talk over HTTP or the `shared.sync_outbox` table
- **Tenant isolation:** `tenant_id` on every business row, taken from the signed-in session, never from client input; tests prove one shop cannot read another's data
- **Server is the source of truth for money:** discount, interest, GST and totals are calculated in `beta_billing`; the app only previews
- **Idempotency:** invoices use `UNIQUE(tenant_id, invoice_number)`; offline replays use `UNIQUE(doc_type, doc_id)`; `Idempotency-Key` header on bill, payment and stock-in requests
- **Append-only khata:** ledger rows are never edited or deleted; corrections are reversing entries
- **Offline-first POS:** the Angular app caches master data, writes bills to IndexedDB and an outbox, and syncs when online

### 4.4 Database design

One database `betalen_db`, five schemas.

| Schema | Owner service | Tables |
| --- | --- | --- |
| `org` | beta\_organization | tenants, org\_users, auth\_identities (email, phone, google), roles, permissions, role\_permissions, subscriptions, settings, audit\_log |
| `inventory` | beta\_inventory | brands, categories, products, packs, warehouses, stock\_lots, stock\_movements |
| `billing` | beta\_billing | farmers (customers), seasons, bills (invoices), bill\_items, payments, payment\_allocations, khata\_entries (credit\_ledger), cashbook\_entries |
| `reports` | beta\_reports | materialized views added later |
| `shared` | all | sync\_outbox |

**Key constraints:** `org_users` unique on (tenant\_id, email); `farmers` unique on (tenant\_id, mobile); `bills` unique on (tenant\_id, invoice\_number); `packs` unique on (product\_id, size, unit); `stock_lots` unique per (pack\_id, batch\_no); `sync_outbox` unique on (doc\_type, doc\_id).

**Units and packs:** a product has a base unit (kg, litre or piece). Each pack stores `size_in_base_unit` (500 ml = 0.5 L, 50 kg bag = 50). Stock is kept in base units, so loose sales (3 kg from a 50 kg bag) work.

**Billing fields:** `payment_type` (SPOT, CREDIT, PART), `subtotal`, `discount`, `interest_rate_per_month`, `months`, `interest_amount`, `total`, `paid_now`, `balance`, `due_date`, `season_id`.

Full DDL lives in `postgres/init/01-init.sql` and runs on first Postgres start. Later changes go through Alembic migrations.

### 4.5 Money calculation rules (billing service)

- **Subtotal** = sum of quantity × unit price
- **Spot:** total = subtotal − discount (₹1,000 with ₹50 discount = ₹950)
- **Credit:** interest = credit amount × rate % per month ÷ 100 × months; total due = credit amount + interest (1% per month, 6 months on ₹1,000 = ₹60, total ₹1,060)
- **Part payment:** interest only on the credit portion
- **Months:** typed by the owner, or (due date − bill date) ÷ 30
- Discount, rate, months and due date are decided **case by case** on each bill; seasons only provide defaults
- Payments are allocated oldest bill first, interest before principal

## 5. Workflows

### 5.1 Owner onboarding

```
Visit website -> Sign up (email, phone OTP or Google) -> verify phone/email
   -> shop (tenant) created, Free plan -> setup wizard (shop name, GSTIN,
   language, tax mode) -> starter catalogue -> import products, stock,
   farmer dues from Excel -> first bill
```

### 5.2 Daily sale

```
New Sale -> pick farmer (or walk-in) -> add products (scan or tap tiles)
   -> choose payment type
        SPOT   -> enter discount -> pay Cash / UPI -> total = subtotal - discount
        CREDIT -> set interest rate, months or due date -> total due shown
        PART   -> enter paid now, rest goes to khata with interest
   -> Complete Sale -> stock reduced, khata entry created -> print / WhatsApp bill
```

### 5.3 Receiving a payment

```
Farmers -> Receive Payment -> amount, mode, date
   -> allocated to oldest unpaid bill (interest first) -> khata balance updated
   -> receipt shared
```

### 5.4 Stock in

```
Purchase arrives -> Stock In -> product, pack, qty, cost, batch, expiry
   -> stock increased -> low-stock and expiry alerts update
```

### 5.5 Season setup

```
Seasons -> create "Kharif 2026" -> dates, default cash discount,
   default interest per month, due date, grace days
   -> new bills suggest these values; owner can still change them
```

### 5.6 Offline billing and sync

```
Offline:  bill saved in IndexedDB + outbox (same local transaction) -> receipt printed
Online:   sync engine sends outbox to billing service with Idempotency-Key
            - new      -> saved, returns ok
            - duplicate -> returns duplicate: true, marked synced
            - error     -> retry with backoff
          then pulls changes: GET /sync?since=<server sequence>
```

Guarantees: exactly-once effect, no data loss on crash, ordering by server sequence rather than device clock.

### 5.7 Cancel and corrections

Cancelling a bill needs a reason; stock is restored and reversing khata entries are added. Nothing is deleted.

### 5.8 Support (Ferti+ team)

Operations Console: find the shop, view with the owner's consent and a time limit, change plan or flags, answer data requests. Every action is audited.

## 6. Repository Structure

```
betalen-ferti-saas/
  README.md
  .env.example
  docker-compose.yml          # dev stack
  docker-compose.test.yml     # isolated test stack
  deploy-local.ps1            # one-command local deploy
  run-tests.ps1               # one-command tests
  docs/                       # the five specification documents + openapi.yaml
  postgres/init/01-init.sql   # schemas and tables
  services/
    api-gateway/  beta_organization/  beta_billing/  beta_inventory/  beta_reports/
      app/ (main.py, config.py, db.py, routes/, schemas/, services/, validations/, integrations/, models/)
      tests/  Dockerfile  requirements.txt  README.md
  frontends/
    shop-web-angular/         # website + auth + POS app
    backoffice-react/         # internal operations console
```

The earlier folder name `shop-pos-angular` becomes `shop-web-angular` because one Angular project holds the public website (`/`, `/pricing`, `/signin`) and the logged-in app (`/app/*`).

## 7. Install on Your Local Machine (Windows, Step by Step)

These steps assume the monorepo scaffold already exists at `C:\Users\PC\betalen-ai\betalen-ferti-saas` with the scripts named in section 6. If a file is missing, ask Copilot to generate it from this README.

### Step 1: Install the tools

| Tool | Version | Check |
| --- | --- | --- |
| Docker Desktop | 24+ | `docker --version` |
| Docker Compose | 2.20+ | `docker compose version` |
| Git | 2.40+ | `git --version` |
| PowerShell | 7+ (5.1 also works) | `$PSVersionTable.PSVersion` |
| Node.js (only to edit frontends) | 20+ | `node --version` |
| Python (only to run services outside Docker) | 3.11+ | `python --version` |

```powershell
winget install Docker.DockerDesktop
winget install Git.Git
winget install OpenJS.NodeJS.LTS
winget install Python.Python.3.11
```

Restart the PC after installing Docker, then open Docker Desktop and wait until it says it is running.

### Step 2: Get the code

```powershell
cd C:\Users\PC\betalen-ai\betalen-ferti-saas
git remote -v
git pull --rebase origin main
```

For a fresh machine use `git clone https://github.com/betalen-ai/betalen-ferti-saas.git` and `cd betalen-ferti-saas`.

### Step 3: Create the environment file

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Set these keys (change the passwords and secret, never commit `.env`):

| Key | Meaning |
| --- | --- |
| POSTGRES\_USER, POSTGRES\_PASSWORD, POSTGRES\_DB | Database login and name (`betalen_db`) |
| DATABASE\_URL | Connection string used by the services |
| REDIS\_URL | Redis address |
| JWT\_SECRET, JWT\_ALGORITHM, JWT\_EXPIRE\_MINUTES | Session signing |
| GOOGLE\_CLIENT\_ID, GOOGLE\_CLIENT\_SECRET | Google sign-in (leave blank to skip in development) |
| SMS\_PROVIDER, SMS\_API\_KEY | OTP SMS (use `console` in development to print OTPs in the logs) |

### Step 4: Build and start everything

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\deploy-local.ps1
```

The first run takes 3 to 5 minutes while Docker downloads images and installs packages. At the end you should see `OK` for ports 8000 to 8004 and the addresses of the apps.

Without the script:

```powershell
docker compose up -d --build
docker compose ps
```

### Step 5: Check that it works

| Open in the browser | Expected |
| --- | --- |
| http://localhost:8000/health | `{"status":"ok","service":"api-gateway"}` |
| http://localhost:8000/docs | Gateway Swagger UI |
| http://localhost:8001/docs | Organization service |
| http://localhost:8002/docs | Billing service |
| http://localhost:8003/docs | Inventory service |
| http://localhost:8004/docs | Reports service |
| http://localhost:4200 | Ferti+ website and shop app |
| http://localhost:3000 | Operations Console |

### Step 6: Look inside the database

```powershell
docker exec -it betalen-postgres psql -U betalen -d betalen_db -c "\dn"
docker exec -it betalen-postgres psql -U betalen -d betalen_db -c "\dt billing.*"
docker exec -it betalen-postgres psql -U betalen -d betalen_db -c "\dt inventory.*"
```

You should see the five schemas (org, billing, inventory, reports, shared) and their tables.

### Step 7: Try the main flow

1. Open http://localhost:4200 and choose **Sign up free**
2. Register with email and password (or phone OTP; in development the OTP is printed in `docker compose logs api-gateway`)
3. Add a brand, then a product with two packs (for example DAP 5 kg and 50 kg)
4. Add stock, add a farmer, then make one spot bill and one credit bill with interest
5. Open the farmer's khata and receive a payment

Expected numbers: a ₹1,000 spot bill with ₹50 discount totals ₹950; a ₹1,000 credit bill at 1% per month for 6 months totals ₹1,060.

### Step 8: Run the tests

```powershell
.\run-tests.ps1
docker compose -f docker-compose.test.yml run --rm beta_billing_tests pytest tests/ -v
```

The test stack uses its own temporary database on port 5433 and does not touch your development data. Billing formulas (spot discount, credit interest, part payment, payment allocation) must have unit tests.

### Step 9: Work on a frontend with live reload (optional)

```powershell
cd frontends\shop-web-angular
npm install
npm start        # http://localhost:4200, proxies /api to http://localhost:8000
```

Stop the Docker copy of the same app first (`docker compose stop shop-web-angular`) to free port 4200. For the console use `cd frontends\backoffice-react`, `npm install`, `npm run dev`.

### Step 10: Stop and reset

```powershell
docker compose down        # keeps database data
docker compose down -v     # DELETES the database volume
```

### Step 11: Save your work to GitHub

```powershell
git add .
git commit -m "docs: updated README with goal, business model, architecture and workflows"
git push -u origin main
```

If the push is rejected: `git pull --rebase origin main` then push again.

## 8. Common Commands

```powershell
docker compose up -d                        # start
docker compose up -d --build beta_billing   # rebuild one service
.\deploy-local.ps1 -Rebuild                 # rebuild everything
docker compose logs -f beta_billing         # live logs
docker compose exec beta_billing bash       # shell in a service
docker compose ps                           # running containers
docker exec -it betalen-postgres psql -U betalen -d betalen_db
docker exec -it betalen-redis redis-cli
```

## 9. Troubleshooting

| Problem | Cause | Fix |
| --- | --- | --- |
| Cannot connect to the Docker daemon | Docker Desktop not running | Start Docker Desktop, wait until it is ready, retry |
| Script blocked by execution policy | PowerShell policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| Service shows FAIL | Postgres still starting or code error | `docker compose logs <service> --tail 100`, then re-run the script |
| `ModuleNotFoundError` | requirements changed without rebuild | `docker compose up -d --build <service>` |
| Port already in use (8000 to 8004, 4200, 3000) | Another program uses it | `netstat -ano \| findstr :8000`, stop that process or change the port |
| Port 5432 in use | Local PostgreSQL installed | In `docker-compose.yml` map `"5433:5432"`; keep `DATABASE_URL` pointing to `postgres:5432` inside Docker |
| Database empty after restart | Used `down -v` | Use plain `docker compose down` to keep data |
| OTP not arriving | SMS not configured | Set `SMS_PROVIDER=console` and read the OTP in the gateway logs |

## 10. Roadmap

| Step | Scope | Status |
| --- | --- | --- |
| 1 | Repository, naming, GitHub setup | Done |
| 2 | Monorepo scaffold, Docker, Postgres schemas, deploy and test scripts | Done |
| 3 | `beta_organization`: models, Alembic, tenant creation, auth in gateway (email, phone OTP, Google, reset link), settings | Next |
| 4 | `beta_inventory`: brands, categories, products, packs, stock in and out, batch and expiry | Pending |
| 5 | `beta_billing`: farmers, seasons, bill preview and save with spot discount and credit interest, payments, khata | Pending |
| 6 | Angular app: website, sign in and sign up, POS shell, products, stock, farmers, billing, khata | Pending |
| 7 | Offline billing with IndexedDB, outbox and sync | Pending |
| 8 | `beta_reports`: dashboard, reports, Excel and PDF, WhatsApp share | Pending |
| 9 | Operations Console, plan limits and feature flags | Pending |
| 10 | CI/CD with GitHub Actions, backups, monitoring, security review, pilot launch | Pending |

Before public launch, complete the Must items in the SaaS Platform Expectations specification (security review, backups, DPDP privacy notice and consent, legal pages, SMS template registration).

## 11. License

Proprietary, © Betalen AI. All rights reserved.
