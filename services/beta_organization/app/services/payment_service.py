import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.services.crud_base import get_owned


async def list_payments(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    farmer_id: uuid.UUID | None = None,
    bill_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(Payment).where(Payment.tenant_id == tenant_id)
    if farmer_id:
        query = query.where(Payment.farmer_id == farmer_id)
    if bill_id:
        query = query.where(Payment.bill_id == bill_id)
    result = await db.execute(
        query.order_by(Payment.payment_date.desc(), Payment.created_at.desc()).limit(limit).offset(offset)
    )
    return result.scalars().all()


async def get_payment(db: AsyncSession, tenant_id: uuid.UUID, payment_id: uuid.UUID) -> Payment:
    return await get_owned(db, Payment, payment_id, tenant_id, "payment_not_found")