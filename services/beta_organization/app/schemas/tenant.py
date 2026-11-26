import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class TenantSignupRequest(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=120)
    subdomain: str = Field(min_length=2, max_length=40, pattern=r"^[a-z0-9-]+$")
    owner_email: EmailStr
    owner_password: str = Field(min_length=8, max_length=128)
    owner_full_name: str | None = None


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    subdomain: str | None = Field(default=None, min_length=2, max_length=40, pattern=r"^[a-z0-9-]+$")


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
    token_type: str = "bearer"


class TenantListOut(BaseModel):
    tenants: list[TenantOut]
    total: int
    limit: int
    offset: int


class SubdomainCheckOut(BaseModel):
    subdomain: str
    available: bool