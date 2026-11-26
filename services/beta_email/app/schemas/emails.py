from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Recipient(BaseModel):
    email: EmailStr
    name: str | None = None


class SendEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    template: Literal[
        "PASSWORD_RESET_REQUESTED",
        "PASSWORD_CHANGED",
        "LOGIN_FAILED_ALERT",
        "ONBOARDING_APPROVED",
    ]
    to: Recipient
    locale: Literal["en", "te", "hi"] = "en"
    tenantId: str | None = None
    userId: str | None = None
    priority: Literal["HIGH", "NORMAL"] = "NORMAL"
    expiresAt: datetime | None = None
    data: dict


class QueuedEmailResponse(BaseModel):
    messageId: UUID
    status: str
