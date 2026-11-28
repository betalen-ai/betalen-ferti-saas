# 🚀 Betalen Ferti SaaS - Developer Cheat Sheet (V3)

Here is the fully updated and corrected cheat sheet for your exact project setup. 

Save this file on your desktop as `betalen-cheatsheet.md` (or `.txt`).

---

# 🚀 Betalen Ferti SaaS - Ultimate Developer Cheat Sheet

## 📌 The Golden Rules
1. **Always run commands from the root of the monorepo**: `C:\Users\PC\betalen-ai\betalen-ferti-saas` unless explicitly told to `cd` into a folder.
2. **Docker is for production / final testing**. For daily UI coding in Angular or React, run them locally (`npm start`) so you get instant hot-reloading.
3. **Never commit `.env` files** or `node_modules` to Git.

---

## 1. Fixing "Port is already in use" (Very Common)

If you get an error that a port (like 4200, 3000, 8000) is in use, a previous `npm start` or a crashed Docker container is holding onto it.

### A. The "Nuclear" Port Killer (Windows PowerShell)
Run this to instantly kill anything blocking the standard dev ports (4200, 3000, 8000, 8001, 8002, 8003, 8004).

```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 4200, 3000, 8000, 8001, 8002, 8003, 8004 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force
```

### B. Manual Port Killing (If you only want to kill one)
```powershell
# 1. Find the Process ID (PID)
netstat -ano | findstr :4200

# 2. Kill it (replace 12345 with the PID from the last column)
Stop-Process -Id 12345 -Force
```

---

## 2. Starting & Stopping the System

**Start everything (Backends + Frontends):**
```powershell
docker compose up -d
```

**Stop everything (Keeps database data safe):**
```powershell
docker compose down
```

**Rebuild and restart a specific backend (after changing Python code):**
```powershell
docker compose up -d --build beta_billing
```

**View live logs for a specific service (to debug errors):**
```powershell
docker compose logs -f beta_billing
```
*(Press `Ctrl+C` to stop viewing logs).*

---

## 3. Database Changes (Alembic Workflow)

Whenever you need to add a new table or change a column:

### Step A: Modify the SQLAlchemy Model
Add or edit the file in `services/beta_billing/app/models/`. Make sure to import it in `services/beta_billing/app/models/__init__.py` so Alembic can see it.

### Step B: Generate the Migration File
Tell Alembic to look at your models and generate the SQL code.
```powershell
docker compose exec beta_billing alembic revision --autogenerate -m "describe your change"
```

### Step C: Check the Generated File
Look inside `services/beta_billing/alembic/versions/`. Open the new `.py` file.
- Verify the `def upgrade():` block looks correct.
- **CRITICAL**: If you are creating a new schema (like `org` or `billing`), ensure `op.execute("CREATE SCHEMA IF NOT EXISTS <schema_name>")` is the first line in `upgrade()`.

### Step D: Apply to the Database
```powershell
docker compose exec beta_billing alembic upgrade head
```

### Step E: Verify it worked
```powershell
docker exec -it betalen-postgres psql -U betalen -d betalen_db -c "\dt billing.*"
```

---

## 4. Running Tests

To run the test suite for a specific service against an isolated test database (won't mess up your dev data):
```powershell
docker compose -f docker-compose.test.yml run --rm beta_billing_tests pytest tests/ -v
```

---

## 5. Frontend Development

### A. Angular POS (`shop-pos-angular`)
**Local Dev (Fast, auto-reloads on save):**
```powershell
cd frontends/shop-pos-angular
npm start
```
*(Open `http://localhost:4200`)*

**Build & Serve in Docker (Production):**
```powershell
cd ../..
docker compose build --no-cache shop-pos-angular
docker compose up -d --force-recreate shop-pos-angular
```

### B. React Backoffice (`backoffice-react`)
**Local Dev:**
```powershell
cd frontends/backoffice-react
npm start
```

**Build & Serve in Docker:**
```powershell
cd ../..
docker compose build --no-cache backoffice-react
docker compose up -d --force-recreate backoffice-react
```

---

## 6. Useful Debugging Commands

**Check if all containers are running and healthy:**
```powershell
docker compose ps
```

**Open a bash terminal inside a running container:**
```powershell
docker compose exec beta_billing bash
```

**Open the PostgreSQL database shell:**
```powershell
docker exec -it betalen-postgres psql -U betalen -d betalen_db
```
*(Type `\q` to exit).*

**Check if a backend API is responding (without the frontend):**
```powershell
Invoke-WebRequest http://localhost:8000/health -UseBasicParsing | Select-Object -ExpandProperty Content
```

---

## 7. Git Workflow (Saving to GitHub)

**Save and push your work:**
```powershell
git add .
git commit -m "feat: describe exactly what you built"
git push origin main
```

**If you accidentally committed a huge `node_modules` folder or `.env` file:**
```powershell
git rm -r --cached node_modules
git rm --cached .env
git commit -m "chore: remove node_modules and .env from tracking"
```

---

## 8. 🚨 "Help, I broke everything" (The Hard Reset)

If the database is completely messed up, migrations are failing, and you just want to start from scratch with a clean slate:

```powershell
# 1. Stop everything AND delete the database volume (WIPES ALL DATA)
docker compose down -v

# 2. Start just the database and let it initialize
docker compose up -d postgres
Start-Sleep -Seconds 5

# 3. Rebuild and start everything else
docker compose up -d --build
```

---

## 9. Current Project Architecture Reference

- **PostgreSQL**: Port `5432` (Database: `betalen_db`)
- **Redis**: Port `6379`
- **API Gateway**: Port `8000` (Handles Auth & Routing)
- **beta_organization**: Port `8001` (Tenants, Users, Roles)
- **beta_billing**: Port `8002` (Invoices, Payments, Credit)
- **beta_inventory**: Port `8003` (Products, Warehouses, Stock)
- **beta_reports**: Port `8004` (Dashboards)
- **Angular POS**: Port `4200`
- **React Backoffice**: Port `3000`

### Key Test Credentials (Local Dev)
- **Subdomain:** `greenvalley`
- **Email:** `owner@greenvalley.com`
- **Password:** `SuperSecret123`

---

💡 **How to use this cheat sheet going forward:**
1. **To add a feature:** Look at **Section 3** to update the database, then write your Python/TS code.
2. **To test backend changes:** Look at **Section 2** to restart that specific container.
3. **To test UI changes:** Look at **Section 5** and run the local `npm start`.
4. **If something crashes:** Look at **Section 1** for port issues, or **Section 6** for logs.

Save this, and you're fully equipped! Let me know when you're ready to write the `beta_billing` models (Invoice, Payment).