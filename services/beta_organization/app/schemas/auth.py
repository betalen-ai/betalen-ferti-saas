import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    subdomain: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUser(BaseModel):
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    role: str | None = None
    permissions: list[str] = []