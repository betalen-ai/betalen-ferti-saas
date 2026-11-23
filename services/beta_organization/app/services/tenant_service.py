import uuid
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org_user import OrgUser
from app.models.permission import Permission, RolePermission
from app.models.role import Role
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.schemas.tenant import TenantSignupRequest
from app.services.auth_service import hash_password


DEFAULT_PERMISSIONS = [
    ("invoice", "create"), ("invoice", "read"), ("invoice", "void"),
    ("payment", "create"), ("payment", "read"),
    ("customer", "create"), ("customer", "read"), ("customer", "update"),
    ("product", "create"), ("product", "read"), ("product", "update"),
    ("warehouse", "create"), ("warehouse", "read"),
    ("credit", "approve"),
    ("user", "create"), ("user", "read"), ("user", "update"),
    ("report", "read"),
    ("subscription", "read"), ("subscription", "manage"),
]

DEFAULT_ROLES = {
    "owner": {"*"},
    "manager": {
        "invoice:create", "invoice:read", "invoice:void",
        "payment:create", "payment:read",
        "customer:create", "customer:read", "customer:update",
        "product:create", "product:read", "product:update",
        "warehouse:create", "warehouse:read",
        "credit:approve", "report:read",
    },
    "cashier": {
        "invoice:create", "invoice:read",
        "payment:create", "payment:read",
        "customer:read", "product:read", "warehouse:read",
    },
}


async def _ensure_permissions(db: AsyncSession) -> dict[str, Permission]:
    existing = {f"{p.resource}:{p.action}": p for p in (await db.execute(select(Permission))).scalars()}
    for resource, action in DEFAULT_PERMISSIONS:
        key = f"{resource}:{action}"
        if key not in existing:
            perm = Permission(resource=resource, action=action)
            db.add(perm)
            await db.flush()
            existing[key] = perm
    return existing


async def _seed_roles_for_tenant(db: AsyncSession, *, tenant_id: uuid.UUID) -> dict[str, Role]:
    perms = await _ensure_permissions(db)
    created: dict[str, Role] = {}
    for role_name, perm_set in DEFAULT_ROLES.items():
        role = Role(tenant_id=tenant_id, name=role_name)
        db.add(role)
        await db.flush()
        created[role_name] = role
        for key in perm_set:
            targets = perms.values() if key == "*" else [perms[key]]
            for perm in targets:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    return created


async def signup_tenant(db: AsyncSession, payload: TenantSignupRequest) -> Tenant:
    existing = await db.execute(select(Tenant).where(Tenant.subdomain == payload.subdomain))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, detail="subdomain_taken")

    tenant = Tenant(name=payload.tenant_name, subdomain=payload.subdomain, subscription_plan="free")
    db.add(tenant)
    await db.flush()

    roles = await _seed_roles_for_tenant(db, tenant_id=tenant.id)

    owner = OrgUser(
        tenant_id=tenant.id,
        email=str(payload.owner_email),
        password_hash=hash_password(payload.owner_password),
        full_name=payload.owner_full_name,
        role_id=roles["owner"].id,
    )
    db.add(owner)

    sub = Subscription(
        tenant_id=tenant.id,
        plan="free",
        status="active",
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=365),
    )
    db.add(sub)

    await db.commit()
    await db.refresh(tenant)
    return tenant
