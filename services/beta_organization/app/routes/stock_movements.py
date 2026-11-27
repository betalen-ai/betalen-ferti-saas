import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.models.stock_movement import StockMovement
from app.schemas.stock_movement import StockMovementCreate, StockMovementOut
from app.services import stock_movement_service
from app.services.crud_base import get_owned, resolve_request_tenant

router = APIRouter(prefix="/stock-movements", tags=["stock"])


@router.get("", response_model=list[StockMovementOut])
async def list_movements(
    tenant_id: uuid.UUID | None = Query(default=None),
    pack_id: uuid.UUID | None = None,
    stock_lot_id: uuid.UUID | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await stock_movement_service.list_movements(
        db, resolve_tenant_id(cu, tenant_id),
        pack_id=pack_id, stock_lot_id=stock_lot_id, limit=limit, offset=offset,
    )


@router.get("/{movement_id}", response_model=StockMovementOut)
async def get_movement(
    movement_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_owned(
        db, StockMovement, movement_id, resolve_tenant_id(cu, tenant_id), "stock_movement_not_found"
    )


@router.post("", response_model=StockMovementOut, status_code=status.HTTP_201_CREATED)
async def create_movement(
    payload: StockMovementCreate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await stock_movement_service.create_movement(
        db, resolve_request_tenant(cu, tenant_id, payload.tenant_id), payload
    )