from pydantic import BaseModel, EmailStr, Field

class SignupRequest(BaseModel):
    owner_name: str = Field(min_length=2)
    shop_name: str = Field(min_length=2)
    email: EmailStr
    mobile: str = Field(pattern=r"^[6-9]\d{9}$")
    password: str = Field(min_length=8)

class SignupResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
