import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.schemas.audit_log import AuditLogOut
from app.services import audit_log_service

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
async def list_audit_logs(
    tenant_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await audit_log_service.list_audit_logs(
        db, resolve_tenant_id(cu, tenant_id), limit=limit, offset=offset,
    )


@router.get("/{log_id}", response_model=AuditLogOut)
async def get_audit_log(
    log_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await audit_log_service.get_audit_log(db, resolve_tenant_id(cu, tenant_id), log_id)