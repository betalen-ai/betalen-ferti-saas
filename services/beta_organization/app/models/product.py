import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.tenant_record import TenantRecord


class Product(TenantRecord, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("tenant_id", "brand_id", "name", name="uq_ferti_product_tenant_brand_name"),
        {"schema": "ferti"},
    )

    brand_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.brands.id"))
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.categories.id"))
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(80))
    hsn: Mapped[str | None] = mapped_column(String(32))
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    unit_type: Mapped[str] = mapped_column(String(16), nullable=False)
    low_stock_level: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")