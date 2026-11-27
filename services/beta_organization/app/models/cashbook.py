from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.tenant_record import TenantRecord


class CashbookEntry(TenantRecord, Base):
    __tablename__ = "cashbook_entries"
    __table_args__ = (Index("ix_ferti_cashbook_tenant_date", "tenant_id", "entry_date"), {"schema": "ferti"})

    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)