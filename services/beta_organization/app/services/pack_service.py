import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pack import Pack
from app.models.product import Product
from app.schemas.pack import PackCreate, PackUpdate
from app.services.crud_base import commit_or_conflict, ensure_same_tenant, get_owned


async def list_packs(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    product_id: uuid.UUID | None = None,
    include_inactive: bool = False,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(Pack).where(Pack.tenant_id == tenant_id)
    if not include_inactive:
        query = query.where(Pack.active.is_(True))
    if product_id:
        query = query.where(Pack.product_id == product_id)
    if q:
        query = query.where(Pack.barcode.ilike(f"%{q}%"))
    result = await db.execute(query.order_by(Pack.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


async def get_pack(db: AsyncSession, tenant_id: uuid.UUID, pack_id: uuid.UUID) -> Pack:
    return await get_owned(db, Pack, pack_id, tenant_id, "pack_not_found")


async def create_pack(db: AsyncSession, tenant_id: uuid.UUID, payload: PackCreate) -> Pack:
    await ensure_same_tenant(db, Product, payload.product_id, tenant_id, "product_id")
    pack = Pack(tenant_id=tenant_id, **payload.model_dump(exclude={"tenant_id"}))
    db.add(pack)
    await commit_or_conflict(db, "pack_size_or_barcode_already_exists")
    await db.refresh(pack)
    return pack


async def update_pack(db: AsyncSession, tenant_id: uuid.UUID, pack_id: uuid.UUID, payload: PackUpdate) -> Pack:
    pack = await get_owned(db, Pack, pack_id, tenant_id, "pack_not_found")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"tenant_id"}).items():
        setattr(pack, field, value)
    pack.version += 1
    await commit_or_conflict(db, "pack_size_or_barcode_already_exists")
    await db.refresh(pack)
    return pack


async def deactivate_pack(db: AsyncSession, tenant_id: uuid.UUID, pack_id: uuid.UUID) -> None:
    pack = await get_owned(db, Pack, pack_id, tenant_id, "pack_not_found")
    pack.active = False
    pack.version += 1
    await db.commit()