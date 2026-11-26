import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, Page, get_current_user, require_roles, require_super_admin
from app.models.org_user import OrgUser
from app.models.tenant import Tenant
from app.schemas.tenant import (
    SubdomainCheckOut, TenantListOut, TenantOut, TenantSignupRequest,
    TenantSignupResponse, TenantUpdate,
)
from app.services.auth_service import create_access_token
from app.services.tenant_service import signup_tenant

router = APIRouter()


async def _get(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    t = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="tenant_not_found")
    return t


def _authorize(cu: CurrentUser, tenant_id: uuid.UUID) -> None:
    if not cu.is_super_admin and cu.tenant_id != tenant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="cross_tenant_forbidden")


async def _subdomain_taken(db: AsyncSession, name: str, exclude: uuid.UUID | None = None) -> bool:
    q = select(Tenant.id).where(Tenant.subdomain == name)
    if exclude:
        q = q.where(Tenant.id != exclude)
    return (await db.execute(q.limit(1))).scalar_one_or_none() is not None


# ---- public ----
@router.post("", response_model=TenantSignupResponse, status_code=201)
async def create_tenant(payload: TenantSignupRequest, db: AsyncSession = Depends(get_db)):
    if await _subdomain_taken(db, payload.subdomain):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="subdomain_taken")
    try:
        tenant = await signup_tenant(db, payload)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="tenant_already_exists")
    owner = (await db.execute(
        select(OrgUser).where(OrgUser.tenant_id == tenant.id, OrgUser.email == str(payload.owner_email))
    )).scalar_one()
    token = create_access_token(user_id=owner.id, tenant_id=tenant.id, email=owner.email)
    return TenantSignupResponse(tenant=TenantOut.model_validate(tenant), access_token=token)


@router.get("/subdomain-available", response_model=SubdomainCheckOut)
async def subdomain_available(name: str = Query(..., min_length=2, max_length=40, pattern=r"^[a-z0-9-]+$"),
                              db: AsyncSession = Depends(get_db)):
    return SubdomainCheckOut(subdomain=name, available=not await _subdomain_taken(db, name))


# ---- authenticated ----
@router.get("/me", response_model=TenantOut)
async def my_tenant(db: AsyncSession = Depends(get_db), cu: CurrentUser = Depends(get_current_user)):
    if cu.tenant_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="no_tenant_on_token")
    return await _get(db, cu.tenant_id)


@router.get("", response_model=TenantListOut)
async def list_tenants(
    q: str | None = None, status_filter: str | None = Query(None, alias="status"),
    page: Page = Depends(),
    db: AsyncSession = Depends(get_db), _: CurrentUser = Depends(require_super_admin),
):
    filters = []
    if q:
        filters.append(Tenant.name.ilike(f"%{q}%") | Tenant.subdomain.ilike(f"%{q}%"))
    if status_filter:
        filters.append(Tenant.status == status_filter)
    total = (await db.execute(select(func.count()).select_from(Tenant).where(*filters))).scalar_one()
    rows = (await db.execute(
        select(Tenant).where(*filters).order_by(Tenant.created_at.desc()).limit(page.limit).offset(page.offset)
    )).scalars().all()
    return TenantListOut(tenants=[TenantOut.model_validate(t) for t in rows],
                         total=total, limit=page.limit, offset=page.offset)


@router.get("/{tenant_id}", response_model=TenantOut)
async def get_tenant(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                     cu: CurrentUser = Depends(get_current_user)):
    _authorize(cu, tenant_id)
    return await _get(db, tenant_id)


@router.patch("/{tenant_id}", response_model=TenantOut)
async def update_tenant(
    tenant_id: uuid.UUID, payload: TenantUpdate, db: AsyncSession = Depends(get_db),
    cu: CurrentUser = Depends(get_current_user),
):
    _authorize(cu, tenant_id)
    if not cu.is_super_admin and cu.role not in ("TENANT", "OWNER", "ADMIN"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="insufficient_role")
    tenant = await _get(db, tenant_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "subdomain" in changes and await _subdomain_taken(db, changes["subdomain"], exclude=tenant_id):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="subdomain_taken")
    for k, v in changes.items():
        setattr(tenant, k, v)
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def _set_status(db: AsyncSession, tenant_id: uuid.UUID, new_status: str) -> Tenant:
    tenant = await _get(db, tenant_id)
    tenant.status = new_status
    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.post("/{tenant_id}/suspend", response_model=TenantOut)
async def suspend_tenant(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                         _: CurrentUser = Depends(require_super_admin)):
    return await _set_status(db, tenant_id, "suspended")


@router.post("/{tenant_id}/activate", response_model=TenantOut)
async def activate_tenant(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                          _: CurrentUser = Depends(require_super_admin)):
    return await _set_status(db, tenant_id, "active")


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                        _: CurrentUser = Depends(require_super_admin)):
    """Soft delete: status -> 'deleted' (login already rejects non-active tenants)."""
    await _set_status(db, tenant_id, "deleted")