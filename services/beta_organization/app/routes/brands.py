import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.brand import BrandCreate, BrandOut, BrandUpdate
from app.services import brand_service
from app.services.crud_base import resolve_request_tenant

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("", response_model=list[BrandOut])
async def list_brands(
    tenant_id: uuid.UUID | None = Query(default=None),
    include_inactive: bool = False,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await brand_service.list_brands(
        db, resolve_tenant_id(cu, tenant_id),
        include_inactive=include_inactive, q=q, limit=limit, offset=offset,
    )


@router.get("/{brand_id}", response_model=BrandOut)
async def get_brand(
    brand_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await brand_service.get_brand(db, resolve_tenant_id(cu, tenant_id), brand_id)


@router.post("", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
async def create_brand(
    payload: BrandCreate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await brand_service.create_brand(db, owned, payload)


@router.patch("/{brand_id}", response_model=BrandOut)
async def update_brand(
    brand_id: uuid.UUID,
    payload: BrandUpdate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await brand_service.update_brand(db, owned, brand_id, payload)


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_brand(
    brand_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await brand_service.deactivate_brand(db, resolve_tenant_id(cu, tenant_id), brand_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)