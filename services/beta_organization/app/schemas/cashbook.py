from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import Field
from app.schemas.common import MoneyPos, RecordOut, TenantIn


class CashbookCreate(TenantIn):
    entry_date: date
    direction: Literal["in", "out"]
    amount: MoneyPos
    category: str = Field(min_length=1, max_length=80)
    description: str | None = None


class CashbookUpdate(TenantIn):
    entry_date: date | None = None
    direction: Literal["in", "out"] | None = None
    amount: MoneyPos | None = None
    category: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = None


class CashbookOut(RecordOut):
    entry_date: date
    direction: str
    amount: Decimal
    category: str
    description: str | None