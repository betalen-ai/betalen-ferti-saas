import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

ROLE_TEMPLATES = r"^(pos_user|stock_keeper|accountant|custom)$"
MOBILE = r"^\+91[6-9]\d{9}$"


class StaffCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    mobile: str = Field(pattern=MOBILE)
    email: EmailStr | None = None
    role_template: str = Field(pattern=ROLE_TEMPLATES)
    permissions: list[str] = []
    is_active: bool = True
    password: str | None = Field(default=None, min_length=8, max_length=128)


class StaffUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    mobile: str | None = Field(default=None, pattern=MOBILE)
    email: EmailStr | None = None
    role_template: str | None = Field(default=None, pattern=ROLE_TEMPLATES)
    permissions: list[str] | None = None


class StaffPasswordReset(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


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


class SeatsOut(BaseModel):
    plan: str
    max_staff: int | None
    seats_used: int
    seats_available: int | None
