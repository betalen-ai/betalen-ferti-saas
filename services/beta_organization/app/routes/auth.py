from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.tenant import Tenant
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user, create_access_token

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    tenant = (
        await db.execute(select(Tenant).where(Tenant.subdomain == payload.subdomain))
    ).scalar_one_or_none()
    if not tenant or tenant.status != "active":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    user = await authenticate_user(
        db, tenant_id=tenant.id, email=str(payload.email), password=payload.password
    )
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    token = create_access_token(user_id=user.id, tenant_id=tenant.id, email=user.email)
    return TokenResponse(access_token=token, expires_in=settings.JWT_EXPIRE_MINUTES * 60)