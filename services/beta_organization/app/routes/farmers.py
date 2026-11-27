import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.farmer import FarmerCreate, FarmerOut, FarmerUpdate
from app.services import farmer_service
from app.services.crud_base import resolve_request_tenant

router = APIRouter(prefix="/farmers", tags=["farmers"])


@router.get("", response_model=list[FarmerOut])
async def list_farmers(
    tenant_id: uuid.UUID | None = Query(default=None),
    include_inactive: bool = False,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await farmer_service.list_farmers(
        db, resolve_tenant_id(cu, tenant_id),
        include_inactive=include_inactive, q=q, limit=limit, offset=offset,
    )


@router.get("/{farmer_id}", response_model=FarmerOut)
async def get_farmer(
    farmer_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await farmer_service.get_farmer(db, resolve_tenant_id(cu, tenant_id), farmer_id)


@router.post("", response_model=FarmerOut, status_code=status.HTTP_201_CREATED)
async def create_farmer(
    payload: FarmerCreate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await farmer_service.create_farmer(db, owned, payload)


@router.patch("/{farmer_id}", response_model=FarmerOut)
async def update_farmer(
    farmer_id: uuid.UUID,
    payload: FarmerUpdate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await farmer_service.update_farmer(db, owned, farmer_id, payload)


@router.delete("/{farmer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_farmer(
    farmer_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await farmer_service.deactivate_farmer(db, resolve_tenant_id(cu, tenant_id), farmer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)