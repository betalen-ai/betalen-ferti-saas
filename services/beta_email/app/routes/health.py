from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.db import engine

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "beta_email"}


@router.get("/ready")
async def ready():
    provider_valid = settings.EMAIL_PROVIDER in ("console", "mailpit", "gmail_smtp")
    if settings.EMAIL_PROVIDER == "gmail_smtp":
        provider_valid = bool(settings.GMAIL_USER and settings.GMAIL_APP_PASSWORD)
    if settings.ENV == "production":
        provider_valid = provider_valid and bool(settings.ENCRYPTION_KEY)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        database_ok = True
    except Exception:
        database_ok = False
    return {
        "status": "ready" if database_ok and provider_valid else "not_ready",
        "database": "ok" if database_ok else "unavailable",
        "provider": "ok" if provider_valid else "invalid",
    }
