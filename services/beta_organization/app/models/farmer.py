from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.tenant_record import TenantRecord


class Farmer(TenantRecord, Base):
    __tablename__ = "farmers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "mobile", name="uq_ferti_farmer_tenant_mobile"),
        {"schema": "ferti"},
    )

    name: Mapped[str] = mapped_column(String(180), nullable=False)
    mobile: Mapped[str] = mapped_column(String(24), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    village: Mapped[str | None] = mapped_column(String(120))
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")