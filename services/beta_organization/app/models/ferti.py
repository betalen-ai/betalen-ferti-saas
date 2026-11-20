import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TenantRecord:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")


class Brand(TenantRecord, Base):
    __tablename__ = "brands"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_ferti_brand_tenant_name"),
        {"schema": "ferti"},
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class Category(TenantRecord, Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_ferti_category_tenant_name"),
        {"schema": "ferti"},
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    product_type: Mapped[str] = mapped_column(String(16), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class Product(TenantRecord, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("tenant_id", "brand_id", "name", name="uq_ferti_product_tenant_brand_name"),
        {"schema": "ferti"},
    )

    brand_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.brands.id"))
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.categories.id"))
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(80))
    hsn: Mapped[str | None] = mapped_column(String(32))
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    unit_type: Mapped[str] = mapped_column(String(16), nullable=False)
    low_stock_level: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class Pack(TenantRecord, Base):
    __tablename__ = "packs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_id", "size_in_base_unit", name="uq_ferti_pack_size"),
        UniqueConstraint("tenant_id", "barcode", name="uq_ferti_pack_tenant_barcode"),
        Index("ix_ferti_packs_tenant_barcode", "tenant_id", "barcode"),
        {"schema": "ferti"},
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ferti.products.id", ondelete="CASCADE"), nullable=False
    )
    size: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    size_unit: Mapped[str] = mapped_column(String(16), nullable=False)
    size_in_base_unit: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    mrp: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cash_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    credit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(80))
    allow_loose_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class StockLot(TenantRecord, Base):
    __tablename__ = "stock_lots"
    __table_args__ = (Index("ix_ferti_stock_lots_tenant_expiry", "tenant_id", "expiry_date"), {"schema": "ferti"})

    pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.packs.id"), nullable=False)
    supplier: Mapped[str | None] = mapped_column(String(180))
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity_base: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    available_base: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    batch_number: Mapped[str | None] = mapped_column(String(80))
    expiry_date: Mapped[date | None] = mapped_column(Date)


class StockMovement(TenantRecord, Base):
    __tablename__ = "stock_movements"
    __table_args__ = (Index("ix_ferti_stock_movements_pack_date", "tenant_id", "pack_id", "created_at"), {"schema": "ferti"})

    pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.packs.id"), nullable=False)
    stock_lot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.stock_lots.id"))
    movement_type: Mapped[str] = mapped_column(String(24), nullable=False)
    quantity_base: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    source_type: Mapped[str | None] = mapped_column(String(24))


class Farmer(TenantRecord, Base):
    __tablename__ = "farmers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "mobile", name="uq_ferti_farmer_tenant_mobile"),
        {"schema": "ferti"},
    )

    name: Mapped[str] = mapped_column(String(180), nullable=False)
    mobile: Mapped[str] = mapped_column(String(24), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    village: Mapped[str | None] = mapped_column(String(120))
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class Season(TenantRecord, Base):
    __tablename__ = "seasons"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_ferti_season_tenant_name"),
        {"schema": "ferti"},
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    default_cash_discount: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False, default=0)
    default_credit_interest_per_month: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False, default=0)
    due_date: Mapped[date | None] = mapped_column(Date)
    grace_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    late_interest_per_day: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)


class Bill(TenantRecord, Base):
    __tablename__ = "bills"
    __table_args__ = (
        UniqueConstraint("tenant_id", "bill_number", name="uq_ferti_bill_tenant_number"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_ferti_bill_idempotency"),
        Index("ix_ferti_bills_tenant_farmer_date", "tenant_id", "farmer_id", "bill_date"),
        {"schema": "ferti"},
    )

    bill_number: Mapped[str] = mapped_column(String(40), nullable=False)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.farmers.id"), nullable=False)
    season_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.seasons.id"))
    bill_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    payment_type: Mapped[str] = mapped_column(String(12), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    interest_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    round_off: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    paid_now: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="posted")
    terms: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(120))


class BillItem(TenantRecord, Base):
    __tablename__ = "bill_items"
    __table_args__ = ({"schema": "ferti"},)

    bill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.bills.id", ondelete="CASCADE"), nullable=False)
    pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.packs.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(180), nullable=False)
    pack_name: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    quantity_base: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


class BillDraft(TenantRecord, Base):
    __tablename__ = "bill_drafts"
    __table_args__ = ({"schema": "ferti"},)

    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class KhataEntry(TenantRecord, Base):
    __tablename__ = "khata_entries"
    __table_args__ = (Index("ix_ferti_khata_tenant_farmer_date", "tenant_id", "farmer_id", "created_at"), {"schema": "ferti"})

    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.farmers.id"), nullable=False)
    bill_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.bills.id"))
    payment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.payments.id"))
    entry_type: Mapped[str] = mapped_column(String(24), nullable=False)
    debit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    credit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reverses_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.khata_entries.id"))


class Payment(TenantRecord, Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_ferti_payment_idempotency"),
        Index("ix_ferti_payments_tenant_farmer_date", "tenant_id", "farmer_id", "payment_date"),
        {"schema": "ferti"},
    )

    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.farmers.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    mode: Mapped[str] = mapped_column(String(12), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    bill_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.bills.id"))
    idempotency_key: Mapped[str | None] = mapped_column(String(120))


class PaymentAllocation(TenantRecord, Base):
    __tablename__ = "payment_allocations"
    __table_args__ = ({"schema": "ferti"},)

    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.payments.id", ondelete="CASCADE"), nullable=False)
    bill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ferti.bills.id"), nullable=False)
    interest_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)


class CashbookEntry(TenantRecord, Base):
    __tablename__ = "cashbook_entries"
    __table_args__ = (Index("ix_ferti_cashbook_tenant_date", "tenant_id", "entry_date"), {"schema": "ferti"})

    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class Setting(Base):
    __tablename__ = "settings"
    __table_args__ = ({"schema": "ferti"},)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org.tenants.id", ondelete="CASCADE"), primary_key=True
    )
    values: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class AuditLog(TenantRecord, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_ferti_audit_tenant_entity", "tenant_id", "entity_type", "entity_id"), {"schema": "ferti"})

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    old_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "operation", "key", name="uq_ferti_idempotency_tenant_operation_key"),
        {"schema": "ferti"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    operation: Mapped[str] = mapped_column(String(40), nullable=False)
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    response: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AuthIdentity(Base):
    __tablename__ = "auth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_subject", name="uq_ferti_auth_provider_subject"),
        {"schema": "ferti"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org.org_users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(24), nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class OtpChallenge(Base):
    __tablename__ = "otp_challenges"
    __table_args__ = (Index("ix_ferti_otp_phone_purpose_created", "phone", "purpose", "created_at"), {"schema": "ferti"})

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(24), nullable=False)
    subdomain: Mapped[str | None] = mapped_column(String(40))
    purpose: Mapped[str] = mapped_column(String(16), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AuthActionToken(Base):
    __tablename__ = "auth_action_tokens"
    __table_args__ = (Index("ix_ferti_auth_tokens_tenant_user", "tenant_id", "user_id", "purpose"), {"schema": "ferti"})

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org.org_users.id", ondelete="CASCADE"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(24), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"
    __table_args__ = (Index("ix_ferti_refresh_tenant_user", "tenant_id", "user_id"), {"schema": "ferti"})

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org.org_users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AuthRateLimit(Base):
    __tablename__ = "auth_rate_limits"
    __table_args__ = (
        UniqueConstraint("action", "subject_hash", "window_start", name="uq_ferti_rate_limit_bucket"),
        {"schema": "ferti"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
