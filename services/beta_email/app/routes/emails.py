from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Header, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.models import EmailMessage, EmailAttempt
from app.schemas.emails import SendEmailRequest, QueuedEmailResponse
from app.security import constant_time_key_match, service_key_map
from app.config import settings
from app.services.email_service import queue_email

router = APIRouter()


def require_service_key(
    x_service_key: str = Header(..., alias="X-Service-Key"),
):
    for service, key in service_key_map().items():
        if constant_time_key_match(x_service_key, key):
            return service
    if settings.ADMIN_API_KEY and constant_time_key_match(x_service_key, settings.ADMIN_API_KEY):
        return "admin"
    raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Invalid service key"})


@router.post("/emails", status_code=202, response_model=QueuedEmailResponse)
async def send_email(
    request: SendEmailRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_request_id: str | None = Header(None, alias="X-Request-Id"),
    caller: str = Depends(require_service_key),
    session: AsyncSession = Depends(get_db),
):
    message, repeated = await queue_email(session, request, caller, x_request_id, idempotency_key)
    return {"messageId": message.id, "status": message.status}


@router.get("/emails/{message_id}")
async def get_email(
    message_id: UUID,
    caller: str = Depends(require_service_key),
    session: AsyncSession = Depends(get_db),
):
    message = await session.get(EmailMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Email not found"})
    attempts = (await session.execute(
        select(EmailAttempt).where(EmailAttempt.message_id == message_id).order_by(EmailAttempt.attempt_no)
    )).scalars().all()
    return {
        "id": str(message.id),
        "template": message.template,
        "locale": message.locale,
        "status": message.status,
        "priority": message.priority,
        "attempts": message.attempts,
        "nextAttemptAt": message.next_attempt_at,
        "sentAt": message.sent_at,
        "createdAt": message.created_at,
        "provider": message.provider,
        "providerMessageId": message.provider_message_id,
        "attemptDetails": [
            {
                "attemptNo": item.attempt_no,
                "startedAt": item.started_at,
                "finishedAt": item.finished_at,
                "result": item.result,
                "smtpCode": item.smtp_code,
                "durationMs": item.duration_ms,
            } for item in attempts
        ],
    }


@router.get("/emails")
async def list_emails(
    tenantId: str | None = None,
    template: str | None = None,
    status: str | None = None,
    to: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    caller: str = Depends(require_service_key),
    session: AsyncSession = Depends(get_db),
):
    query = select(EmailMessage)
    if tenantId:
        query = query.where(EmailMessage.tenant_id == tenantId)
    if template:
        query = query.where(EmailMessage.template == template)
    if status:
        query = query.where(EmailMessage.status == status)
    if to:
        query = query.where(EmailMessage.to_email == to)
    query = query.order_by(EmailMessage.created_at.desc()).offset(offset).limit(limit)
    rows = (await session.execute(query)).scalars().all()
    return {"items": [
        {
            "id": str(row.id),
            "template": row.template,
            "status": row.status,
            "attempts": row.attempts,
            "createdAt": row.created_at,
            "sentAt": row.sent_at,
        } for row in rows
    ], "offset": offset, "limit": limit}


@router.post("/emails/{message_id}/retry")
async def retry_email(
    message_id: UUID,
    caller: str = Depends(require_service_key),
    session: AsyncSession = Depends(get_db),
):
    if caller != "admin":
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Admin key required"})
    message = await session.get(EmailMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Email not found"})
    if message.status not in ("FAILED", "DEAD"):
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATUS", "message": "Only FAILED or DEAD can be retried"})
    message.status = "QUEUED"
    message.next_attempt_at = datetime.now()
    await session.commit()
    return {"messageId": str(message.id), "status": "QUEUED"}
