import uuid
from decimal import Decimal

from app.schemas.common import RecordOut


class KhataEntryOut(RecordOut):
    farmer_id: uuid.UUID
    bill_id: uuid.UUID | None
    payment_id: uuid.UUID | None
    entry_type: str
    debit: Decimal
    credit: Decimal
    description: str
    reverses_entry_id: uuid.UUID | None