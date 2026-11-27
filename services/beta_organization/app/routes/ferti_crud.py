"""Tenant-scoped helpers and generic CRUD router factory for ferti.* tables.

Every query filters on tenant_id. Every foreign key supplied by the client is
verified to belong to the same tenant before it is written.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def resolve_request_tenant(
    cu: CurrentUser,
    query_tenant_id: uuid.UUID | None,
    payload_tenant_id: uuid.UUID | None = None,
) -> uuid.UUID:
    if query_tenant_id and payload_tenant_id and query_tenant_id != payload_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id_mismatch",
        )
    return resolve_tenant_id(cu, payload_tenant_id or query_tenant_id)


async def get_owned(
    db: AsyncSession,
    model: Any,
    obj_id: uuid.UUID,
    tenant_id: uuid.UUID,
    detail: str,
):
    result = await db.execute(
        select(model).where(model.id == obj_id, model.tenant_id == tenant_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise not_found(detail)
    return obj


async def ensure_same_tenant(
    db: AsyncSession,
    model: Any,
    obj_id: uuid.UUID | None,
    tenant_id: uuid.UUID,
    field: str,
) -> None:
    """Reject a foreign key that points at another tenant's row."""
    if obj_id is None:
        return

    found = await db.scalar(
        select(model.id).where(model.id == obj_id, model.tenant_id == tenant_id)
    )
    if found is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid_{field}",
        )


async def commit_or_conflict(db: AsyncSession, detail: str) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        ) from exc


def build_crud_router(
    *,
    prefix: str,
    tag: str,
    model: Any,
    create_schema: Any,
    update_schema: Any | None,
    out_schema: Any,
    not_found_detail: str,
    conflict_detail: str,
    order_by: list[Any],
    fk_checks: dict[str, Any] | None = None,
    search_columns: list[Any] | None = None,
    writable: bool = True,
    soft_delete: bool = False,
    nullable_fields: frozenset[str] = frozenset(),
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])
    fk_checks = fk_checks or {}
    search_columns = search_columns or []
    has_active = hasattr(model, "active")

    @router.get("", response_model=list[out_schema])
    async def list_items(
        request: Request,
        tenant_id: uuid.UUID | None = Query(default=None),
        include_inactive: bool = False,
        q: str | None = Query(default=None, max_length=100),
        limit: int = Query(default=100, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        cu: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        owned = resolve_tenant_id(cu, tenant_id)
        query = select(model).where(model.tenant_id == owned)

        if has_active and not include_inactive:
            query = query.where(model.active.is_(True))

        for field in fk_checks:
            raw = request.query_params.get(field)
            if raw:
                try:
                    query = query.where(getattr(model, field) == uuid.UUID(raw))
                except ValueError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"invalid_{field}",
                    ) from exc

        if q and search_columns:
            query = query.where(
                or_(*[column.ilike(f"%{q}%") for column in search_columns])
            )

        result = await db.execute(
            query.order_by(*order_by).limit(limit).offset(offset)
        )
        return result.scalars().all()

    @router.get("/{item_id}", response_model=out_schema)
    async def get_item(
        item_id: uuid.UUID,
        tenant_id: uuid.UUID | None = Query(default=None),
        cu: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        owned = resolve_tenant_id(cu, tenant_id)
        return await get_owned(db, model, item_id, owned, not_found_detail)

    # Read-only resources (bills, payments, ledgers, audit logs) stop here.
    if not writable:
        return router

    @router.post("", response_model=out_schema, status_code=status.HTTP_201_CREATED)
    async def create_item(
        payload: create_schema,
        tenant_id: uuid.UUID | None = Query(default=None),
        cu: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
        data = payload.model_dump(exclude={"tenant_id"})

        for field, ref_model in fk_checks.items():
            await ensure_same_tenant(db, ref_model, data.get(field), owned, field)

        obj = model(tenant_id=owned, **data)
        db.add(obj)
        await commit_or_conflict(db, conflict_detail)
        await db.refresh(obj)
        return obj

    if update_schema is not None:

        @router.patch("/{item_id}", response_model=out_schema)
        async def update_item(
            item_id: uuid.UUID,
            payload: update_schema,
            tenant_id: uuid.UUID | None = Query(default=None),
            cu: CurrentUser = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
        ):
            owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
            obj = await get_owned(db, model, item_id, owned, not_found_detail)

            raw = payload.model_dump(
                exclude_unset=True,
                exclude={"tenant_id"},
            )
            changes = {
                key: value
                for key, value in raw.items()
                if value is not None or key in nullable_fields
            }

            for field, ref_model in fk_checks.items():
                if field in changes:
                    await ensure_same_tenant(
                        db, ref_model, changes[field], owned, field
                    )

            for field, value in changes.items():
                setattr(obj, field, value)

            if hasattr(obj, "version"):
                obj.version += 1

            await commit_or_conflict(db, conflict_detail)
            await db.refresh(obj)
            return obj

    if soft_delete and has_active:

        @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
        async def deactivate_item(
            item_id: uuid.UUID,
            tenant_id: uuid.UUID | None = Query(default=None),
            cu: CurrentUser = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
        ):
            owned = resolve_tenant_id(cu, tenant_id)
            obj = await get_owned(db, model, item_id, owned, not_found_detail)
            obj.active = False

            if hasattr(obj, "version"):
                obj.version += 1

            await db.commit()
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
