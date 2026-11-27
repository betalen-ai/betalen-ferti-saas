import uuid
from datetime import date
from decimal import Decimal

from app.schemas.common import RecordOut


class PaymentOut(RecordOut):
    farmer_id: uuid.UUID
    amount: Decimal
    mode: str
    payment_date: date
    bill_id: uuid.UUID | None