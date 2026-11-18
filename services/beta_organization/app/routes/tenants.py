from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.org_user import OrgUser
from app.models.tenant import Tenant
from app.schemas.tenant import TenantOut, TenantSignupRequest, TenantSignupResponse
from app.services.auth_service import create_access_token
from app.services.tenant_service import signup_tenant

router = APIRouter()


@router.post("", response_model=TenantSignupResponse, status_code=201)
async def create_tenant(payload: TenantSignupRequest, db: AsyncSession = Depends(get_db)):
    tenant = await signup_tenant(db, payload)
    owner = (
        await db.execute(
            select(OrgUser).where(
                OrgUser.tenant_id == tenant.id, OrgUser.email == str(payload.owner_email)
            )
        )
    ).scalar_one()
    token = create_access_token(user_id=owner.id, tenant_id=tenant.id, email=owner.email)
    return TenantSignupResponse(tenant=TenantOut.model_validate(tenant), access_token=token)


@router.get("/{tenant_id}", response_model=TenantOut)
async def get_tenant(tenant_id: UUID, db: AsyncSession = Depends(get_db)):
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, detail="tenant_not_found")
    return tenant