# Betalen Ferti SaaS --- Developer Cheat Sheet

A practical reference for starting the monorepo, managing database
migrations, running tests, developing the Angular frontend, debugging
services, and using Git.

> **Purpose:** Keep common development commands and workflows in one
> place so you can work consistently without guessing which terminal or
> directory to use.

------------------------------------------------------------------------

## Table of Contents

1.  [Golden Rule](#1-golden-rule)
2.  [Start and Stop the System](#2-start-and-stop-the-system)
3.  [Database Changes and Alembic
    Migrations](#3-database-changes-and-alembic-migrations)
4.  [Run Tests](#4-run-tests)
5.  [Angular Frontend Development](#5-angular-frontend-development)
6.  [Debugging and Useful Commands](#6-debugging-and-useful-commands)
7.  [Git Workflow](#7-git-workflow)
8.  [Typical Development Workflow](#8-typical-development-workflow)
9.  [Important Notes](#9-important-notes)

------------------------------------------------------------------------

## 1. Golden Rule

**Run commands from the monorepo root unless a step explicitly tells you
to change directories.**

``` powershell
C:\Users\PC\betalen-ai\betalen-ferti-saas
```

Open this folder in VS Code and use its integrated terminal. The
commands below assume:

-   Docker Desktop is running.
-   You are in the repository root unless otherwise stated.
-   The Docker Compose service and container names match your local
    configuration.

If a service name or path differs in your checkout, confirm it in
`docker-compose.yml` before running the command.

------------------------------------------------------------------------

## 2. Start and Stop the System

### Start all services

``` powershell
docker compose up -d
```

### Check service status

``` powershell
docker compose ps
```

### Stop services

``` powershell
docker compose down
```

This stops and removes the Compose containers and network. **It normally
preserves database data stored in named volumes.** Do not use
`docker compose down -v` unless you intentionally want to remove the
volumes and their data.

### Rebuild and restart one service

For example, rebuild the `beta_billing` service after changing its image
or dependencies:

``` powershell
docker compose up -d --build beta_billing
```

For code changes, whether a rebuild is needed depends on how the service
is configured (for example, bind mounts versus code copied into the
image).

### Follow logs for one service

``` powershell
docker compose logs -f beta_billing
```

Press **Ctrl+C** to stop following the logs. This does not stop the
container.

------------------------------------------------------------------------

## 3. Database Changes and Alembic Migrations

Use this workflow whenever you add or change a SQLAlchemy model, table,
column, index, or constraint.

### Step A --- Create or update the SQLAlchemy model

Add or update the model in:

``` text
services/beta_billing/app/models/
```

For example:

``` text
services/beta_billing/app/models/invoice.py
```

Make sure the model is imported or otherwise registered through:

``` text
services/beta_billing/app/models/__init__.py
```

Alembic must be able to load the model metadata before it can detect
schema changes.

### Step B --- Generate a migration

From the monorepo root, run:

``` powershell
docker compose exec beta_billing alembic revision --autogenerate -m "add invoice table"
```

This asks Alembic to compare the loaded SQLAlchemy metadata with the
current database schema and generate a migration.

> Autogenerate is a starting point, not a guarantee. It may miss or
> misinterpret some changes. Always review the generated migration.

### Step C --- Review the generated migration

Find the new file under:

``` text
services/beta_billing/alembic/versions/
```

Open it in VS Code and review both:

-   `upgrade()` --- applies the schema change.
-   `downgrade()` --- reverses the schema change where possible.

Check table names, schema names, column types, nullability, defaults,
indexes, foreign keys, and constraints.

**If you are creating a new PostgreSQL schema**, make sure the schema is
created before objects inside it. For example, add an operation near the
beginning of `upgrade()`:

``` python
op.execute("CREATE SCHEMA IF NOT EXISTS billing")
```

Replace `billing` with the actual schema name. Also consider whether the
downgrade should drop the schema; only do so if it is safe and the
schema contains no other objects that must be retained.

### Step D --- Apply the migration

``` powershell
docker compose exec beta_billing alembic upgrade head
```

This applies migrations up to the latest revision known to that Alembic
environment.

### Step E --- Verify the database change

To list tables in the `billing` schema:

``` powershell
docker exec -it betalen-postgres psql -U betalen -d betalen_db -c "\dt billing.*"
```

To open an interactive PostgreSQL shell:

``` powershell
docker exec -it betalen-postgres psql -U betalen -d betalen_db
```

Useful commands inside `psql`:

``` sql
\dn              -- List schemas
\dt billing.*    -- List tables in the billing schema
\d billing.invoices -- Describe a table (adjust the table name)
\q               -- Exit psql
```

### Useful Alembic commands

Show the current database revision:

``` powershell
docker compose exec beta_billing alembic current
```

Show migration history:

``` powershell
docker compose exec beta_billing alembic history
```

Show the latest revision:

``` powershell
docker compose exec beta_billing alembic heads
```

------------------------------------------------------------------------

## 4. Run Tests

Run the billing service tests using the test Compose configuration:

``` powershell
docker compose -f docker-compose.test.yml run --rm beta_billing_tests pytest tests/ -v
```

This runs the test service and removes its one-off container when the
command finishes.

**Important:** Confirm that `docker-compose.test.yml` points to a
dedicated test database and does not use your development or production
database. Tests that write data should never run against a real
production database.

------------------------------------------------------------------------

## 5. Angular Frontend Development

For day-to-day UI development, run Angular locally for faster rebuilds
and automatic reloads.

### Start the local Angular development server

``` powershell
cd frontends/shop-pos-angular
npm install
npm start
```

Open:

``` text
http://localhost:4200
```

Keep this terminal open while developing. Stop the local server with
**Ctrl+C**.

### Build and run the Docker frontend

Return to the monorepo root:

``` powershell
cd ..\..
docker compose build --no-cache shop-pos-angular
docker compose up -d shop-pos-angular
```

Use `--no-cache` only when you need a clean image build; it can make
builds take longer.

------------------------------------------------------------------------

## 6. Debugging and Useful Commands

### List running containers and services

``` powershell
docker compose ps
```

### View logs for a service

``` powershell
docker compose logs -f beta_billing
```

### Open a shell inside a running service container

``` powershell
docker compose exec beta_billing bash
```

If the image does not include Bash, try:

``` powershell
docker compose exec beta_billing sh
```

### Check whether port 4200 is in use

``` powershell
netstat -ano | findstr :4200
```

The last column is the process ID (PID). Identify the process before
stopping it:

``` powershell
Get-Process -Id <PID_NUMBER>
```

If you are certain it is the process you want to stop:

``` powershell
Stop-Process -Id <PID_NUMBER> -Force
```

### Stop specific processes

Use the PID values you have verified on your machine. For example:

``` powershell
Stop-Process -Id 6548 -Force
Stop-Process -Id 9512 -Force
```

PIDs can change after a restart, so do not reuse old values without
checking them first.

------------------------------------------------------------------------

## 7. Git Workflow

Before committing, check which files have changed:

``` powershell
git status
```

Review the changes:

``` powershell
git diff
```

Stage and commit your work:

``` powershell
git add .
git commit -m "feat: describe the change"
```

Push the current branch:

``` powershell
git push
```

If this is a new branch and it has no upstream configured:

``` powershell
git push -u origin <branch-name>
```

**Good practice:** Work on a feature branch rather than committing
directly to `main`, unless your team's workflow explicitly requires
otherwise.

Example:

``` powershell
git switch -c feature/billing-invoices
```

------------------------------------------------------------------------

## 8. Typical Development Workflow

For a normal backend feature that requires a database change:

1.  Start the required Docker services:

    ``` powershell
    docker compose up -d
    ```

2.  Update or create the SQLAlchemy model.

3.  Register the model so Alembic can load its metadata.

4.  Generate the migration:

    ``` powershell
    docker compose exec beta_billing alembic revision --autogenerate -m "describe the change"
    ```

5.  Review and, if necessary, correct the generated migration.

6.  Apply the migration:

    ``` powershell
    docker compose exec beta_billing alembic upgrade head
    ```

7.  Run the relevant tests.

8.  Check service logs and verify the API/database behavior.

9.  Review your Git changes, commit, and push your feature branch.

For frontend-only work, start the Angular development server locally and
use the browser at `http://localhost:4200`.

------------------------------------------------------------------------

## 9. Important Notes

-   **Never run destructive database commands casually.** Confirm the
    target database before dropping schemas, tables, or volumes.
-   **Do not commit secrets.** Keep passwords, API keys, tokens, and
    connection strings in environment variables or approved local secret
    files.
-   **Review every autogenerated migration.** Confirm that it matches
    the intended database change.
-   **Use the test database for automated tests.** Verify the test
    configuration before running tests.
-   **Check service names before running Compose commands.** Use
    `docker compose config --services` to list configured service names.
-   **Check container names before using `docker exec`.** Use
    `docker ps` if a container name such as `betalen-postgres` is not
    found.
-   **Keep Git changes focused.** Avoid committing generated files,
    local configuration, or secrets unless the repository explicitly
    requires them.

### Quick reference

  ------------------------------------------------------------------------------------------------------------------------------
  Task                                Command
  ----------------------------------- ------------------------------------------------------------------------------------------
  Start all services                  `docker compose up -d`

  Stop all services                   `docker compose down`

  Check services                      `docker compose ps`

  Follow billing logs                 `docker compose logs -f beta_billing`

  Generate migration                  `docker compose exec beta_billing alembic revision --autogenerate -m "message"`

  Apply migrations                    `docker compose exec beta_billing alembic upgrade head`

  Check Alembic revision              `docker compose exec beta_billing alembic current`

  Run billing tests                   `docker compose -f docker-compose.test.yml run --rm beta_billing_tests pytest tests/ -v`

  Start Angular                       `cd frontends/shop-pos-angular` then `npm start`

  Check Git status                    `git status`
  ------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

**You now have a repeatable workflow for backend changes, migrations,
tests, frontend development, and Git. Keep this file in the repository
(for example, as `DEVELOPER_CHEAT_SHEET.md`) so it stays close to the
codebase and can be updated as the project evolves.**
