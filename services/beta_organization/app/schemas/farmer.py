from decimal import Decimal
from typing import Annotated

from pydantic import Field
from app.schemas.common import RecordOut, TenantIn


class FarmerCreate(TenantIn):
    name: str = Field(min_length=1, max_length=180)
    mobile: str = Field(pattern=r"^\+?\d{10,15}$")
    address: str | None = None
    village: str | None = Field(default=None, max_length=120)
    opening_balance: Annotated[Decimal, Field(max_digits=14, decimal_places=2)] = Decimal("0")
    active: bool = True


class FarmerUpdate(TenantIn):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    mobile: str | None = Field(default=None, pattern=r"^\+?\d{10,15}$")
    address: str | None = None
    village: str | None = Field(default=None, max_length=120)
    active: bool | None = None


class FarmerOut(RecordOut):
    name: str
    mobile: str
    address: str | None
    village: str | None
    opening_balance: Decimal
    active: bool