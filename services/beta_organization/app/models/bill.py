import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.tenant_record import TenantRecord


class Bill(TenantRecord, Base):
    __tablename__ = "bills"
    __table_args__ = (
        UniqueConstraint("tenant_id", "bill_number", name="uq_ferti_bill_tenant_number"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_ferti_bill_idempotency"),
        Index("ix_ferti_bills_tenant_farmer_date", "tenant_id", "farmer_id", "bill_date"),
        {"schema": "ferti"},
    )

    bill_number: Mapped[str] = mapped_column(String(40), nullable=False)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.farmers.id"), nullable=False)
    season_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.seasons.id"))
    bill_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    payment_type: Mapped[str] = mapped_column(String(12), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    interest_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    round_off: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    paid_now: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="posted")
    terms: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(120))


class BillItem(TenantRecord, Base):
    __tablename__ = "bill_items"
    __table_args__ = ({"schema": "ferti"},)

    bill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ferti.bills.id", ondelete="CASCADE"), nullable=False
    )
    pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.packs.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(180), nullable=False)
    pack_name: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    quantity_base: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


class BillDraft(TenantRecord, Base):
    __tablename__ = "bill_drafts"
    __table_args__ = ({"schema": "ferti"},)

    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)