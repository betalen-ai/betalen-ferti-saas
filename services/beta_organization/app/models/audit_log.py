import uuid
from typing import Any

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.tenant_record import TenantRecord


class AuditLog(TenantRecord, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_ferti_audit_tenant_entity", "tenant_id", "entity_type", "entity_id"),
        {"schema": "ferti"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    old_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)