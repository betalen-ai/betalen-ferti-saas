"""Staff management routes (spec v2, section 7)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, Page, require_permission
from app.models.org_user import User
from app.models.tenant import Tenant
from app.models.v2 import Staff, SubscriptionPlan
from app.schemas.staff import (
    SeatsOut, StaffCreate, StaffListOut, StaffOut, StaffPasswordReset, StaffUpdate,
)
from app.services.audit_service import write_audit_log, write_auth_event
from app.services.auth_service import hash_password
from app.services.subscription_service import evaluate_access

router = APIRouter()

DEFAULT_MAX_STAFF = 2  # used only if the plan row is missing; plan.max_staff None = unlimited

manage_staff = require_permission("staff.manage")


# ---------- helpers ----------
def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _out(s: Staff) -> StaffOut:
    return StaffOut(
        id=s.id, tenant_id=s.tenant_id, role="STAFF", name=s.name, mobile=s.mobile,
        email=s.email, role_template=s.role_template, permissions=s.permissions or [],
        is_active=s.is_active, status="ACTIVE" if s.is_active else "DISABLED",
        created_at=s.created_at, updated_at=s.updated_at,
    )


async def _access(db: AsyncSession, cu: CurrentUser, method: str):
    access = await evaluate_access(db, tenant_id=cu.tenant_id, role=cu.role, path="/staff", method=method)
    if not access.allowed:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, detail=access.error_code)
    return access


async def _limit(db: AsyncSession, plan_code: str) -> int | None:
    plan = (await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == plan_code))).scalar_one_or_none()
    return DEFAULT_MAX_STAFF if plan is None else plan.max_staff


async def _active_count(db: AsyncSession, tenant_id) -> int:
    return (await db.execute(
        select(func.count()).select_from(Staff).where(Staff.tenant_id == tenant_id, Staff.is_active.is_(True))
    )).scalar_one()


async def _lock_tenant(db: AsyncSession, tenant_id) -> None:
    """Serialise seat-changing requests per tenant so the seat check cannot be raced."""
    await db.execute(select(Tenant.id).where(Tenant.id == tenant_id).with_for_update())


async def _check_seat(db: AsyncSession, tenant_id, plan_code: str) -> None:
    max_staff = await _limit(db, plan_code)
    used = await _active_count(db, tenant_id)
    if max_staff is not None and used >= max_staff:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={"error": "staff_limit_reached", "max_staff": max_staff, "seats_used": used},
        )


async def _get_staff(db: AsyncSession, tenant_id, staff_id: uuid.UUID) -> Staff:
    s = (await db.execute(select(Staff).where(Staff.id == staff_id, Staff.tenant_id == tenant_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="staff_not_found")
    return s


async def _linked_user(db: AsyncSession, staff: Staff) -> User | None:
    conds = [User.phone == staff.mobile] if staff.mobile else []
    if staff.email:
        conds.append(User.email == staff.email)
    if not conds:
        return None
    return (await db.execute(
        select(User).where(User.tenant_id == staff.tenant_id, User.role == "STAFF", or_(*conds)).limit(1)
    )).scalars().first()


async def _ensure_unique(db: AsyncSession, tenant_id, mobile, email, exclude_id=None) -> None:
    conds = []
    if mobile:
        conds.append(Staff.mobile == mobile)
    if email:
        conds.append(Staff.email == email)
    if not conds:
        return
    q = select(Staff.id).where(Staff.tenant_id == tenant_id, or_(*conds))
    if exclude_id:
        q = q.where(Staff.id != exclude_id)
    if (await db.execute(q.limit(1))).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, detail="staff_already_exists")


async def _commit(db: AsyncSession) -> None:
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="staff_already_exists")


async def _audit(db, cu: CurrentUser, request: Request, action: str, staff: Staff, payload: dict):
    await write_audit_log(
        db, tenant_id=cu.tenant_id, actor_user_id=cu.user_id, actor_type="TENANT",
        action=action, entity_name="staff", entity_id=staff.id, payload=payload,
        ip=_ip(request), request_id=request.headers.get("x-request-id"),
    )


# ---------- endpoints ----------
@router.post("", response_model=StaffOut, status_code=201)
async def create_staff(
    payload: StaffCreate, request: Request,
    db: AsyncSession = Depends(get_db), cu: CurrentUser = Depends(manage_staff),
):
    access = await _access(db, cu, "POST")
    await _lock_tenant(db, cu.tenant_id)
    if payload.is_active:
        await _check_seat(db, cu.tenant_id, access.subscription.get("plan", "TRIAL"))
    await _ensure_unique(db, cu.tenant_id, payload.mobile, payload.email)

    staff = Staff(
        tenant_id=cu.tenant_id, name=payload.name, mobile=payload.mobile, email=payload.email,
        role_template=payload.role_template, permissions=payload.permissions, is_active=payload.is_active,
    )
    db.add(staff)
    await db.flush()

    user = User(
        tenant_id=cu.tenant_id, role="STAFF", name=payload.name, email=payload.email,
        phone=payload.mobile, permissions=payload.permissions,
        status="ACTIVE" if payload.is_active else "DISABLED", created_by=cu.user_id,
    )
    if payload.password:
        user.password_hash = hash_password(payload.password)
    db.add(user)
    await db.flush()

    await _audit(db, cu, request, "STAFF_CREATED", staff,
                 {"name": payload.name, "role_template": payload.role_template})
    await write_auth_event(
        db, tenant_id=cu.tenant_id, user_id=user.id, identifier=payload.mobile or payload.email or "",
        method="PASSWORD", event_type="STAFF_CREATED", success=True, failure_reason=None, request=request,
    )
    await _commit(db)
    return _out(staff)


@router.get("", response_model=StaffListOut)
async def list_staff(
    q: str | None = Query(None, description="search name/mobile/email"),
    is_active: bool | None = None,
    role_template: str | None = None,
    page: Page = Depends(),
    db: AsyncSession = Depends(get_db), cu: CurrentUser = Depends(manage_staff),
):
    access = await _access(db, cu, "GET")

    filters = [Staff.tenant_id == cu.tenant_id]
    if is_active is not None:
        filters.append(Staff.is_active.is_(is_active))
    if role_template:
        filters.append(Staff.role_template == role_template)
    if q:
        like = f"%{q}%"
        filters.append(or_(Staff.name.ilike(like), Staff.mobile.ilike(like), Staff.email.ilike(like)))

    total = (await db.execute(select(func.count()).select_from(Staff).where(*filters))).scalar_one()
    rows = (await db.execute(
        select(Staff).where(*filters).order_by(Staff.created_at.desc()).limit(page.limit).offset(page.offset)
    )).scalars().all()

    max_staff = await _limit(db, access.subscription.get("plan", "TRIAL"))
    used = await _active_count(db, cu.tenant_id)
    return StaffListOut(
        staff=[_out(s) for s in rows], total=total, seats_used=used,
        seats_available=None if max_staff is None else max(0, max_staff - used),
    )


@router.get("/seats", response_model=SeatsOut)
async def seats(db: AsyncSession = Depends(get_db), cu: CurrentUser = Depends(manage_staff)):
    access = await _access(db, cu, "GET")
    plan_code = access.subscription.get("plan", "TRIAL")
    max_staff = await _limit(db, plan_code)
    used = await _active_count(db, cu.tenant_id)
    return SeatsOut(plan=plan_code, max_staff=max_staff, seats_used=used,
                    seats_available=None if max_staff is None else max(0, max_staff - used))


@router.get("/{staff_id}", response_model=StaffOut)
async def get_staff(staff_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                    cu: CurrentUser = Depends(manage_staff)):
    await _access(db, cu, "GET")
    return _out(await _get_staff(db, cu.tenant_id, staff_id))


@router.patch("/{staff_id}", response_model=StaffOut)
async def update_staff(
    staff_id: uuid.UUID, payload: StaffUpdate, request: Request,
    db: AsyncSession = Depends(get_db), cu: CurrentUser = Depends(manage_staff),
):
    await _access(db, cu, "PATCH")
    staff = await _get_staff(db, cu.tenant_id, staff_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return _out(staff)

    await _ensure_unique(db, cu.tenant_id, changes.get("mobile"), changes.get("email"), exclude_id=staff.id)
    user = await _linked_user(db, staff)  # look up BEFORE mobile/email change

    for k, v in changes.items():
        setattr(staff, k, v)
    if user:
        if "name" in changes: user.name = staff.name
        if "mobile" in changes: user.phone = staff.mobile
        if "email" in changes: user.email = staff.email
        if "permissions" in changes: user.permissions = staff.permissions

    await _audit(db, cu, request, "STAFF_UPDATED", staff, {"fields": list(changes.keys())})
    await _commit(db)
    return _out(staff)


async def _set_active(staff_id, active: bool, request, db, cu) -> StaffOut:
    access = await _access(db, cu, "POST")
    await _lock_tenant(db, cu.tenant_id)
    staff = await _get_staff(db, cu.tenant_id, staff_id)
    if staff.is_active == active:
        return _out(staff)
    if active:
        await _check_seat(db, cu.tenant_id, access.subscription.get("plan", "TRIAL"))
    staff.is_active = active
    user = await _linked_user(db, staff)
    if user:
        user.status = "ACTIVE" if active else "DISABLED"
    await _audit(db, cu, request, "STAFF_ACTIVATED" if active else "STAFF_DEACTIVATED", staff, {})
    await _commit(db)
    return _out(staff)


@router.post("/{staff_id}/activate", response_model=StaffOut)
async def activate_staff(staff_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db),
                         cu: CurrentUser = Depends(manage_staff)):
    return await _set_active(staff_id, True, request, db, cu)


@router.post("/{staff_id}/deactivate", response_model=StaffOut)
async def deactivate_staff(staff_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db),
                           cu: CurrentUser = Depends(manage_staff)):
    return await _set_active(staff_id, False, request, db, cu)


@router.post("/{staff_id}/reset-password", status_code=204)
async def reset_staff_password(
    staff_id: uuid.UUID, payload: StaffPasswordReset, request: Request,
    db: AsyncSession = Depends(get_db), cu: CurrentUser = Depends(manage_staff),
):
    await _access(db, cu, "POST")
    staff = await _get_staff(db, cu.tenant_id, staff_id)
    user = await _linked_user(db, staff)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="linked_user_not_found")
    user.password_hash = hash_password(payload.new_password)
    await _audit(db, cu, request, "STAFF_PASSWORD_RESET", staff, {})
    await db.commit()


@router.delete("/{staff_id}", status_code=204)
async def delete_staff(staff_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db),
                       cu: CurrentUser = Depends(manage_staff)):
    await _access(db, cu, "DELETE")
    await _lock_tenant(db, cu.tenant_id)
    staff = await _get_staff(db, cu.tenant_id, staff_id)
    user = await _linked_user(db, staff)
    if user:
        user.status = "DELETED"
    await _audit(db, cu, request, "STAFF_DELETED", staff, {"name": staff.name})
    await db.delete(staff)
    await _commit(db)