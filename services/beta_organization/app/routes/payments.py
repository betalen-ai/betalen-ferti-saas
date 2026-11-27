import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.payment import PaymentOut
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[PaymentOut])
async def list_payments(
    tenant_id: uuid.UUID | None = Query(default=None),
    farmer_id: uuid.UUID | None = None,
    bill_id: uuid.UUID | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.list_payments(
        db, resolve_tenant_id(cu, tenant_id),
        farmer_id=farmer_id, bill_id=bill_id, limit=limit, offset=offset,
    )


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await payment_service.get_payment(db, resolve_tenant_id(cu, tenant_id), payment_id)