from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PasswordResetRequestedData(StrictModel):
    ownerName: str
    resetLink: HttpUrl
    expiresInMinutes: int = 30
    requestedAt: datetime
    requestIp: str
    deviceDescription: str


class PasswordChangedData(StrictModel):
    ownerName: str
    changedAt: datetime
    changeType: Literal["RESET", "CHANGE"]
    ip: str
    deviceDescription: str
    location: str
    secureAccountLink: HttpUrl
    supportEmail: EmailStr


class LoginFailedAlertData(StrictModel):
    ownerName: str
    attemptCount: int = Field(ge=1)
    lastAttemptAt: datetime
    ip: str
    deviceDescription: str
    method: Literal["PASSWORD", "OTP", "GOOGLE"]
    locked: bool
    lockedUntil: datetime | None = None
    resetPasswordLink: HttpUrl


class OnboardingApprovedData(StrictModel):
    ownerName: str
    shopName: str
    tenantId: str
    referenceNo: str
    approvedAt: datetime
    signInUrl: HttpUrl
    loginEmail: EmailStr
    supportEmail: EmailStr
    helpCenterUrl: HttpUrl | None = None
