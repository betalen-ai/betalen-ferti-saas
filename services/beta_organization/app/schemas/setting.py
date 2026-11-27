import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
from app.schemas.common import TenantIn


class SettingsIn(TenantIn):
    values: dict[str, Any]


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tenant_id: uuid.UUID
    values: dict[str, Any]
    updated_at: datetime