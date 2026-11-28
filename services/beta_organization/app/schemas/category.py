from pydantic import Field
from app.schemas.common import RecordOut, TenantIn


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