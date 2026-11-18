import uuid

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