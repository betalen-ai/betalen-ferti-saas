import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.khata import KhataEntry
from app.services.crud_base import get_owned


async def list_khata_entries(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    farmer_id: uuid.UUID | None = None,
    bill_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(KhataEntry).where(KhataEntry.tenant_id == tenant_id)
    if farmer_id:
        query = query.where(KhataEntry.farmer_id == farmer_id)
    if bill_id:
        query = query.where(KhataEntry.bill_id == bill_id)
    result = await db.execute(query.order_by(KhataEntry.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


async def get_khata_entry(db: AsyncSession, tenant_id: uuid.UUID, entry_id: uuid.UUID) -> KhataEntry:
    return await get_owned(db, KhataEntry, entry_id, tenant_id, "khata_entry_not_found")