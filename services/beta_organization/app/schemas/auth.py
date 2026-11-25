import uuid
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    tenant_id: str | None = None
    subdomain: str | None = None
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
