from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    subdomain: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: EmailStr