import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.models.stock_lot import StockLot
from app.schemas.stock_lot import StockLotCreate, StockLotOut, StockLotUpdate
from app.services import stock_lot_service
from app.services.crud_base import get_owned, resolve_request_tenant

router = APIRouter(prefix="/stock-lots", tags=["stock"])


@router.get("", response_model=list[StockLotOut])
async def list_lots(
    tenant_id: uuid.UUID | None = Query(default=None),
    pack_id: uuid.UUID | None = None,
    in_stock_only: bool = False,
    expiring_before: date | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await stock_lot_service.list_lots(
        db, resolve_tenant_id(cu, tenant_id),
        pack_id=pack_id, in_stock_only=in_stock_only,
        expiring_before=expiring_before, limit=limit, offset=offset,
    )


@router.post("", response_model=StockLotOut, status_code=status.HTTP_201_CREATED)
async def create_lot(
    payload: StockLotCreate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await stock_lot_service.create_lot(
        db, resolve_request_tenant(cu, tenant_id, payload.tenant_id), payload
    )


@router.get("/{lot_id}", response_model=StockLotOut)
async def get_lot(
    lot_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_owned(db, StockLot, lot_id, resolve_tenant_id(cu, tenant_id), "stock_lot_not_found")


@router.patch("/{lot_id}", response_model=StockLotOut)
async def update_lot(
    lot_id: uuid.UUID,
    payload: StockLotUpdate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await stock_lot_service.update_lot(
        db, resolve_request_tenant(cu, tenant_id, payload.tenant_id), lot_id, payload
    )