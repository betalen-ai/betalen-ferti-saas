from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.permission import RolePermission
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleOut

router = APIRouter()


def _require_tenant(x_tenant_id: str | None = Header(default=None)) -> UUID:
    if not x_tenant_id:
        raise HTTPException(401, detail="missing_tenant_header")
    return UUID(x_tenant_id)


@router.get("", response_model=list[RoleOut])
async def list_roles(tenant_id: UUID = Depends(_require_tenant), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Role).where(Role.tenant_id == tenant_id))).scalars().all()
    out = []
    for r in rows:
        perm_ids = (
            await db.execute(select(RolePermission.permission_id).where(RolePermission.role_id == r.id))
        ).scalars().all()
        out.append(RoleOut(id=r.id, tenant_id=r.tenant_id, name=r.name, permission_ids=list(perm_ids)))
    return out


@router.post("", response_model=RoleOut, status_code=201)
async def create_role(
    payload: RoleCreate,
    tenant_id: UUID = Depends(_require_tenant),
    db: AsyncSession = Depends(get_db),
):
    role = Role(tenant_id=tenant_id, name=payload.name)
    db.add(role)
    await db.flush()
    for pid in payload.permission_ids:
        db.add(RolePermission(role_id=role.id, permission_id=pid))
    await db.commit()
    return RoleOut(id=role.id, tenant_id=role.tenant_id, name=role.name, permission_ids=payload.permission_ids)