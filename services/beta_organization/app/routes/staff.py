"""Staff management routes (spec v2, section 7)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.org_user import User
from app.models.onboarding import AuthEvent
from app.models.tenant import Tenant
from app.models.v2 import Staff, SubscriptionPlan, TenantSubscription
from app.schemas.staff import StaffCreate, StaffOut, StaffListOut, StaffUpdate
from app.services.auth_service import hash_password
from app.services.audit_service import write_audit_log, write_auth_event
from app.services.subscription_service import check_staff_seats, evaluate_access

router = APIRouter()


async def _current_user(
    authorization: str | None = None,
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing_bearer_token")
    token = authorization.split(" ", 1)[1]
    from app.services.auth_service import decode_token
    try:
        claims = decode_token(token)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    return {
        "user_id": claims.get("sub"),
        "tenant_id": claims.get("tid"),
        "role": claims.get("role", "TENANT"),
        "permissions": claims.get("permissions", []),
    }


@router.post("", response_model=StaffOut, status_code=201)
async def create_staff(
    payload: StaffCreate, request: Request, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(_current_user),
):
    tenant_id = current_user["tenant_id"]
    role = current_user["role"]

    access = await evaluate_access(db, tenant_id=tenant_id, role=role, path="/staff", method="POST")
    if not access.allowed:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, detail=access.error_code)

    plan = (
        await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == access.subscription.get("plan", "TRIAL")))
    ).scalar_one_or_none()
    max_staff = plan.max_staff if plan else 2
    seat_check = await check_staff_seats(db, tenant_id=tenant_id, plan_max_staff=max_staff)
    if not seat_check.allowed:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=seat_check.error_code)

    staff = Staff(
        tenant_id=tenant_id,
        name=payload.name,
        mobile=payload.mobile,
        email=payload.email,
        role_template=payload.role_template,
        permissions=payload.permissions,
        is_active=payload.is_active,
    )
    db.add(staff)
    await db.flush()

    user = User(
        tenant_id=tenant_id,
        role="STAFF",
        name=payload.name,
        email=payload.email,
        phone=payload.mobile,
        permissions=payload.permissions,
        status="ACTIVE",
        created_by=uuid.UUID(current_user["user_id"]) if current_user.get("user_id") else None,
    )
    db.add(user)
    await db.flush()

    await write_audit_log(
        db, tenant_id=tenant_id,
        actor_user_id=uuid.UUID(current_user["user_id"]) if current_user.get("user_id") else None,
        actor_type="TENANT", action="STAFF_CREATED", entity_name="staff", entity_id=staff.id,
        payload={"name": payload.name, "role_template": payload.role_template},
        ip=request.client.host if request.client else None,
        request_id=request.headers.get("x-request-id"),
    )
    await write_auth_event(
        db, tenant_id=tenant_id, user_id=user.id, identifier=payload.mobile or payload.email or "",
        method="PASSWORD", event_type="STAFF_CREATED", success=True,
        failure_reason=None, request=request,
    )
    await db.commit()

    return StaffOut(
        id=staff.id, tenant_id=staff.tenant_id, role="STAFF", name=staff.name,
        mobile=staff.mobile, email=staff.email, role_template=staff.role_template,
        permissions=staff.permissions, is_active=staff.is_active, status="ACTIVE",
        created_at=staff.created_at, updated_at=staff.updated_at,
    )


@router.get("", response_model=StaffListOut)
async def list_staff(
    request: Request, db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(_current_user),
):
    tenant_id = current_user["tenant_id"]
    role = current_user["role"]

    access = await evaluate_access(db, tenant_id=tenant_id, role=role, path="/staff", method="GET")
    if not access.allowed:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, detail=access.error_code)

    rows = (
        await db.execute(select(Staff).where(Staff.tenant_id == tenant_id).order_by(Staff.created_at.desc()))
    ).scalars().all()
    plan = (
        await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == access.subscription.get("plan", "TRIAL")))
    ).scalar_one_or_none()
    max_staff = plan.max_staff if plan else 2

    return StaffListOut(
        staff=[
            StaffOut(
                id=s.id, tenant_id=s.tenant_id, role="STAFF", name=s.name,
                mobile=s.mobile, email=s.email, role_template=s.role_template,
                permissions=s.permissions, is_active=s.is_active,
                status="ACTIVE" if s.is_active else "DISABLED",
                created_at=s.created_at, updated_at=s.updated_at,
            ) for s in rows
        ],
        total=len(rows),
        seats_used=len(rows),
        seats_available=max(0, max_staff - len(rows)),
    )