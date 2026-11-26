"""Shared auth dependencies. Every router should use these instead of raw headers."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from fastapi import Depends, Header, HTTPException, Query, status

from app.services.auth_service import decode_token


@dataclass
class CurrentUser:
    user_id: uuid.UUID | None
    tenant_id: uuid.UUID | None
    role: str
    permissions: list[str] = field(default_factory=list)

    @property
    def is_super_admin(self) -> bool:
        return self.tenant_id is None or self.role == "SUPER_ADMIN"


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing_bearer_token")
    try:
        claims = decode_token(authorization.split(" ", 1)[1])
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    try:
        uid = uuid.UUID(str(claims["sub"])) if claims.get("sub") else None
        tid = uuid.UUID(str(claims["tid"])) if claims.get("tid") else None
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    return CurrentUser(uid, tid, claims.get("role", "TENANT"), claims.get("permissions", []))


async def require_tenant_user(cu: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if cu.tenant_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="tenant_required")
    return cu


async def require_super_admin(cu: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not cu.is_super_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="super_admin_required")
    return cu


def require_roles(*roles: str):
    async def _dep(cu: CurrentUser = Depends(require_tenant_user)) -> CurrentUser:
        if cu.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="insufficient_role")
        return cu
    return _dep


def require_permission(perm: str):
    async def _dep(cu: CurrentUser = Depends(require_tenant_user)) -> CurrentUser:
        if cu.role in ("TENANT", "OWNER", "ADMIN") or perm in cu.permissions:
            return cu
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"missing_permission:{perm}")
    return _dep


def resolve_tenant_id(cu: CurrentUser, tenant_id: uuid.UUID | None) -> uuid.UUID:
    """Tenant users always get their own tenant; super admins must name one."""
    if cu.tenant_id is not None and not cu.is_super_admin:
        if tenant_id and tenant_id != cu.tenant_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="cross_tenant_forbidden")
        return cu.tenant_id
    if tenant_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="tenant_id_required")
    return tenant_id


class Page:
    def __init__(self, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
        self.limit, self.offset = limit, offset