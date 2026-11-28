import uuid
from datetime import date
from decimal import Decimal

from pydantic import Field, model_validator
from app.schemas.common import Money, Qty, RecordOut, TenantIn


class StockLotCreate(TenantIn):
    pack_id: uuid.UUID
    supplier: str | None = Field(default=None, max_length=180)
    received_date: date
    quantity_base: Qty
    cost_price: Money
    batch_number: str | None = Field(default=None, max_length=80)
    expiry_date: date | None = None

    @model_validator(mode="after")
    def expiry_after_received(self):
        if self.expiry_date and self.expiry_date < self.received_date:
            raise ValueError("expiry_date must not be before received_date")
        return self


class StockLotUpdate(TenantIn):
    supplier: str | None = Field(default=None, max_length=180)
    cost_price: Money | None = None
    batch_number: str | None = Field(default=None, max_length=80)
    expiry_date: date | None = None


class StockLotOut(RecordOut):
    pack_id: uuid.UUID
    supplier: str | None
    received_date: date
    quantity_base: Decimal
    available_base: Decimal
    cost_price: Decimal
    batch_number: str | None
    expiry_date: date | None