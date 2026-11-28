import asyncio
import json
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from app.config import settings
from app.db import SessionLocal
from app.models.models import EmailMessage, EmailAttempt, EmailSuppression
from app.providers.base import ProviderResult
from app.providers.console import ConsoleProvider
from app.providers.gmail_smtp import SmtpProvider
from app.security import decrypt_payload
from app.services.renderer import Renderer


BACKOFF = (timedelta(minutes=1), timedelta(minutes=5), timedelta(minutes=15),
           timedelta(hours=1), timedelta(hours=6))


def mask_email(email: str) -> str:
    local, sep, domain = email.partition("@")
    if not sep:
        return "***"
    return f"{local[:2]}***@{domain}"


def sanitize_error(error: str | None) -> str:
    if not error:
        return ""
    text = re.sub(r"https?://[^\\s]+", "[link]", error)
    if settings.GMAIL_APP_PASSWORD:
        text = text.replace(settings.GMAIL_APP_PASSWORD, "***")
    return text[:500]


class EmailWorker:
    def __init__(self, provider):
        self.provider = provider
        self.renderer = Renderer()
        self.running = False
        self.task = None

    async def start(self):
        self.running = True
        self.task = asyncio.create_task(self.loop())

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def recover_stuck(self, session):
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        await session.execute(
            update(EmailMessage)
            .where(EmailMessage.status == "SENDING", EmailMessage.next_attempt_at < cutoff)
            .values(status="QUEUED", next_attempt_at=datetime.now(timezone.utc))
        )
        await session.commit()

    async def loop(self):
        while self.running:
            try:
                async with SessionLocal() as session:
                    await self.recover_stuck(session)
                    await self.process_batch(session)
            except Exception as exc:
                print(f"[beta_email] worker error: {sanitize_error(type(exc).__name__)}")
            await asyncio.sleep(settings.WORKER_POLL_SECONDS)

    async def process_batch(self, session):
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(EmailMessage)
            .where(
                EmailMessage.status.in_(("QUEUED", "FAILED")),
                EmailMessage.next_attempt_at <= now,
                EmailMessage.payload_encrypted.is_not(None),
            )
            .order_by(EmailMessage.priority.desc(), EmailMessage.created_at.asc())
            .limit(settings.WORKER_BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        messages = result.scalars().all()
        for message in messages:
            await self.process_one(session, message)

    async def process_one(self, session, message: EmailMessage):
        if message.expires_at:
            expiry = message.expires_at
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if expiry <= datetime.now(timezone.utc):
                message.status = "EXPIRED"
                message.payload_encrypted = None
                await session.commit()
                return

        message.status = "SENDING"
        message.attempts += 1
        started = datetime.now(timezone.utc)
        await session.commit()
        attempt = EmailAttempt(
            id=__import__("uuid").uuid4(),
            message_id=message.id,
            attempt_no=message.attempts,
            started_at=started,
            result="TEMP_FAIL",
        )
        try:
            payload = json.loads(decrypt_payload(message.payload_encrypted))
            subject, html, text = self.renderer.render(
                payload["template"], payload["locale"], payload["data"], payload["to"].get("name")
            )
            mime = self.renderer.build_mime(
                settings.MAIL_FROM_NAME,
                settings.MAIL_FROM_ADDRESS,
                settings.MAIL_REPLY_TO,
                payload["to"]["email"],
                payload["to"].get("name"),
                subject,
                html,
                text,
            )
            result: ProviderResult = await self.provider.send(mime)
            finished = datetime.now(timezone.utc)
            attempt.finished_at = finished
            attempt.duration_ms = int((finished - started).total_seconds() * 1000)
            attempt.smtp_code = result.smtp_code
            if result.ok:
                message.status = "SENT"
                message.sent_at = finished
                message.provider = self.provider.name
                message.provider_message_id = result.provider_message_id
                message.payload_encrypted = None
                message.last_error = None
                attempt.result = "OK"
            elif result.temporary:
                attempt.result = "TEMP_FAIL"
                attempt.error_text = sanitize_error(result.error)
                message.last_error = sanitize_error(result.error)
                if message.attempts >= settings.MAX_ATTEMPTS:
                    message.status = "DEAD"
                else:
                    message.status = "QUEUED"
                    message.next_attempt_at = finished + BACKOFF[min(message.attempts - 1, len(BACKOFF) - 1)]
            else:
                attempt.result = "PERM_FAIL"
                attempt.error_text = sanitize_error(result.error)
                message.status = "FAILED"
                message.last_error = sanitize_error(result.error)
                if result.smtp_code and 500 <= result.smtp_code < 600:
                    session.add(EmailSuppression(
                        email=message.to_email,
                        reason="HARD_BOUNCE",
                        created_at=finished,
                        created_by="worker",
                    ))
        except Exception as exc:
            attempt.result = "TEMP_FAIL"
            attempt.error_text = sanitize_error(type(exc).__name__)
            message.last_error = sanitize_error(type(exc).__name__)
            message.status = "DEAD" if message.attempts >= settings.MAX_ATTEMPTS else "QUEUED"
            if message.status == "QUEUED":
                message.next_attempt_at = datetime.now(timezone.utc) + BACKOFF[min(message.attempts - 1, len(BACKOFF) - 1)]
        session.add(attempt)
        await session.commit()
