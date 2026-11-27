from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import Field, model_validator
from app.schemas.common import Pct, RecordOut, TenantIn


class SeasonCreate(TenantIn):
    name: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date
    default_cash_discount: Pct = Decimal("0")
    default_credit_interest_per_month: Pct = Decimal("0")
    due_date: date | None = None
    grace_days: int = Field(default=0, ge=0)
    late_interest_per_day: Annotated[Decimal, Field(ge=0, max_digits=7, decimal_places=4)] = Decimal("0")

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class SeasonUpdate(TenantIn):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    default_cash_discount: Pct | None = None
    default_credit_interest_per_month: Pct | None = None
    due_date: date | None = None
    grace_days: int | None = Field(default=None, ge=0)
    late_interest_per_day: Annotated[Decimal, Field(ge=0, max_digits=7, decimal_places=4)] | None = None

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class SeasonOut(RecordOut):
    name: str
    start_date: date
    end_date: date
    default_cash_discount: Decimal
    default_credit_interest_per_month: Decimal
    due_date: date | None
    grace_days: int
    late_interest_per_day: Decimal