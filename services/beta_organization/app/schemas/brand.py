from pydantic import Field
from app.schemas.common import RecordOut, TenantIn


class BrandCreate(TenantIn):
    name: str = Field(min_length=1, max_length=120)
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