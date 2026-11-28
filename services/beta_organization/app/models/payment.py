import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.tenant_record import TenantRecord


class Payment(TenantRecord, Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_ferti_payment_idempotency"),
        Index("ix_ferti_payments_tenant_farmer_date", "tenant_id", "farmer_id", "payment_date"),
        {"schema": "ferti"},
    )

    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.farmers.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    mode: Mapped[str] = mapped_column(String(12), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    bill_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.bills.id"))
    idempotency_key: Mapped[str | None] = mapped_column(String(120))


class PaymentAllocation(TenantRecord, Base):
    __tablename__ = "payment_allocations"
    __table_args__ = ({"schema": "ferti"},)

    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ferti.payments.id", ondelete="CASCADE"), nullable=False
    )
    bill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.bills.id"), nullable=False)
    interest_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)