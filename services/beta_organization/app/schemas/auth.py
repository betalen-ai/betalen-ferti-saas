import uuid
from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    tenant_id: str | None = None
    subdomain: str | None = None
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class SignupRequest(BaseModel):
    owner_name: str = Field(min_length=2, max_length=120)
    shop_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    mobile: str = Field(description="10-digit number, without +91")
    password: str = Field(min_length=8, max_length=128)

class SignupResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
