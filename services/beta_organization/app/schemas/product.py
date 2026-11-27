import uuid
from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator
from app.schemas.common import Qty0, RecordOut, TenantIn, blank_to_none


class ProductCreate(TenantIn):
    brand_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=180)
    grade: str | None = Field(default=None, max_length=80)
    hsn: str | None = Field(default=None, max_length=32)
    gst_rate: Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)] = Decimal("0")
    unit_type: str = Field(min_length=1, max_length=16)
    low_stock_level: Qty0 = Decimal("0")
    active: bool = True

    @field_validator("grade", "hsn")
    @classmethod
    def _clean(cls, v: str | None) -> str | None:
        return blank_to_none(v)


class ProductUpdate(TenantIn):
    brand_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=180)
    grade: str | None = Field(default=None, max_length=80)
    hsn: str | None = Field(default=None, max_length=32)
    gst_rate: Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)] | None = None
    unit_type: str | None = Field(default=None, min_length=1, max_length=16)
    low_stock_level: Qty0 | None = None
    active: bool | None = None


class ProductOut(RecordOut):
    brand_id: uuid.UUID | None
    category_id: uuid.UUID | None
    name: str
    grade: str | None
    hsn: str | None
    gst_rate: Decimal
    unit_type: str
    low_stock_level: Decimal
    active: bool