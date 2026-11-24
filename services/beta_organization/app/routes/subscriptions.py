from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut

router = APIRouter()

def _require_tenant(x_tenant_id: str | None = Header(default=None)) -> UUID:
    if not x_tenant_id:
        raise HTTPException(401, detail="missing_tenant_header")
    return UUID(x_tenant_id)

@router.get("", response_model=list[SubscriptionOut])
async def list_subscriptions(tenant_id: UUID = Depends(_require_tenant), db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))).scalars().all()

@router.post("", response_model=SubscriptionOut, status_code=201)
async def create_subscription(payload: SubscriptionCreate, tenant_id: UUID = Depends(_require_tenant), db: AsyncSession = Depends(get_db)):
    sub = Subscription(tenant_id=tenant_id, plan=payload.plan, status="active", valid_from=payload.valid_from, valid_to=payload.valid_to)
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub
