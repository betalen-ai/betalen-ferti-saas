import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    subdomain: str | None = None
    tenant_id: str | None = None
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("tenant_id")
    @classmethod
    def validate_tenant_id(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        try:
            uuid.UUID(value)
        except (ValueError, AttributeError) as exc:
            raise ValueError("tenant_id must be a valid UUID") from exc
        return value

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


class MeResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: EmailStr