import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, Page, require_permission
from app.models.org_user import OrgUser
from app.schemas.org_user import (
    OrgUserCreate, OrgUserListOut, OrgUserOut, OrgUserUpdate, PasswordReset,
)
from app.services.auth_service import hash_password

router = APIRouter()
manage_users = require_permission("users.manage")


async def _get(db: AsyncSession, tenant_id, user_id: uuid.UUID) -> OrgUser:
    u = (await db.execute(
        select(OrgUser).where(OrgUser.id == user_id, OrgUser.tenant_id == tenant_id)
    )).scalar_one_or_none()
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user_not_found")
    return u


async def _email_taken(db, tenant_id, email: str, exclude: uuid.UUID | None = None) -> bool:
    q = select(OrgUser.id).where(OrgUser.tenant_id == tenant_id, OrgUser.email == email)
    if exclude:
        q = q.where(OrgUser.id != exclude)
    return (await db.execute(q.limit(1))).scalar_one_or_none() is not None


@router.post("", response_model=OrgUserOut, status_code=201)
async def create_user(payload: OrgUserCreate, db: AsyncSession = Depends(get_db),
                      cu: CurrentUser = Depends(manage_users)):
    if await _email_taken(db, cu.tenant_id, str(payload.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email_exists_in_tenant")
    user = OrgUser(
        tenant_id=cu.tenant_id, email=str(payload.email), password_hash=hash_password(payload.password),
        full_name=payload.full_name, role_id=payload.role_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("", response_model=OrgUserListOut)
async def list_users(
    q: str | None = Query(None, description="search email/name"),
    status_filter: str | None = Query(None, alias="status"),
    role_id: uuid.UUID | None = None,
    page: Page = Depends(),
    db: AsyncSession = Depends(get_db), cu: CurrentUser = Depends(manage_users),
):
    filters = [OrgUser.tenant_id == cu.tenant_id]
    if q:
        like = f"%{q}%"
        filters.append(or_(OrgUser.email.ilike(like), OrgUser.full_name.ilike(like)))
    if status_filter:
        filters.append(OrgUser.status == status_filter)
    if role_id:
        filters.append(OrgUser.role_id == role_id)
    total = (await db.execute(select(func.count()).select_from(OrgUser).where(*filters))).scalar_one()
    rows = (await db.execute(
        select(OrgUser).where(*filters).order_by(OrgUser.created_at.desc()).limit(page.limit).offset(page.offset)
    )).scalars().all()
    return OrgUserListOut(users=rows, total=total, limit=page.limit, offset=page.offset)


@router.get("/{user_id}", response_model=OrgUserOut)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                   cu: CurrentUser = Depends(manage_users)):
    return await _get(db, cu.tenant_id, user_id)


@router.patch("/{user_id}", response_model=OrgUserOut)
async def update_user(user_id: uuid.UUID, payload: OrgUserUpdate, db: AsyncSession = Depends(get_db),
                      cu: CurrentUser = Depends(manage_users)):
    user = await _get(db, cu.tenant_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    if "email" in changes and changes["email"] is not None:
        changes["email"] = str(changes["email"])
        if await _email_taken(db, cu.tenant_id, changes["email"], exclude=user.id):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="email_exists_in_tenant")
    for k, v in changes.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user


async def _set_status(db, cu: CurrentUser, user_id: uuid.UUID, new_status: str) -> OrgUser:
    if cu.user_id == user_id and new_status != "active":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="cannot_disable_self")
    user = await _get(db, cu.tenant_id, user_id)
    user.status = new_status
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/{user_id}/activate", response_model=OrgUserOut)
async def activate_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                        cu: CurrentUser = Depends(manage_users)):
    return await _set_status(db, cu, user_id, "active")


@router.post("/{user_id}/deactivate", response_model=OrgUserOut)
async def deactivate_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                          cu: CurrentUser = Depends(manage_users)):
    return await _set_status(db, cu, user_id, "disabled")


@router.post("/{user_id}/reset-password", status_code=204)
async def reset_password(user_id: uuid.UUID, payload: PasswordReset, db: AsyncSession = Depends(get_db),
                         cu: CurrentUser = Depends(manage_users)):
    user = await _get(db, cu.tenant_id, user_id)
    user.password_hash = hash_password(payload.new_password)
    await db.commit()


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                      cu: CurrentUser = Depends(manage_users)):
    """Soft delete."""
    await _set_status(db, cu, user_id, "deleted")