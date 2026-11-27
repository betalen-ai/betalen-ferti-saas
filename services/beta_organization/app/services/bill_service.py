import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bill import Bill, BillItem
from app.services.crud_base import get_owned


async def list_bills(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    farmer_id: uuid.UUID | None = None,
    season_id: uuid.UUID | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(Bill).where(Bill.tenant_id == tenant_id)
    if farmer_id:
        query = query.where(Bill.farmer_id == farmer_id)
    if season_id:
        query = query.where(Bill.season_id == season_id)
    if q:
        query = query.where(Bill.bill_number.ilike(f"%{q}%"))
    result = await db.execute(
        query.order_by(Bill.bill_date.desc(), Bill.created_at.desc()).limit(limit).offset(offset)
    )
    return result.scalars().all()


async def get_bill(db: AsyncSession, tenant_id: uuid.UUID, bill_id: uuid.UUID) -> Bill:
    return await get_owned(db, Bill, bill_id, tenant_id, "bill_not_found")


async def list_bill_items(db: AsyncSession, tenant_id: uuid.UUID, bill_id: uuid.UUID):
    await get_owned(db, Bill, bill_id, tenant_id, "bill_not_found")
    result = await db.execute(
        select(BillItem)
        .where(BillItem.bill_id == bill_id, BillItem.tenant_id == tenant_id)
        .order_by(BillItem.created_at)
    )
    return result.scalars().all()