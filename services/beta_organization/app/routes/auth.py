from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import re
import secrets
from datetime import date, timedelta

from app.config import settings
from app.db import get_db
from app.models.tenant import Tenant
from app.models.org_user import OrgUser
from app.models.subscription import Subscription
from app.schemas.auth import (
    LoginRequest, TokenResponse, SignupRequest, SignupResponse,
    RefreshRequest, LogoutRequest,
)
from app.services.auth_service import authenticate_user, create_access_token, verify_password, hash_password
from app.services.refresh_service import (
    issue_refresh_token, rotate_refresh_token, revoke_refresh_token, REFRESH_DAYS,
)

router = APIRouter()

COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME, token,
        httponly=True,
        samesite="lax",
        secure=not getattr(settings, "DEBUG", True),  # True in production (HTTPS)
        path="/auth",
        max_age=REFRESH_DAYS * 86400,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    tenant = None
    tenant_identifier = payload.tenant_id or payload.subdomain

    if tenant_identifier:
        try:
            tenant_uuid = uuid.UUID(tenant_identifier)
            tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))).scalar_one_or_none()
        except ValueError:
            tenant = (await db.execute(select(Tenant).where(Tenant.subdomain == tenant_identifier))).scalar_one_or_none()

        if not tenant or tenant.status != "active":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

        user = await authenticate_user(
            db, tenant_id=tenant.id, email=str(payload.email), password=payload.password
        )
    else:
        result = await db.execute(select(OrgUser).where(OrgUser.email == str(payload.email), OrgUser.status == "active"))
        user = result.scalar_one_or_none()
        if user and not verify_password(payload.password, user.password_hash):
            user = None

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, email=user.email)
    refresh = await issue_refresh_token(db, user_id=user.id, tenant_id=user.tenant_id)
    _set_refresh_cookie(response, refresh)
    return TokenResponse(
        access_token=token,
        refresh_token=refresh,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


async def _unique_subdomain(db: AsyncSession, shop_name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", shop_name.lower()).strip("-")[:30] or "shop"
    candidate = base
    for _ in range(6):
        taken = (await db.execute(select(Tenant.id).where(Tenant.subdomain == candidate).limit(1))).scalar_one_or_none()
        if not taken:
            return candidate
        candidate = f"{base[:35]}-{secrets.token_hex(2)}"
    raise HTTPException(status.HTTP_409_CONFLICT, detail="subdomain_unavailable")


@router.post("/signup", response_model=SignupResponse, status_code=201)
async def signup(payload: SignupRequest, response: Response, db: AsyncSession = Depends(get_db)):
    email = str(payload.email).lower()

    # Sanitize mobile: keep digits only, strip leading 91 if present
    clean_mobile = re.sub(r"\D", "", payload.mobile)
    if clean_mobile.startswith("91") and len(clean_mobile) > 10:
        clean_mobile = clean_mobile[2:]

    if len(clean_mobile) != 10 or not re.match(r"^[6-9]", clean_mobile):
        raise HTTPException(status_code=422, detail="Invalid mobile number format. Must be 10 digits starting with 6-9.")

    exists = (await db.execute(select(OrgUser.id).where(OrgUser.email == email).limit(1))).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email_already_registered")

    subdomain = await _unique_subdomain(db, payload.shop_name)

    tenant = Tenant(name=payload.shop_name, subdomain=subdomain, subscription_plan="BASIC", status="active")
    db.add(tenant)
    await db.flush()

    today = date.today()
    subscription = Subscription(
        tenant_id=tenant.id, plan="BASIC", status="active",
        valid_from=today, valid_to=today + timedelta(days=365),
    )
    user = OrgUser(
        tenant_id=tenant.id, email=email, password_hash=hash_password(payload.password),
        full_name=payload.owner_name, status="active",
    )

    if hasattr(user, "phone"):
        setattr(user, "phone", f"+91{clean_mobile}")
    elif hasattr(user, "mobile"):
        setattr(user, "mobile", f"+91{clean_mobile}")

    db.add_all([subscription, user])
    await db.commit()

    token = create_access_token(user_id=user.id, tenant_id=tenant.id, email=user.email)
    refresh = await issue_refresh_token(db, user_id=user.id, tenant_id=tenant.id)
    _set_refresh_cookie(response, refresh)
    return SignupResponse(
        access_token=token,
        refresh_token=refresh,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    raw = (payload.refresh_token if payload else None) or request.cookies.get(COOKIE_NAME)
    if not raw:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")

    rotated = await rotate_refresh_token(db, raw)
    if not rotated:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")
    old_session, new_raw = rotated

    user = (await db.execute(
        select(OrgUser).where(OrgUser.id == old_session.user_id, OrgUser.status == "active")
    )).scalar_one_or_none()
    tenant = (await db.execute(
        select(Tenant).where(Tenant.id == old_session.tenant_id)
    )).scalar_one_or_none()
    if not user or not tenant or tenant.status != "active":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")

    access = create_access_token(user_id=user.id, tenant_id=user.tenant_id, email=user.email)
    _set_refresh_cookie(response, new_raw)
    return TokenResponse(
        access_token=access,
        refresh_token=new_raw,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    payload: LogoutRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    raw = (payload.refresh_token if payload else None) or request.cookies.get(COOKIE_NAME)
    if raw:
        await revoke_refresh_token(db, raw)
    response.delete_cookie(COOKIE_NAME, path="/auth")