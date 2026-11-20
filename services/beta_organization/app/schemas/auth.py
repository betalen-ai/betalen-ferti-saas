import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    subdomain: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password cannot exceed 72 UTF-8 bytes")
        return value


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


class CurrentUser(BaseModel):
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    role: str | None = None
    permissions: list[str] = []