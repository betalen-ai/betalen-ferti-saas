import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services import product_service
from app.services.crud_base import resolve_request_tenant

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(
    tenant_id: uuid.UUID | None = Query(default=None),
    brand_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    include_inactive: bool = False,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.list_products(
        db, resolve_tenant_id(cu, tenant_id),
        brand_id=brand_id, category_id=category_id,
        include_inactive=include_inactive, q=q, limit=limit, offset=offset,
    )


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.get_product(db, resolve_tenant_id(cu, tenant_id), product_id)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await product_service.create_product(db, owned, payload)


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await product_service.update_product(db, owned, product_id, payload)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_product(
    product_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await product_service.deactivate_product(db, resolve_tenant_id(cu, tenant_id), product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)