from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut
from app.routes.ferti import current_identity

router = APIRouter()


@router.get("", response_model=list[SubscriptionOut])
async def list_subscriptions(
    identity: dict[str, UUID] = Depends(current_identity), db: AsyncSession = Depends(get_db)
):
    tenant_id = identity["tenant_id"]
    return (
        await db.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
    ).scalars().all()


@router.post("", response_model=SubscriptionOut, status_code=201)
async def create_subscription(
    payload: SubscriptionCreate,
    identity: dict[str, UUID] = Depends(current_identity),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = identity["tenant_id"]
    sub = Subscription(
        tenant_id=tenant_id,
        plan=payload.plan,
        status="active",
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub