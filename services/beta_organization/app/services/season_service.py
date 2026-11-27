import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.season import Season
from app.schemas.season import SeasonCreate, SeasonUpdate
from app.services.crud_base import commit_or_conflict, get_owned


async def list_seasons(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(Season).where(Season.tenant_id == tenant_id)
    if q:
        query = query.where(Season.name.ilike(f"%{q}%"))
    result = await db.execute(query.order_by(Season.start_date.desc()).limit(limit).offset(offset))
    return result.scalars().all()


async def get_season(db: AsyncSession, tenant_id: uuid.UUID, season_id: uuid.UUID) -> Season:
    return await get_owned(db, Season, season_id, tenant_id, "season_not_found")


async def create_season(db: AsyncSession, tenant_id: uuid.UUID, payload: SeasonCreate) -> Season:
    season = Season(tenant_id=tenant_id, **payload.model_dump(exclude={"tenant_id"}))
    db.add(season)
    await commit_or_conflict(db, "season_name_already_exists")
    await db.refresh(season)
    return season


async def update_season(db: AsyncSession, tenant_id: uuid.UUID, season_id: uuid.UUID, payload: SeasonUpdate) -> Season:
    season = await get_owned(db, Season, season_id, tenant_id, "season_not_found")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"tenant_id"}).items():
        setattr(season, field, value)
    season.version += 1
    await commit_or_conflict(db, "season_name_already_exists")
    await db.refresh(season)
    return season