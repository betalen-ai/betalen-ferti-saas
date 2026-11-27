import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import CurrentUser, resolve_tenant_id


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def resolve_request_tenant(
    cu: CurrentUser,
    query_tenant_id: uuid.UUID | None,
    payload_tenant_id: uuid.UUID | None = None,
) -> uuid.UUID:
    if query_tenant_id and payload_tenant_id and query_tenant_id != payload_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id_mismatch")
    return resolve_tenant_id(cu, payload_tenant_id or query_tenant_id)


async def get_owned(db: AsyncSession, model: Any, obj_id: uuid.UUID, tenant_id: uuid.UUID, detail: str):
    result = await db.execute(select(model).where(model.id == obj_id, model.tenant_id == tenant_id))
    obj = result.scalar_one_or_none()
    if obj is None:
        raise not_found(detail)
    return obj


async def ensure_same_tenant(
    db: AsyncSession, model: Any, obj_id: uuid.UUID | None, tenant_id: uuid.UUID, field: str
) -> None:
    if obj_id is None:
        return
    found = await db.scalar(select(model.id).where(model.id == obj_id, model.tenant_id == tenant_id))
    if found is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"invalid_{field}")


async def commit_or_conflict(db: AsyncSession, detail: str) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc