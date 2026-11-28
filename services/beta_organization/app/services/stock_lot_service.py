import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pack import Pack
from app.models.stock_lot import StockLot
from app.models.stock_movement import StockMovement
from app.schemas.stock_lot import StockLotCreate, StockLotUpdate
from app.services.crud_base import commit_or_conflict, ensure_same_tenant, get_owned


async def list_lots(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    pack_id: uuid.UUID | None = None,
    in_stock_only: bool = False,
    expiring_before: date | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(StockLot).where(StockLot.tenant_id == tenant_id)
    if pack_id:
        query = query.where(StockLot.pack_id == pack_id)
    if in_stock_only:
        query = query.where(StockLot.available_base > 0)
    if expiring_before:
        query = query.where(StockLot.expiry_date.is_not(None), StockLot.expiry_date <= expiring_before)
    result = await db.execute(
        query.order_by(StockLot.expiry_date.asc().nulls_last(), StockLot.received_date).limit(limit).offset(offset)
    )
    return result.scalars().all()


async def create_lot(db: AsyncSession, tenant_id: uuid.UUID, payload: StockLotCreate) -> StockLot:
    await ensure_same_tenant(db, Pack, payload.pack_id, tenant_id, "pack_id")
    lot = StockLot(
        tenant_id=tenant_id,
        available_base=payload.quantity_base,
        **payload.model_dump(exclude={"tenant_id"}),
    )
    db.add(lot)
    await db.flush()
    db.add(
        StockMovement(
            tenant_id=tenant_id,
            pack_id=lot.pack_id,
            stock_lot_id=lot.id,
            movement_type="receipt",
            quantity_base=lot.quantity_base,
            source_id=lot.id,
            source_type="stock_lot",
        )
    )
    await commit_or_conflict(db, "stock_lot_conflict")
    await db.refresh(lot)
    return lot


async def update_lot(db: AsyncSession, tenant_id: uuid.UUID, lot_id: uuid.UUID, payload: StockLotUpdate) -> StockLot:
    lot = await get_owned(db, StockLot, lot_id, tenant_id, "stock_lot_not_found")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"tenant_id"}).items():
        setattr(lot, field, value)
    lot.version += 1
    await commit_or_conflict(db, "stock_lot_conflict")
    await db.refresh(lot)
    return lot