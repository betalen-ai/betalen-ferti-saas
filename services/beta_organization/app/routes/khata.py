import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.khata import KhataEntryOut
from app.services import khata_service

router = APIRouter(prefix="/khata", tags=["khata"])


@router.get("", response_model=list[KhataEntryOut])
async def list_khata_entries(
    tenant_id: uuid.UUID | None = Query(default=None),
    farmer_id: uuid.UUID | None = None,
    bill_id: uuid.UUID | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await khata_service.list_khata_entries(
        db, resolve_tenant_id(cu, tenant_id),
        farmer_id=farmer_id, bill_id=bill_id, limit=limit, offset=offset,
    )


@router.get("/{entry_id}", response_model=KhataEntryOut)
async def get_khata_entry(
    entry_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await khata_service.get_khata_entry(db, resolve_tenant_id(cu, tenant_id), entry_id)