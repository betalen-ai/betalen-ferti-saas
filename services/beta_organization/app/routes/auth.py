import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.org_user import OrgUser
from app.models.tenant import Tenant
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user, create_access_token, verify_password

router = APIRouter()


async def _resolve_tenant(db: AsyncSession, payload: LoginRequest) -> Tenant | None:
    if payload.tenant_id:
        try:
            tid = uuid.UUID(payload.tenant_id)
        except (ValueError, AttributeError):
            return None
        return (await db.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
    if payload.subdomain:
        return (await db.execute(select(Tenant).where(Tenant.subdomain == payload.subdomain))).scalar_one_or_none()
    return None


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    tenant = await _resolve_tenant(db, payload)

    # Super-admin login: no tenant required. Email must exist globally and be a super admin.
    if tenant is None:
        result = await db.execute(select(OrgUser).where(OrgUser.email == str(payload.email)))
        user = result.scalar_one_or_none()
        if user and user.is_super_admin and verify_password(payload.password, user.password_hash):
            token = create_access_token(user_id=user.id, tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"), email=user.email)
            return TokenResponse(access_token=token, expires_in=settings.JWT_EXPIRE_MINUTES * 60)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    if tenant.status != "active":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    user = await authenticate_user(
        db, tenant_id=tenant.id, email=str(payload.email), password=payload.password
    )
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    token = create_access_token(user_id=user.id, tenant_id=tenant.id, email=user.email)
    return TokenResponse(access_token=token, expires_in=settings.JWT_EXPIRE_MINUTES * 60)