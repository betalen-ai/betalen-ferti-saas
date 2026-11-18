import uuid
from datetime import date

from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    plan: str
    valid_from: date
    valid_to: date


class SubscriptionOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    plan: str
    status: str
    valid_from: date
    valid_to: date

    model_config = {"from_attributes": True}