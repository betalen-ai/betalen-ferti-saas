import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.setting import SettingsIn, SettingsOut
from app.services import settings_service
from app.services.crud_base import resolve_request_tenant

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
async def get_settings(
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await settings_service.get_settings(db, resolve_tenant_id(cu, tenant_id))


@router.put("", response_model=SettingsOut)
async def put_settings(
    payload: SettingsIn,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await settings_service.upsert_settings(
        db, resolve_request_tenant(cu, tenant_id, payload.tenant_id), payload.values
    )