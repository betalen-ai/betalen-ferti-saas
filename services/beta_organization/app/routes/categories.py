import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services import category_service
from app.services.crud_base import resolve_request_tenant

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(
    tenant_id: uuid.UUID | None = Query(default=None),
    include_inactive: bool = False,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await category_service.list_categories(
        db, resolve_tenant_id(cu, tenant_id),
        include_inactive=include_inactive, q=q, limit=limit, offset=offset,
    )


@router.get("/{category_id}", response_model=CategoryOut)
async def get_category(
    category_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await category_service.get_category(db, resolve_tenant_id(cu, tenant_id), category_id)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await category_service.create_category(db, owned, payload)


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await category_service.update_category(db, owned, category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_category(
    category_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await category_service.deactivate_category(db, resolve_tenant_id(cu, tenant_id), category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)