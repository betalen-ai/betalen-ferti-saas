import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cashbook import CashbookEntry
from app.schemas.cashbook import CashbookCreate, CashbookUpdate
from app.services.crud_base import commit_or_conflict, get_owned


async def list_cashbook(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(CashbookEntry).where(CashbookEntry.tenant_id == tenant_id)
    if q:
        query = query.where(CashbookEntry.category.ilike(f"%{q}%"))
    result = await db.execute(
        query.order_by(CashbookEntry.entry_date.desc(), CashbookEntry.created_at.desc()).limit(limit).offset(offset)
    )
    return result.scalars().all()


async def get_cashbook_entry(db: AsyncSession, tenant_id: uuid.UUID, entry_id: uuid.UUID) -> CashbookEntry:
    return await get_owned(db, CashbookEntry, entry_id, tenant_id, "cashbook_entry_not_found")


async def create_cashbook_entry(
    db: AsyncSession, tenant_id: uuid.UUID, payload: CashbookCreate
) -> CashbookEntry:
    entry = CashbookEntry(tenant_id=tenant_id, **payload.model_dump(exclude={"tenant_id"}))
    db.add(entry)
    await commit_or_conflict(db, "cashbook_conflict")
    await db.refresh(entry)
    return entry


async def update_cashbook_entry(
    db: AsyncSession, tenant_id: uuid.UUID, entry_id: uuid.UUID, payload: CashbookUpdate
) -> CashbookEntry:
    entry = await get_owned(db, CashbookEntry, entry_id, tenant_id, "cashbook_entry_not_found")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"tenant_id"}).items():
        setattr(entry, field, value)
    entry.version += 1
    await commit_or_conflict(db, "cashbook_conflict")
    await db.refresh(entry)
    return entry