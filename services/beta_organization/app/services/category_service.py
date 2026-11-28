import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.crud_base import commit_or_conflict, get_owned


async def list_categories(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    include_inactive: bool = False,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(Category).where(Category.tenant_id == tenant_id)
    if not include_inactive:
        query = query.where(Category.active.is_(True))
    if q:
        query = query.where(Category.name.ilike(f"%{q}%"))
    result = await db.execute(query.order_by(Category.name).limit(limit).offset(offset))
    return result.scalars().all()


async def get_category(db: AsyncSession, tenant_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    return await get_owned(db, Category, category_id, tenant_id, "category_not_found")


async def create_category(db: AsyncSession, tenant_id: uuid.UUID, payload: CategoryCreate) -> Category:
    category = Category(tenant_id=tenant_id, **payload.model_dump(exclude={"tenant_id"}))
    db.add(category)
    await commit_or_conflict(db, "category_name_already_exists")
    await db.refresh(category)
    return category


async def update_category(
    db: AsyncSession, tenant_id: uuid.UUID, category_id: uuid.UUID, payload: CategoryUpdate
) -> Category:
    category = await get_owned(db, Category, category_id, tenant_id, "category_not_found")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"tenant_id"}).items():
        setattr(category, field, value)
    category.version += 1
    await commit_or_conflict(db, "category_name_already_exists")
    await db.refresh(category)
    return category


async def deactivate_category(db: AsyncSession, tenant_id: uuid.UUID, category_id: uuid.UUID) -> None:
    category = await get_owned(db, Category, category_id, tenant_id, "category_not_found")
    category.active = False
    category.version += 1
    await db.commit()