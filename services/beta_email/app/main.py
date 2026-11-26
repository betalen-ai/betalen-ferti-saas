from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.config import settings
from app.db import engine, ensure_schema
from app.models.models import Base
from app.providers.console import ConsoleProvider
from app.providers.gmail_smtp import GmailSmtpProvider, SmtpProvider
from app.routes import emails, templates, health
from app.services.worker import EmailWorker


worker: EmailWorker | None = None


def make_provider():
    if settings.EMAIL_PROVIDER == "gmail_smtp":
        return GmailSmtpProvider()
    if settings.EMAIL_PROVIDER == "mailpit":
        provider = SmtpProvider(settings.MAILPIT_HOST, settings.MAILPIT_PORT)
        provider.name = "mailpit"
        return provider
    return ConsoleProvider()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker
    if settings.ENV == "production":
        missing = [
            name for name, value in (
                ("GMAIL_USER", settings.GMAIL_USER),
                ("GMAIL_APP_PASSWORD", settings.GMAIL_APP_PASSWORD),
                ("ENCRYPTION_KEY", settings.ENCRYPTION_KEY),
            ) if not value
        ]
        if missing:
            raise RuntimeError("Missing production settings: " + ", ".join(missing))
    await ensure_schema()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    worker = EmailWorker(make_provider())
    await worker.start()
    yield
    await worker.stop()
    await engine.dispose()


app = FastAPI(title="beta_email", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(emails.router, prefix="/v1", tags=["emails"])
app.include_router(templates.router, prefix="/v1", tags=["templates"])
