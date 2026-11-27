import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Money = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]
Qty = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=3)]
Qty0 = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=3)]
MoneyPos = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2)]


class TenantIn(BaseModel):
    """Base for every write payload. tenant_id is optional; it is always checked
    against the caller's tenant by resolve_request_tenant()."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    tenant_id: uuid.UUID | None = None


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    version: int


def _blank_to_none(v: str | None) -> str | None:
    return v or None


# ---------- Brand ----------
class BrandCreate(TenantIn):
    name: str = Field(min_length=1, max_length=120)  # whitespace is stripped first, so blank names fail min_length
    manufacturer: str = Field(default="", max_length=180)
    notes: str = ""
    active: bool = True


class BrandUpdate(TenantIn):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    manufacturer: str | None = Field(default=None, max_length=180)
    notes: str | None = None
    active: bool | None = None


class BrandOut(RecordOut):
    name: str
    manufacturer: str
    notes: str
    active: bool


# ---------- Category ----------
class CategoryCreate(TenantIn):
    name: str = Field(min_length=1, max_length=120)
    product_type: str = Field(min_length=1, max_length=16)
    active: bool = True


class CategoryUpdate(TenantIn):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    product_type: str | None = Field(default=None, min_length=1, max_length=16)
    active: bool | None = None


class CategoryOut(RecordOut):
    name: str
    product_type: str
    active: bool


# ---------- Product ----------
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
    def blank_to_none(cls, v: str | None) -> str | None:
        return _blank_to_none(v)


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


# ---------- Pack ----------
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
    def blank_to_none(cls, v: str | None) -> str | None:
        return _blank_to_none(v)


class PackUpdate(TenantIn):
    """product_id / size fields are immutable once stock and bills reference the pack."""

    mrp: Money | None = None
    cash_price: Money | None = None
    credit_price: Money | None = None
    barcode: str | None = Field(default=None, max_length=80)
    allow_loose_sale: bool | None = None
    active: bool | None = None

    @field_validator("barcode")
    @classmethod
    def blank_to_none(cls, v: str | None) -> str | None:
        return _blank_to_none(v)


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


# ---------- Stock ----------
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
    """available_base is changed only through stock movements."""

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


class StockMovementCreate(TenantIn):
    stock_lot_id: uuid.UUID
    movement_type: Literal["adjustment", "damage", "return", "opening"]
    quantity_base: Annotated[Decimal, Field(max_digits=14, decimal_places=3)]  # signed (+ in, - out)
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


# ---------- Farmer ----------
class FarmerCreate(TenantIn):
    name: str = Field(min_length=1, max_length=180)
    mobile: str = Field(pattern=r"^\+?\d{10,15}$")
    address: str | None = None
    village: str | None = Field(default=None, max_length=120)
    opening_balance: Annotated[Decimal, Field(max_digits=14, decimal_places=2)] = Decimal("0")
    active: bool = True


class FarmerUpdate(TenantIn):
    """opening_balance is a ledger value and is not editable here."""

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


# ---------- Season ----------
_Pct = Annotated[Decimal, Field(ge=0, max_digits=7, decimal_places=2)]


class SeasonCreate(TenantIn):
    name: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date
    default_cash_discount: _Pct = Decimal("0")
    default_credit_interest_per_month: _Pct = Decimal("0")
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
    default_cash_discount: _Pct | None = None
    default_credit_interest_per_month: _Pct | None = None
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


# ---------- Cashbook ----------
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


# ---------- Settings (one row per tenant) ----------
class SettingsIn(TenantIn):
    values: dict[str, Any]


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tenant_id: uuid.UUID
    values: dict[str, Any]
    updated_at: datetime


# ---------- Read-only ledger outputs ----------
class BillOut(RecordOut):
    bill_number: str
    farmer_id: uuid.UUID
    season_id: uuid.UUID | None
    bill_date: date
    due_date: date | None
    payment_type: str
    subtotal: Decimal
    discount: Decimal
    interest_amount: Decimal
    gst_amount: Decimal
    round_off: Decimal
    total: Decimal
    paid_now: Decimal
    balance: Decimal
    status: str
    terms: str | None


class BillItemOut(RecordOut):
    bill_id: uuid.UUID
    pack_id: uuid.UUID
    product_name: str
    pack_name: str
    quantity: Decimal
    quantity_base: Decimal
    unit_price: Decimal
    line_total: Decimal


class PaymentOut(RecordOut):
    farmer_id: uuid.UUID
    amount: Decimal
    mode: str
    payment_date: date
    bill_id: uuid.UUID | None


class KhataEntryOut(RecordOut):
    farmer_id: uuid.UUID
    bill_id: uuid.UUID | None
    payment_id: uuid.UUID | None
    entry_type: str
    debit: Decimal
    credit: Decimal
    description: str
    reverses_entry_id: uuid.UUID | None


class AuditLogOut(RecordOut):
    user_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    action: str
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None