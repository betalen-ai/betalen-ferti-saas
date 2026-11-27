import uuid
from decimal import Decimal

from pydantic import Field, field_validator
from app.schemas.common import Money, Qty, RecordOut, TenantIn, blank_to_none


class PackCreate(TenantIn):
    product_id: uuid.UUID
    size: Qty
    size_unit: str = Field(min_length=1, max_length=16)
    size_in_base_unit: Qty
    mrp: Money
    cash_price: Money
    credit_price: Money
    barcode: str | None = Field(default=None, max_length=80)
    allow_loose_sale: bool = False
    active: bool = True

    @field_validator("barcode")
    @classmethod
    def _clean(cls, v: str | None) -> str | None:
        return blank_to_none(v)


class PackUpdate(TenantIn):
    mrp: Money | None = None
    cash_price: Money | None = None
    credit_price: Money | None = None
    barcode: str | None = Field(default=None, max_length=80)
    allow_loose_sale: bool | None = None
    active: bool | None = None

    @field_validator("barcode")
    @classmethod
    def _clean(cls, v: str | None) -> str | None:
        return blank_to_none(v)


class PackOut(RecordOut):
    product_id: uuid.UUID
    size: Decimal
    size_unit: str
    size_in_base_unit: Decimal
    mrp: Decimal
    cash_price: Decimal
    credit_price: Decimal
    barcode: str | None
    allow_loose_sale: bool
    active: bool