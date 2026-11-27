import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.cashbook import CashbookCreate, CashbookOut, CashbookUpdate
from app.services import cashbook_service
from app.services.crud_base import resolve_request_tenant

router = APIRouter(prefix="/cashbook", tags=["cashbook"])


@router.get("", response_model=list[CashbookOut])
async def list_cashbook(
    tenant_id: uuid.UUID | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await cashbook_service.list_cashbook(
        db, resolve_tenant_id(cu, tenant_id), q=q, limit=limit, offset=offset,
    )


@router.get("/{entry_id}", response_model=CashbookOut)
async def get_cashbook_entry(
    entry_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await cashbook_service.get_cashbook_entry(db, resolve_tenant_id(cu, tenant_id), entry_id)


@router.post("", response_model=CashbookOut, status_code=status.HTTP_201_CREATED)
async def create_cashbook_entry(
    payload: CashbookCreate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await cashbook_service.create_cashbook_entry(db, owned, payload)


@router.patch("/{entry_id}", response_model=CashbookOut)
async def update_cashbook_entry(
    entry_id: uuid.UUID,
    payload: CashbookUpdate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await cashbook_service.update_cashbook_entry(db, owned, entry_id, payload)