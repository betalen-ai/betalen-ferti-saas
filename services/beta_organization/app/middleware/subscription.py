"""Subscription enforcement middleware (spec v2, section 6).

Checks tenant status and subscription on every request. Adds warning headers
to responses and returns 402/403 when access is blocked.
"""
from __future__ import annotations

from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.db import SessionLocal
from app.models.org_user import User
from app.models.subscription import TenantSubscription
from app.models.tenant import Tenant
from app.models.v2 import Staff
from app.services.auth_service import decode_token
from app.services.subscription_service import ADMIN_ROLES, evaluate_access, EXEMPT_PREFIXES

# Paths that don't require tenant/subscription enforcement
PUBLIC_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/register",
    "/api/v1/auth/otp/send",
    "/api/v1/auth/otp/verify",
)


class SubscriptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        method = request.method

        # Public paths: no enforcement
        if any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        # Extract token
        auth = request.headers.get("authorization", "")
        tenant_id = None
        role = None
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
            try:
                claims = decode_token(token)
                tenant_id = claims.get("tid")
                role = claims.get("role")
            except Exception:
                # Invalid token - let the route handler return 401
                return await call_next(request)

        # Admin tokens: skip subscription check (spec 6.2 step 3)
        if role in ADMIN_ROLES:
            response = await call_next(request)
            return response

        # No valid token: let route handler deal with auth
        if tenant_id is None:
            return await call_next(request)

        from uuid import UUID
        try:
            tid = UUID(tenant_id)
        except (ValueError, AttributeError):
            return await call_next(request)

        async with SessionLocal() as db:
            access = await evaluate_access(
                db, tenant_id=tid, role=role or "TENANT", path=path, method=method,
            )

        if not access.allowed:
            return JSONResponse(
                status_code=access.status_code,
                content={
                    "code": access.error_code,
                    "title": access.error_title,
                    "detail": access.error_detail,
                    "subscription": access.subscription,
                    "action": {"label": "Renew now", "route": "/billing"},
                },
                headers=access.headers,
            )

        response = await call_next(request)
        # Add subscription headers to every response (spec 6.4 channel 1)
        for key, value in access.headers.items():
            response.headers[key] = value
        return response