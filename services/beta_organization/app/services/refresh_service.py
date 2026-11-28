import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.refresh_session import RefreshSession

REFRESH_DAYS = getattr(settings, "REFRESH_EXPIRE_DAYS", 30)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def issue_refresh_token(db: AsyncSession, *, user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    raw = secrets.token_urlsafe(48)
    db.add(RefreshSession(
        tenant_id=tenant_id,
        user_id=user_id,
        token_hash=_hash(raw),
        expires_at=_now() + timedelta(days=REFRESH_DAYS),
    ))
    await db.commit()
    return raw


async def rotate_refresh_token(db: AsyncSession, raw: str) -> tuple[RefreshSession, str] | None:
    """Validate, revoke the old token and issue a new one.
    Returns (old_session, new_raw_token) or None if invalid."""
    session = (await db.execute(
        select(RefreshSession).where(RefreshSession.token_hash == _hash(raw))
    )).scalar_one_or_none()

    if not session or session.expires_at <= _now():
        return None

    if session.revoked_at is not None:
        # Reuse of a revoked token: assume theft, revoke all sessions of this user.
        await db.execute(
            update(RefreshSession)
            .where(RefreshSession.user_id == session.user_id, RefreshSession.revoked_at.is_(None))
            .values(revoked_at=_now())
        )
        await db.commit()
        return None

    session.revoked_at = _now()
    new_raw = secrets.token_urlsafe(48)
    db.add(RefreshSession(
        tenant_id=session.tenant_id,
        user_id=session.user_id,
        token_hash=_hash(new_raw),
        expires_at=_now() + timedelta(days=REFRESH_DAYS),
    ))
    await db.commit()
    return session, new_raw


async def revoke_refresh_token(db: AsyncSession, raw: str) -> None:
    await db.execute(
        update(RefreshSession)
        .where(RefreshSession.token_hash == _hash(raw), RefreshSession.revoked_at.is_(None))
        .values(revoked_at=_now())
    )
    await db.commit()