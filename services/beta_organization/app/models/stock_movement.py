import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.tenant_record import TenantRecord


class StockMovement(TenantRecord, Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        Index("ix_ferti_stock_movements_pack_date", "tenant_id", "pack_id", "created_at"),
        {"schema": "ferti"},
    )

    pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.packs.id"), nullable=False)
    stock_lot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.stock_lots.id"))
    movement_type: Mapped[str] = mapped_column(String(24), nullable=False)
    quantity_base: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    source_type: Mapped[str | None] = mapped_column(String(24))