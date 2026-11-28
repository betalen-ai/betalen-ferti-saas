"""Subscription enforcement service (spec v2, sections 5 & 6).

Computes subscription/tenant access live from the database (never trusts JWT),
caches briefly, and produces the warning headers / block decisions used by the
request middleware.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sa_text

from app.config import settings
from app.db import get_db
from app.models.org_user import User
from app.models.subscription import TenantSubscription
from app.models.tenant import Tenant
from app.models.v2 import SubscriptionPlan, Staff

ADMIN_ROLES = {"SUPER_ADMIN", "SUPPORT", "REVIEWER"}

# Exempt endpoints that always work for an authenticated tenant even when
# the subscription is EXPIRED (spec 6.3).
EXEMPT_PREFIXES = (
    "/auth/",
    "/subscription/",
    "/billing/",
    "/notifications/",
    "/support/",
)


class AccessResult:
    __slots__ = (
        "allowed", "status_code", "error_code", "error_title", "error_detail",
        "subscription", "tenant", "warning", "headers",
    )

    def __init__(
        self,
        *,
        allowed: bool,
        status_code: int = 200,
        error_code: str | None = None,
        error_title: str | None = None,
        error_detail: str | None = None,
        subscription: dict[str, Any] | None = None,
        tenant: dict[str, Any] | None = None,
        warning: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.allowed = allowed
        self.status_code = status_code
        self.error_code = error_code
        self.error_title = error_title
        self.error_detail = error_detail
        self.subscription = subscription or {}
        self.tenant = tenant or {}
        self.warning = warning
        self.headers = headers or {}


def _platform_setting(db: AsyncSession, key: str, default: str) -> str:
    row = db.execute(
        sa_text("SELECT value FROM org.platform_settings WHERE key = :k"), {"k": key}
    ).scalar_one_or_none()
    return row if row is not None else default


def _warning_thresholds(days_left: int | None) -> str | None:
    """Return warning label for the given days-left (spec 6.4 thresholds)."""
    if days_left is None:
        return None
    thresholds = (30, 15, 7, 3, 1, 0)
    for t in thresholds:
        if days_left == t:
            return "TRIAL_ENDING" if days_left <= 30 else "RENEWAL_DUE"
    return None


async def evaluate_access(
    *,
    db: AsyncSession,
    tenant_id: UUID,
    role: str,
    path: str,
    method: str,
) -> AccessResult:
    if role in ADMIN_ROLES:
        return AccessResult(allowed=True, role="admin")

    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if tenant is None:
        return AccessResult(
            allowed=False, status_code=404, error_code="TENANT_NOT_FOUND",
            error_title="Tenant not found", error_detail="No tenant found for this user",
        )

    tenant_status = tenant.status
    if tenant_status == "SUSPENDED":
        return AccessResult(
            allowed=False, status_code=403, error_code="TENANT_SUSPENDED",
            error_title="Account suspended",
            error_detail="Your account is suspended. Contact support.",
            tenant={"id": str(tenant_id), "status": tenant_status},
            headers={"X-Tenant-Status": tenant_status},
        )
    if tenant_status == "CLOSED":
        return AccessResult(
            allowed=False, status_code=403, error_code="TENANT_CLOSED",
            error_title="Account closed",
            error_detail="Your account is closed. Start a new registration.",
            tenant={"id": str(tenant_id), "status": tenant_status},
            headers={"X-Tenant-Status": tenant_status},
        )

    # Load current subscription (spec 6.2 step 4).
    sub = (
        await db.execute(
            select(TenantSubscription).where(TenantSubscription.tenant_id == tenant_id)
            .order_by(TenantSubscription.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    # Compute status live from dates (spec 5.3: status computed at request time).
    now = datetime.now(timezone.utc)
    sub_status = sub.status if sub else "EXPIRED"
    plan_code = sub.plan_id if sub else "TRIAL"
    days_left = None
    warning = None
    expired_at = None

    if sub:
        period_end = sub.current_period_end
        if period_end and period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=timezone.utc)

        if sub_status == "TRIAL" and sub.trial_ends_at:
            trial_end = sub.trial_ends_at
            if trial_end.tzinfo is None:
                trial_end = trial_end.replace(tzinfo=timezone.utc)
            if now > trial_end:
                sub_status = "GRACE"
            else:
                delta = trial_end - now
                days_left = max(0, delta.days)
                warning = _warning_thresholds(days_left)
        elif sub_status in ("ACTIVE", "CANCELLED") and period_end:
            if now > period_end:
                sub_status = "EXPIRED"
            else:
                delta = period_end - now
                days_left = max(0, delta.days)
                warning = _warning_thresholds(days_left)
        elif sub_status == "GRACE" and sub.grace_ends_at:
            grace_end = sub.grace_ends_at
            if grace_end.tzinfo is None:
                grace_end = grace_end.replace(tzinfo=timezone.utc)
            if now > grace_end:
                sub_status = "EXPIRED"
            else:
                delta = grace_end - now
                days_left = max(0, delta.days)
                warning = "GRACE"
        elif sub_status == "EXPIRED":
            expired_at = period_end

    # Exempt endpoints (spec 6.3): always allow for authenticated tenant.
    if any(path.startswith(p) for p in EXEMPT_PREFIXES) or method == "GET":
        allowed = True
    else:
        # Evaluate subscription (spec 6.2 step 6).
        if sub_status in ("TRIAL", "ACTIVE"):
            allowed = True
        elif sub_status == "GRACE":
            allowed = True
        elif sub_status == "EXPIRED":
            allowed = method == "GET"
        else:
            allowed = False

    # Build headers (spec 6.4 channel 1).
    headers: dict[str, str] = {}
    if sub:
        headers["X-Subscription-Status"] = sub_status
        headers["X-Subscription-Plan"] = plan_code
        if days_left is not None:
            headers["X-Subscription-Days-Left"] = str(days_left)
        if warning:
            headers["X-Subscription-Warning"] = warning
    headers["X-Tenant-Status"] = tenant_status

    subscription_payload = {
        "status": sub_status,
        "plan": plan_code,
        "days_left": days_left,
        "trial_ends_at": sub.trial_ends_at.isoformat() if sub and sub.trial_ends_at else None,
        "current_period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
        "grace_ends_at": sub.grace_ends_at.isoformat() if sub and sub.grace_ends_at else None,
        "expired_at": expired_at.isoformat() if expired_at else None,
    }

    if not allowed:
        return AccessResult(
            allowed=False, status_code=402, error_code="SUBSCRIPTION_EXPIRED",
            error_title="Subscription expired",
            error_detail="Your subscription has expired. Renew to continue.",
            subscription=subscription_payload,
            tenant={"id": str(tenant_id), "status": tenant_status},
            warning=warning,
            headers={
                **headers,
                "X-Subscription-Warning": "EXPIRED",
            },
        )

    return AccessResult(
        allowed=True,
        subscription=subscription_payload,
        tenant={"id": str(tenant_id), "status": tenant_status},
        warning=warning,
        headers=headers,
    )


async def check_staff_seats(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    plan_max_staff: int,
) -> AccessResult:
    current = (
        await db.execute(
            select(Staff).where(Staff.tenant_id == tenant_id, Staff.is_active == True)  # noqa: E712
        )
    ).scalars().all()
    if len(current) >= plan_max_staff:
        return AccessResult(
            allowed=False, status_code=403, error_code="SUBSCRIPTION_SEATS_EXCEEDED",
            error_title="Staff seat limit reached",
            error_detail=f"This plan allows {plan_max_staff} staff. Upgrade to add more.",
            subscription={"max_staff": plan_max_staff, "seats_used": len(current)},
        )
    return AccessResult(allowed=True)