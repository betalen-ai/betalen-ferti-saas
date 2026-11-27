import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer
from app.schemas.farmer import FarmerCreate, FarmerUpdate
from app.services.crud_base import commit_or_conflict, get_owned


async def list_farmers(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    include_inactive: bool = False,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(Farmer).where(Farmer.tenant_id == tenant_id)
    if not include_inactive:
        query = query.where(Farmer.active.is_(True))
    if q:
        query = query.where(
            or_(Farmer.name.ilike(f"%{q}%"), Farmer.mobile.ilike(f"%{q}%"), Farmer.village.ilike(f"%{q}%"))
        )
    result = await db.execute(query.order_by(Farmer.name).limit(limit).offset(offset))
    return result.scalars().all()


async def get_farmer(db: AsyncSession, tenant_id: uuid.UUID, farmer_id: uuid.UUID) -> Farmer:
    return await get_owned(db, Farmer, farmer_id, tenant_id, "farmer_not_found")


async def create_farmer(db: AsyncSession, tenant_id: uuid.UUID, payload: FarmerCreate) -> Farmer:
    farmer = Farmer(tenant_id=tenant_id, **payload.model_dump(exclude={"tenant_id"}))
    db.add(farmer)
    await commit_or_conflict(db, "farmer_mobile_already_exists")
    await db.refresh(farmer)
    return farmer


async def update_farmer(db: AsyncSession, tenant_id: uuid.UUID, farmer_id: uuid.UUID, payload: FarmerUpdate) -> Farmer:
    farmer = await get_owned(db, Farmer, farmer_id, tenant_id, "farmer_not_found")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"tenant_id"}).items():
        setattr(farmer, field, value)
    farmer.version += 1
    await commit_or_conflict(db, "farmer_mobile_already_exists")
    await db.refresh(farmer)
    return farmer


async def deactivate_farmer(db: AsyncSession, tenant_id: uuid.UUID, farmer_id: uuid.UUID) -> None:
    farmer = await get_owned(db, Farmer, farmer_id, tenant_id, "farmer_not_found")
    farmer.active = False
    farmer.version += 1
    await db.commit()