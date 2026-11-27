import uuid
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, field_validator
from app.schemas.common import RecordOut, TenantIn


class StockMovementCreate(TenantIn):
    stock_lot_id: uuid.UUID
    movement_type: Literal["adjustment", "damage", "return", "opening"]
    quantity_base: Annotated[Decimal, Field(max_digits=14, decimal_places=3)]
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("quantity_base")
    @classmethod
    def non_zero(cls, v: Decimal) -> Decimal:
        if v == 0:
            raise ValueError("quantity_base must not be zero")
        return v


class StockMovementOut(RecordOut):
    pack_id: uuid.UUID
    stock_lot_id: uuid.UUID | None
    movement_type: str
    quantity_base: Decimal
    reason: str | None
    source_id: uuid.UUID | None
    source_type: str | None