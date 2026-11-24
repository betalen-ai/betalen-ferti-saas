from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.tenant import Tenant
from app.models.org_user import OrgUser
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user, create_access_token, verify_password

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    
    tenant_id = None
    
    # 1. Resolve Tenant ID (Shop POS users)
    if payload.tenant_id:
        tenant_id = payload.tenant_id
    elif payload.subdomain:
        tenant = (await db.execute(select(Tenant).where(Tenant.subdomain == payload.subdomain))).scalar_one_or_none()
        if not tenant:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
        tenant_id = tenant.id

    # 2. Authenticate
    if tenant_id:
        # Standard Shop Owner / Cashier
        user = await authenticate_user(db, tenant_id=tenant_id, email=str(payload.email), password=payload.password)
    else:
        # Super Admin (Backoffice) - No tenant ID provided, look up by email
        result = await db.execute(select(OrgUser).where(OrgUser.email == str(payload.email), OrgUser.status == "active"))
        user = result.scalar_one_or_none()
        if not user or not verify_password(payload.password, user.password_hash):
            user = None

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, email=user.email)
    return TokenResponse(access_token=token, expires_in=settings.JWT_EXPIRE_MINUTES * 60)
