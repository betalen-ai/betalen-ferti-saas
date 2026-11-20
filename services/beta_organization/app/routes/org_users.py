from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.org_user import OrgUser
from app.models.role import Role
from app.schemas.org_user import OrgUserCreate, OrgUserOut
from app.services.auth_service import hash_password
from app.routes.ferti import current_identity

router = APIRouter()


@router.post("", response_model=OrgUserOut, status_code=201)
async def create_user(
    payload: OrgUserCreate,
    identity: dict[str, UUID] = Depends(current_identity),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = identity["tenant_id"]
    dup = (
        await db.execute(
            select(OrgUser).where(OrgUser.tenant_id == tenant_id, OrgUser.email == str(payload.email))
        )
    ).scalar_one_or_none()
    if dup:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email_exists_in_tenant")
    if payload.role_id:
        role = (await db.execute(select(Role).where(
            Role.id == payload.role_id, Role.tenant_id == tenant_id
        ))).scalar_one_or_none()
        if role is None:
            raise HTTPException(404, detail="role_not_found")

    user = OrgUser(
        tenant_id=tenant_id,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role_id=payload.role_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user