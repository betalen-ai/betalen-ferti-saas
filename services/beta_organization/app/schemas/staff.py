import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field, field_validator


class StaffCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    mobile: str = Field(pattern=r"^\+91[6-9]\d{9}$")
    email: EmailStr | None = None
    role_template: str = Field(pattern=r"^(pos_user|stock_keeper|accountant|custom)$")
    permissions: list[str] = []
    is_active: bool = True


class StaffUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    mobile: str | None = Field(default=None, pattern=r"^\+91[6-9]\d{9}$")
    email: EmailStr | None = None
    role_template: str | None = Field(default=None, pattern=r"^(pos_user|stock_keeper|accountant|custom)$")
    permissions: list[str] | None = None
    is_active: bool | None = None


class StaffOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    role: str = "STAFF"
    name: str | None
    mobile: str | None
    email: str | None
    role_template: str | None
    permissions: list[str] = []
    is_active: bool = True
    status: str = "ACTIVE"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class StaffListOut(BaseModel):
    staff: list[StaffOut]
    total: int
    seats_used: int
    seats_available: int | None = None