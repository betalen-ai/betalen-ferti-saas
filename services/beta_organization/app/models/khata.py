import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.tenant_record import TenantRecord


class KhataEntry(TenantRecord, Base):
    __tablename__ = "khata_entries"
    __table_args__ = (
        Index("ix_ferti_khata_tenant_farmer_date", "tenant_id", "farmer_id", "created_at"),
        {"schema": "ferti"},
    )

    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.farmers.id"), nullable=False)
    bill_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.bills.id"))
    payment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.payments.id"))
    entry_type: Mapped[str] = mapped_column(String(24), nullable=False)
    debit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    credit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reverses_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ferti.khata_entries.id")
    )