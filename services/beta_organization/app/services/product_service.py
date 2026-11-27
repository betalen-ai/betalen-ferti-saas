import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.crud_base import commit_or_conflict, ensure_same_tenant, get_owned


async def list_products(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    brand_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    include_inactive: bool = False,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(Product).where(Product.tenant_id == tenant_id)
    if not include_inactive:
        query = query.where(Product.active.is_(True))
    if brand_id:
        query = query.where(Product.brand_id == brand_id)
    if category_id:
        query = query.where(Product.category_id == category_id)
    if q:
        query = query.where(or_(Product.name.ilike(f"%{q}%"), Product.hsn.ilike(f"%{q}%")))
    result = await db.execute(query.order_by(Product.name).limit(limit).offset(offset))
    return result.scalars().all()


async def get_product(db: AsyncSession, tenant_id: uuid.UUID, product_id: uuid.UUID) -> Product:
    return await get_owned(db, Product, product_id, tenant_id, "product_not_found")


async def create_product(db: AsyncSession, tenant_id: uuid.UUID, payload: ProductCreate) -> Product:
    await ensure_same_tenant(db, Brand, payload.brand_id, tenant_id, "brand_id")
    await ensure_same_tenant(db, Category, payload.category_id, tenant_id, "category_id")
    product = Product(tenant_id=tenant_id, **payload.model_dump(exclude={"tenant_id"}))
    db.add(product)
    await commit_or_conflict(db, "product_already_exists")
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession, tenant_id: uuid.UUID, product_id: uuid.UUID, payload: ProductUpdate
) -> Product:
    product = await get_owned(db, Product, product_id, tenant_id, "product_not_found")
    changes = payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"tenant_id"})
    if "brand_id" in changes:
        await ensure_same_tenant(db, Brand, changes["brand_id"], tenant_id, "brand_id")
    if "category_id" in changes:
        await ensure_same_tenant(db, Category, changes["category_id"], tenant_id, "category_id")
    for field, value in changes.items():
        setattr(product, field, value)
    product.version += 1
    await commit_or_conflict(db, "product_already_exists")
    await db.refresh(product)
    return product


async def deactivate_product(db: AsyncSession, tenant_id: uuid.UUID, product_id: uuid.UUID) -> None:
    product = await get_owned(db, Product, product_id, tenant_id, "product_not_found")
    product.active = False
    product.version += 1
    await db.commit()