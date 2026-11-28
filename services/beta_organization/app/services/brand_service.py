import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand
from app.schemas.brand import BrandCreate, BrandUpdate
from app.services.crud_base import commit_or_conflict, get_owned


async def list_brands(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    include_inactive: bool = False,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(Brand).where(Brand.tenant_id == tenant_id)
    if not include_inactive:
        query = query.where(Brand.active.is_(True))
    if q:
        query = query.where(or_(Brand.name.ilike(f"%{q}%"), Brand.manufacturer.ilike(f"%{q}%")))
    result = await db.execute(query.order_by(Brand.name).limit(limit).offset(offset))
    return result.scalars().all()


async def get_brand(db: AsyncSession, tenant_id: uuid.UUID, brand_id: uuid.UUID) -> Brand:
    return await get_owned(db, Brand, brand_id, tenant_id, "brand_not_found")


async def create_brand(db: AsyncSession, tenant_id: uuid.UUID, payload: BrandCreate) -> Brand:
    brand = Brand(tenant_id=tenant_id, **payload.model_dump(exclude={"tenant_id"}))
    db.add(brand)
    await commit_or_conflict(db, "brand_name_already_exists")
    await db.refresh(brand)
    return brand


async def update_brand(db: AsyncSession, tenant_id: uuid.UUID, brand_id: uuid.UUID, payload: BrandUpdate) -> Brand:
    brand = await get_owned(db, Brand, brand_id, tenant_id, "brand_not_found")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"tenant_id"}).items():
        setattr(brand, field, value)
    brand.version += 1
    await commit_or_conflict(db, "brand_name_already_exists")
    await db.refresh(brand)
    return brand


async def deactivate_brand(db: AsyncSession, tenant_id: uuid.UUID, brand_id: uuid.UUID) -> None:
    brand = await get_owned(db, Brand, brand_id, tenant_id, "brand_not_found")
    brand.active = False
    brand.version += 1
    await db.commit()