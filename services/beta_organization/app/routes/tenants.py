from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.org_user import OrgUser
from app.models.tenant import Tenant
from app.schemas.tenant import TenantOut, TenantSignupRequest, TenantSignupResponse
from app.services.tenant_service import signup_tenant
from app.routes.ferti import (
    _enforce_auth_rate_limit,
    _issue_session,
    _set_session_cookies,
    current_identity,
)

router = APIRouter()


@router.post("", response_model=TenantSignupResponse, status_code=201)
async def create_tenant(
    payload: TenantSignupRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    await _enforce_auth_rate_limit(
        db, request, action="register", subject=str(payload.owner_email), limit=5, window_seconds=3600
    )
    tenant = await signup_tenant(db, payload)
    owner = (
        await db.execute(
            select(OrgUser).where(
                OrgUser.tenant_id == tenant.id, OrgUser.email == str(payload.owner_email)
            )
        )
    ).scalar_one()
    tokens = await _issue_session(db, owner)
    await db.commit()
    _set_session_cookies(response, tokens)
    return TenantSignupResponse(tenant=TenantOut.model_validate(tenant), **tokens)


@router.get("/{tenant_id}", response_model=TenantOut)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    identity: dict[str, UUID] = Depends(current_identity),
):
    if tenant_id != identity["tenant_id"]:
        raise HTTPException(404, detail="tenant_not_found")
    tenant = (await db.execute(select(Tenant).where(
        Tenant.id == tenant_id, Tenant.id == identity["tenant_id"]
    ))).scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, detail="tenant_not_found")
    return tenant