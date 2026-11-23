import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, String, DateTime, Text, Date, Numeric, Integer, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "org"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    subdomain: Mapped[str | None] = mapped_column(String, unique=True)
    status: Mapped[str] = mapped_column(String, default="PENDING_REVIEW")
    subscription_plan: Mapped[str] = mapped_column(String, default="free")
    shop_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    pan: Mapped[str | None] = mapped_column(String(10))
    address_line: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    village_town: Mapped[str | None] = mapped_column(String(120))
    mandal_taluk: Mapped[str | None] = mapped_column(String(120))
    district: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(80))
    pincode: Mapped[str | None] = mapped_column(String(6))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    years_in_business: Mapped[int | None] = mapped_column(Integer)
    farmers_served_range: Mapped[str | None] = mapped_column(String(40))
    current_system: Mapped[str | None] = mapped_column(String(40))
    referral_code: Mapped[str | None] = mapped_column(String(80))
    heard_from: Mapped[str | None] = mapped_column(String(120))
    fertilizer_licence_no: Mapped[str | None] = mapped_column(String(120))
    fertilizer_licence_expiry: Mapped[date | None] = mapped_column(Date)
    pesticide_licence_no: Mapped[str | None] = mapped_column(String(120))
    pesticide_licence_expiry: Mapped[date | None] = mapped_column(Date)
    seed_licence_no: Mapped[str | None] = mapped_column(String(120))
    seed_licence_expiry: Mapped[date | None] = mapped_column(Date)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    alternate_mobile: Mapped[str | None] = mapped_column(String(24))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    review_reason: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reference_no: Mapped[str | None] = mapped_column(String(40), unique=True)
    consent_terms_version: Mapped[str | None] = mapped_column(String(40))
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consent_ip: Mapped[str | None] = mapped_column(String(64))
    consent_whatsapp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gstin: Mapped[str | None] = mapped_column(String(15))
    phone: Mapped[str | None] = mapped_column(String(24))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())