from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.tenant_record import TenantRecord


class Season(TenantRecord, Base):
    __tablename__ = "seasons"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_ferti_season_tenant_name"),
        {"schema": "ferti"},
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    default_cash_discount: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False, default=0)
    default_credit_interest_per_month: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False, default=0)
    due_date: Mapped[date | None] = mapped_column(Date)
    grace_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    late_interest_per_day: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)