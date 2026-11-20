import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class TenantSignupRequest(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=120)
    subdomain: str = Field(min_length=2, max_length=40, pattern=r"^[a-z0-9-]+$")
    owner_email: EmailStr
    owner_phone: str | None = Field(default=None, min_length=7, max_length=24)
    owner_password: str = Field(min_length=8, max_length=128)
    owner_full_name: str | None = None

    @field_validator("owner_password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password cannot exceed 72 UTF-8 bytes")
        return value


class TenantOut(BaseModel):
    id: uuid.UUID
    name: str
    subdomain: str | None
    subscription_plan: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantSignupResponse(BaseModel):
    tenant: TenantOut
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"