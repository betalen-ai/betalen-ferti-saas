import uuid
from datetime import date
from pydantic import BaseModel, Field

class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=40)
    permission_ids: list[uuid.UUID] = []

class RoleOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    permission_ids: list[uuid.UUID] = []

    model_config = {"from_attributes": True}

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
