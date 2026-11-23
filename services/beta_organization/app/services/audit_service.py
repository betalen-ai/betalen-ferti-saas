import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import AuditLogEntry, AuthEvent


async def write_auth_event(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    identifier: str | None,
    method: str,
    event_type: str,
    success: bool,
    failure_reason: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> None:
    db.add(AuthEvent(
        tenant_id=tenant_id,
        user_id=user_id,
        identifier=identifier,
        method=method,
        event_type=event_type,
        success=success,
        failure_reason=failure_reason,
        ip=ip,
        user_agent=user_agent,
        request_id=request_id,
    ))


async def write_audit_log(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    actor_type: str,
    action: str,
    entity_name: str,
    entity_id: uuid.UUID | None,
    payload: dict[str, Any],
    ip: str | None = None,
    request_id: str | None = None,
) -> None:
    db.add(AuditLogEntry(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        actor_type=actor_type,
        action=action,
        entity_name=entity_name,
        entity_id=entity_id,
        json_payload=payload,
        ip=ip,
        request_id=request_id,
    ))
