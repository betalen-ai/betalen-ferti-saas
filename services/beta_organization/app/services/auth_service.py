import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.org_user import OrgUser
from app.models.permission import Permission, RolePermission
from app.models.role import Role


pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_access_token(*, user_id: uuid.UUID, tenant_id: uuid.UUID, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError(f"invalid token: {exc}") from exc


async def authenticate_user(
    db: AsyncSession, *, tenant_id: uuid.UUID, email: str, password: str
) -> OrgUser | None:
    result = await db.execute(
        select(OrgUser).where(
            OrgUser.tenant_id == tenant_id,
            OrgUser.email == email,
            OrgUser.status == "active",
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


async def load_user_permissions(db: AsyncSession, *, user: OrgUser) -> tuple[str | None, list[str]]:
    if not user.role_id:
        return None, []
    role = (await db.execute(select(Role).where(Role.id == user.role_id))).scalar_one_or_none()
    if not role:
        return None, []
    perm_rows = await db.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role.id)
    )
    perms = [f"{p.resource}:{p.action}" for p in perm_rows.scalars().all()]
    return role.name, perms