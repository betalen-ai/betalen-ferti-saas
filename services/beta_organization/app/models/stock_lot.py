import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.tenant_record import TenantRecord


class StockLot(TenantRecord, Base):
    __tablename__ = "stock_lots"
    __table_args__ = (Index("ix_ferti_stock_lots_tenant_expiry", "tenant_id", "expiry_date"), {"schema": "ferti"})

    pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.packs.id"), nullable=False)
    supplier: Mapped[str | None] = mapped_column(String(180))
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity_base: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    available_base: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    batch_number: Mapped[str | None] = mapped_column(String(80))
    expiry_date: Mapped[date | None] = mapped_column(Date)