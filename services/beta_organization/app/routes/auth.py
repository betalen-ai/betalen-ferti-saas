from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.config import settings
from app.db import get_db
from app.models.tenant import Tenant
from app.models.org_user import OrgUser
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user, create_access_token, verify_password

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    
    tenant = None
    
    # 1. Try to find the tenant by ID or Subdomain
    tenant_identifier = payload.tenant_id or payload.subdomain
    
    if tenant_identifier:
        try:
            # Check if it's a valid UUID
            tenant_uuid = uuid.UUID(tenant_identifier)
            tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))).scalar_one_or_none()
        except ValueError:
            # Not a UUID, so treat it as a subdomain
            tenant = (await db.execute(select(Tenant).where(Tenant.subdomain == tenant_identifier))).scalar_one_or_none()
            
        if not tenant or tenant.status != "active":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

        # Authenticate with tenant_id
        user = await authenticate_user(
            db, tenant_id=tenant.id, email=str(payload.email), password=payload.password
        )
    else:
        # Super Admin (No tenant provided)
        result = await db.execute(select(OrgUser).where(OrgUser.email == str(payload.email), OrgUser.status == "active"))
        user = result.scalar_one_or_none()
        if user and not verify_password(payload.password, user.password_hash):
            user = None

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, email=user.email)
    return TokenResponse(access_token=token, expires_in=settings.JWT_EXPIRE_MINUTES * 60)
