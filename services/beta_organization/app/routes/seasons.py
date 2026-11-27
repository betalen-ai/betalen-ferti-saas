import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.season import SeasonCreate, SeasonOut, SeasonUpdate
from app.services import season_service
from app.services.crud_base import resolve_request_tenant

router = APIRouter(prefix="/seasons", tags=["seasons"])


@router.get("", response_model=list[SeasonOut])
async def list_seasons(
    tenant_id: uuid.UUID | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await season_service.list_seasons(
        db, resolve_tenant_id(cu, tenant_id), q=q, limit=limit, offset=offset,
    )


@router.get("/{season_id}", response_model=SeasonOut)
async def get_season(
    season_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await season_service.get_season(db, resolve_tenant_id(cu, tenant_id), season_id)


@router.post("", response_model=SeasonOut, status_code=status.HTTP_201_CREATED)
async def create_season(
    payload: SeasonCreate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await season_service.create_season(db, owned, payload)


@router.patch("/{season_id}", response_model=SeasonOut)
async def update_season(
    season_id: uuid.UUID,
    payload: SeasonUpdate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    return await season_service.update_season(db, owned, season_id, payload)