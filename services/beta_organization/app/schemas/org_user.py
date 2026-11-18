import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class OrgUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    role_id: uuid.UUID


class OrgUserOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role_id: uuid.UUID | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}