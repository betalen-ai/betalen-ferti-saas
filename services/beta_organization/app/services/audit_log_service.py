import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.services.crud_base import get_owned


async def list_audit_logs(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    limit: int = 100,
    offset: int = 0,
):
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


async def get_audit_log(db: AsyncSession, tenant_id: uuid.UUID, log_id: uuid.UUID) -> AuditLog:
    return await get_owned(db, AuditLog, log_id, tenant_id, "audit_log_not_found")