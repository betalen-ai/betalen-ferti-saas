from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.tenant import Tenant
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user
from app.routes.ferti import _enforce_auth_rate_limit
from app.routes.ferti import _issue_session, _set_session_cookies

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    await _enforce_auth_rate_limit(
        db, request, action="login", subject=f"{payload.subdomain}:{payload.email}", limit=5, window_seconds=60
    )
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
    if not user.email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="email_verification_required")

    tokens = await _issue_session(db, user)
    await db.commit()
    _set_session_cookies(response, tokens)
    return TokenResponse(**tokens)