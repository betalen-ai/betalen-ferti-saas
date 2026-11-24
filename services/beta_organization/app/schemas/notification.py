import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class NotificationOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    type: str
    severity: str = "INFO"  # INFO | WARNING | CRITICAL
    title: str
    message: str
    notification_key: str | None = None
    channels_sent: list[str] = []
    is_read: bool = False
    read_at: datetime | None = None
    action_label: str | None = None
    action_route: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class NotificationListOut(BaseModel):
    notifications: list[NotificationOut]
    unread_count: int
    total: int


class NotificationReadRequest(BaseModel):
    notification_id: uuid.UUID


class MarkAllReadRequest(BaseModel):
    pass