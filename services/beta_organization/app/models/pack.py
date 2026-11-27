import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.tenant_record import TenantRecord


class Pack(TenantRecord, Base):
    __tablename__ = "packs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_id", "size_in_base_unit", name="uq_ferti_pack_size"),
        UniqueConstraint("tenant_id", "barcode", name="uq_ferti_pack_tenant_barcode"),
        Index("ix_ferti_packs_tenant_barcode", "tenant_id", "barcode"),
        {"schema": "ferti"},
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ferti.products.id", ondelete="CASCADE"), nullable=False
    )
    size: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    size_unit: Mapped[str] = mapped_column(String(16), nullable=False)
    size_in_base_unit: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    mrp: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cash_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    credit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(80))
    allow_loose_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")