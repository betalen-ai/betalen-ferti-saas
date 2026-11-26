import uuid
from datetime import date
from pydantic import BaseModel, Field, model_validator


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

    @model_validator(mode="after")
    def _dates(self):
        if self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be after valid_from")
        return self


class SubscriptionUpdate(BaseModel):
    plan: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None


class SubscriptionOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    plan: str
    status: str
    valid_from: date
    valid_to: date

    model_config = {"from_attributes": True}


class PlanOut(BaseModel):
    code: str
    name: str | None = None
    max_staff: int | None = None
