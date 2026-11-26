import json
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select

from app.models.models import EmailMessage, EmailSuppression
from app.schemas.template_data import (
    PasswordResetRequestedData,
    PasswordChangedData,
    LoginFailedAlertData,
    OnboardingApprovedData,
)
from app.schemas.emails import SendEmailRequest
from app.security import encrypt_payload
from app.config import settings


MODEL_MAP = {
    "PASSWORD_RESET_REQUESTED": PasswordResetRequestedData,
    "PASSWORD_CHANGED": PasswordChangedData,
    "LOGIN_FAILED_ALERT": LoginFailedAlertData,
    "ONBOARDING_APPROVED": OnboardingApprovedData,
}

LINK_FIELDS = {
    "PASSWORD_RESET_REQUESTED": ("resetLink",),
    "PASSWORD_CHANGED": ("secureAccountLink",),
    "LOGIN_FAILED_ALERT": ("resetPasswordLink",),
    "ONBOARDING_APPROVED": ("signInUrl", "helpCenterUrl"),
}


def validate_template(template: str, data: dict) -> dict:
    model = MODEL_MAP.get(template)
    if not model:
        raise HTTPException(status_code=422, detail={"code": "INVALID_TEMPLATE_DATA", "message": "Unknown template"})
    try:
        validated = model.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_TEMPLATE_DATA", "message": exc.errors(include_url=False)})
    base = urlparse(settings.APP_BASE_URL)
    for field_name in LINK_FIELDS[template]:
        value = getattr(validated, field_name, None)
        if value is None:
            continue
        parsed = urlparse(str(value))
        if parsed.scheme not in ("http", "https") or parsed.netloc != base.netloc:
            raise HTTPException(status_code=422, detail={"code": "INVALID_TEMPLATE_DATA", "message": f"{field_name} is outside APP_BASE_URL"})
    return validated.model_dump(mode="json")


async def queue_email(session, request: SendEmailRequest, caller: str, request_id: str | None,
                      idempotency: str) -> tuple[EmailMessage, bool]:
    if not idempotency:
        raise HTTPException(status_code=400, detail={"code": "INVALID_REQUEST", "message": "Idempotency-Key is required"})
    data = validate_template(request.template, request.data)
    payload = json.dumps({
        "template": request.template,
        "to": request.to.model_dump(mode="json"),
        "locale": request.locale,
        "tenantId": request.tenantId,
        "userId": request.userId,
        "priority": request.priority,
        "expiresAt": request.expiresAt.isoformat() if request.expiresAt else None,
        "data": data,
    }, sort_keys=True)
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    existing = (await session.execute(
        select(EmailMessage).where(
            EmailMessage.caller_service == caller,
            EmailMessage.idempotency_key == idempotency,
        )
    )).scalars().first()
    if existing:
        if existing.idempotency_hash and existing.idempotency_hash != payload_hash:
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_CONFLICT", "message": "Idempotency key was used with a different request"})
        return existing, True

    suppressed = (await session.execute(
        select(EmailSuppression).where(EmailSuppression.email == str(request.to.email))
    )).scalars().first()
    status = "SUPPRESSED" if suppressed else "QUEUED"
    message = EmailMessage(
        id=uuid4(),
        tenant_id=request.tenantId,
        user_id=request.userId,
        template=request.template,
        locale=request.locale,
        to_email=str(request.to.email),
        to_name=request.to.name,
        subject="",
        status=status,
        priority=request.priority,
        payload_encrypted=None if status == "SUPPRESSED" else encrypt_payload(payload),
        idempotency_key=idempotency,
        idempotency_hash=payload_hash,
        attempts=0,
        next_attempt_at=datetime.now(timezone.utc),
        caller_service=caller,
        expires_at=request.expiresAt,
        request_id=request_id,
        created_at=datetime.now(timezone.utc),
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message, False
