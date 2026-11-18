from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.org_user import OrgUser
from app.schemas.org_user import OrgUserCreate, OrgUserOut
from app.services.auth_service import hash_password

router = APIRouter()


def _require_tenant(x_tenant_id: str | None = Header(default=None)) -> UUID:
    if not x_tenant_id:
        raise HTTPException(401, detail="missing_tenant_header")
    return UUID(x_tenant_id)


@router.post("", response_model=OrgUserOut, status_code=201)
async def create_user(
    payload: OrgUserCreate,
    tenant_id: UUID = Depends(_require_tenant),
    db: AsyncSession = Depends(get_db),
):
    dup = (
        await db.execute(
            select(OrgUser).where(OrgUser.tenant_id == tenant_id, OrgUser.email == str(payload.email))
        )
    ).scalar_one_or_none()
    if dup:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email_exists_in_tenant")

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