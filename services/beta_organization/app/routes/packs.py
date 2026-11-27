import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.pack import PackCreate, PackOut, PackUpdate
from app.services import pack_service
from app.services.crud_base import resolve_request_tenant

router = APIRouter(prefix="/packs", tags=["packs"])


@router.get("", response_model=list[PackOut])
async def list_packs(
    tenant_id: uuid.UUID | None = Query(default=None),
    product_id: uuid.UUID | None = None,
    include_inactive: bool = False,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await pack_service.list_packs(
        db, resolve_tenant_id(cu, tenant_id),
        product_id=product_id, include_inactive=include_inactive,
        q=q, limit=limit, offset=offset,
    )


@router.get("/{pack_id}", response_model=PackOut)
async def get_pack(
    pack_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await pack_service.get_pack(db, resolve_tenant_id(cu, tenant_id), pack_id)


@router.post("", response_model=PackOut, status_code=status.HTTP_201_CREATED)
async def create_pack(
    payload: PackCreate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await pack_service.create_pack(db, owned, payload)


@router.patch("/{pack_id}", response_model=PackOut)
async def update_pack(
    pack_id: uuid.UUID,
    payload: PackUpdate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await pack_service.update_pack(db, owned, pack_id, payload)


@router.delete("/{pack_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_pack(
    pack_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await pack_service.deactivate_pack(db, resolve_tenant_id(cu, tenant_id), pack_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)