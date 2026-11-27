import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.bill import BillItemOut, BillOut
from app.services import bill_service

router = APIRouter(prefix="/bills", tags=["bills"])


@router.get("", response_model=list[BillOut])
async def list_bills(
    tenant_id: uuid.UUID | None = Query(default=None),
    farmer_id: uuid.UUID | None = None,
    season_id: uuid.UUID | None = None,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await bill_service.list_bills(
        db, resolve_tenant_id(cu, tenant_id),
        farmer_id=farmer_id, season_id=season_id, q=q, limit=limit, offset=offset,
    )


@router.get("/{bill_id}", response_model=BillOut)
async def get_bill(
    bill_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await bill_service.get_bill(db, resolve_tenant_id(cu, tenant_id), bill_id)


@router.get("/{bill_id}/items", response_model=list[BillItemOut])
async def list_bill_items(
    bill_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await bill_service.list_bill_items(db, resolve_tenant_id(cu, tenant_id), bill_id)