<#
.SYNOPSIS  Scaffold ONLY the Alembic structure for a service.
           Migrations are generated later via `alembic revision --autogenerate`.
.USAGE     cd C:\Users\PC\betalen-ai\betalen-ferti-saas
           .\setup-migrations.ps1 -Service beta_organization
#>
param([string]$Service = "beta_organization")

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$svcDir   = Join-Path $repoRoot "services\$Service"

if (-not (Test-Path $svcDir)) {
    Write-Error "Service folder not found: $svcDir"
    exit 1
}

Write-Host "=== Scaffolding Alembic for $Service ===" -ForegroundColor Cyan
Write-Host "Repo root : $repoRoot"
Write-Host "Service   : $svcDir"

function New-File {
    param(
        [Parameter(Mandatory)][string]$RelPath,
        [Parameter(Mandatory)][string]$Content
    )
    $full = Join-Path $svcDir $RelPath
    $dir  = Split-Path -Parent $full
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    [System.IO.File]::WriteAllText($full, $Content, [System.Text.UTF8Encoding]::new($false))
    Write-Host "  + $full"
}

# ---------- alembic.ini ----------
New-File "alembic.ini" @"
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"@

# ---------- alembic/env.py ----------
New-File "alembic\env.py" @"
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.models.base import Base
import app.models  # noqa: F401 -- import all models so metadata is populated

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        version_table_schema="public",
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        version_table_schema="public",
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
"@

# ---------- alembic/script.py.mako ----------
New-File "alembic\script.py.mako" @'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'@

# ---------- empty versions/ folder ----------
$versionsDir = Join-Path $svcDir "alembic\versions"
if (-not (Test-Path $versionsDir)) {
    New-Item -ItemType Directory -Force -Path $versionsDir | Out-Null
}
# .gitkeep so git tracks the empty folder
New-File "alembic\versions\.gitkeep" ""

Write-Host ""
Write-Host "Done. Now generate the first migration from models:" -ForegroundColor Green
Write-Host "  docker compose exec $Service alembic revision --autogenerate -m `"initial tables`"" -ForegroundColor Cyan
Write-Host "  docker compose exec $Service alembic upgrade head" -ForegroundColor Cyan