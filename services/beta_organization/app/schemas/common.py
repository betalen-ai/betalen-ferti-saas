import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Money = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]
Qty = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=3)]
Qty0 = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=3)]
MoneyPos = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2)]
Pct = Annotated[Decimal, Field(ge=0, max_digits=7, decimal_places=2)]


class TenantIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    tenant_id: uuid.UUID | None = None


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    version: int


def blank_to_none(v: str | None) -> str | None:
    return v or None