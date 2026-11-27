import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_lot import StockLot
from app.models.stock_movement import StockMovement
from app.schemas.stock_movement import StockMovementCreate
from app.services.crud_base import commit_or_conflict, not_found


async def list_movements(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    pack_id: uuid.UUID | None = None,
    stock_lot_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(StockMovement).where(StockMovement.tenant_id == tenant_id)
    if pack_id:
        query = query.where(StockMovement.pack_id == pack_id)
    if stock_lot_id:
        query = query.where(StockMovement.stock_lot_id == stock_lot_id)
    result = await db.execute(query.order_by(StockMovement.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


async def create_movement(db: AsyncSession, tenant_id: uuid.UUID, payload: StockMovementCreate) -> StockMovement:
    result = await db.execute(
        select(StockLot)
        .where(StockLot.id == payload.stock_lot_id, StockLot.tenant_id == tenant_id)
        .with_for_update()
    )
    lot = result.scalar_one_or_none()
    if lot is None:
        raise not_found("stock_lot_not_found")
    new_available = lot.available_base + payload.quantity_base
    if new_available < 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="insufficient_stock")
    lot.available_base = new_available
    lot.version += 1
    movement = StockMovement(
        tenant_id=tenant_id,
        pack_id=lot.pack_id,
        stock_lot_id=lot.id,
        movement_type=payload.movement_type,
        quantity_base=payload.quantity_base,
        reason=payload.reason,
        source_type="manual",
    )
    db.add(movement)
    await commit_or_conflict(db, "stock_movement_conflict")
    await db.refresh(movement)
    return movement