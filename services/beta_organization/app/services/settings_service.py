import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting
from app.services.crud_base import commit_or_conflict, not_found


async def get_settings(db: AsyncSession, tenant_id: uuid.UUID) -> Setting:
    row = await db.get(Setting, tenant_id)
    if row is None:
        raise not_found("settings_not_found")
    return row


async def upsert_settings(db: AsyncSession, tenant_id: uuid.UUID, values: dict[str, Any]) -> Setting:
    row = await db.get(Setting, tenant_id)
    if row is None:
        row = Setting(tenant_id=tenant_id, values=values)
        db.add(row)
    else:
        row.values = values
    await commit_or_conflict(db, "settings_conflict")
    await db.refresh(row)
    return row