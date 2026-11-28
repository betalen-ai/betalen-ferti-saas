import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class OrgUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None
    role_id: uuid.UUID | None = None


class OrgUserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    role_id: uuid.UUID | None = None


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class OrgUserOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role_id: uuid.UUID | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OrgUserListOut(BaseModel):
    users: list[OrgUserOut]
    total: int
    limit: int
    offset: int
