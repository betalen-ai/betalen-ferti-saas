import uuid
from datetime import date
from decimal import Decimal

from app.schemas.common import RecordOut


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