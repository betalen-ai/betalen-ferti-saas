"""Add tenant-scoped Ferti+ domain tables.

Revision ID: d4e5f6a7b8c9
Revises: a1b2c3d4e5f6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tenant_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    ]


def upgrade() -> None:
    op.add_column("tenants", sa.Column("address", sa.Text(), nullable=True), schema="org")
    op.add_column("tenants", sa.Column("gstin", sa.String(length=15), nullable=True), schema="org")
    op.add_column("tenants", sa.Column("phone", sa.String(length=24), nullable=True), schema="org")
    op.add_column("tenants", sa.Column("logo_url", sa.String(length=500), nullable=True), schema="org")
    op.add_column("org_users", sa.Column("language", sa.String(length=8), nullable=False, server_default="en"), schema="org")
    op.add_column("org_users", sa.Column("phone", sa.String(length=24), nullable=True), schema="org")
    op.add_column("org_users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.true()), schema="org")
    op.create_unique_constraint("uq_org_user_tenant_phone", "org_users", ["tenant_id", "phone"], schema="org")
    op.execute("CREATE SCHEMA IF NOT EXISTS ferti")

    op.create_table(
        "brands", *_tenant_columns(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "name", name="uq_ferti_brand_tenant_name"),
        schema="ferti",
    )
    op.create_index("ix_ferti_brands_tenant_id", "brands", ["tenant_id"], schema="ferti")
    op.create_table(
        "categories", *_tenant_columns(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("product_type", sa.String(16), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "name", name="uq_ferti_category_tenant_name"),
        schema="ferti",
    )
    op.create_index("ix_ferti_categories_tenant_id", "categories", ["tenant_id"], schema="ferti")
    op.create_table(
        "farmers", *_tenant_columns(),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("mobile", sa.String(24), nullable=False),
        sa.Column("address", sa.Text()),
        sa.Column("village", sa.String(120)),
        sa.Column("opening_balance", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "mobile", name="uq_ferti_farmer_tenant_mobile"),
        schema="ferti",
    )
    op.create_index("ix_ferti_farmers_tenant_id", "farmers", ["tenant_id"], schema="ferti")
    op.create_table(
        "seasons", *_tenant_columns(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("default_cash_discount", sa.Numeric(7, 2), nullable=False, server_default="0"),
        sa.Column("default_credit_interest_per_month", sa.Numeric(7, 2), nullable=False, server_default="0"),
        sa.Column("due_date", sa.Date()),
        sa.Column("grace_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("late_interest_per_day", sa.Numeric(7, 4), nullable=False, server_default="0"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_ferti_season_tenant_name"),
        schema="ferti",
    )
    op.create_index("ix_ferti_seasons_tenant_id", "seasons", ["tenant_id"], schema="ferti")
    op.create_table(
        "settings",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.tenants.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("values", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="ferti",
    )
    op.create_table(
        "products", *_tenant_columns(),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.brands.id")),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.categories.id")),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("grade", sa.String(80)),
        sa.Column("hsn", sa.String(32)),
        sa.Column("gst_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("unit_type", sa.String(16), nullable=False),
        sa.Column("low_stock_level", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "brand_id", "name", name="uq_ferti_product_tenant_brand_name"),
        schema="ferti",
    )
    op.create_index("ix_ferti_products_tenant_id", "products", ["tenant_id"], schema="ferti")
    op.create_table(
        "packs", *_tenant_columns(),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("size", sa.Numeric(14, 3), nullable=False),
        sa.Column("size_unit", sa.String(16), nullable=False),
        sa.Column("size_in_base_unit", sa.Numeric(14, 3), nullable=False),
        sa.Column("mrp", sa.Numeric(14, 2), nullable=False),
        sa.Column("cash_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("credit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("barcode", sa.String(80)),
        sa.Column("allow_loose_sale", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "product_id", "size_in_base_unit", name="uq_ferti_pack_size"),
        sa.UniqueConstraint("tenant_id", "barcode", name="uq_ferti_pack_tenant_barcode"),
        schema="ferti",
    )
    op.create_index("ix_ferti_packs_tenant_id", "packs", ["tenant_id"], schema="ferti")
    op.create_index("ix_ferti_packs_tenant_barcode", "packs", ["tenant_id", "barcode"], schema="ferti")
    op.create_table(
        "stock_lots", *_tenant_columns(),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.packs.id"), nullable=False),
        sa.Column("supplier", sa.String(180)),
        sa.Column("received_date", sa.Date(), nullable=False),
        sa.Column("quantity_base", sa.Numeric(14, 3), nullable=False),
        sa.Column("available_base", sa.Numeric(14, 3), nullable=False),
        sa.Column("cost_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("batch_number", sa.String(80)),
        sa.Column("expiry_date", sa.Date()),
        schema="ferti",
    )
    op.create_index("ix_ferti_stock_lots_tenant_id", "stock_lots", ["tenant_id"], schema="ferti")
    op.create_index("ix_ferti_stock_lots_tenant_expiry", "stock_lots", ["tenant_id", "expiry_date"], schema="ferti")
    op.create_table(
        "bills", *_tenant_columns(),
        sa.Column("bill_number", sa.String(40), nullable=False),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.farmers.id"), nullable=False),
        sa.Column("season_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.seasons.id")),
        sa.Column("bill_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date()),
        sa.Column("payment_type", sa.String(12), nullable=False),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False),
        sa.Column("discount", sa.Numeric(14, 2), nullable=False),
        sa.Column("interest_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("gst_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("round_off", sa.Numeric(14, 2), nullable=False),
        sa.Column("total", sa.Numeric(14, 2), nullable=False),
        sa.Column("paid_now", sa.Numeric(14, 2), nullable=False),
        sa.Column("balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="posted"),
        sa.Column("terms", sa.Text()),
        sa.Column("idempotency_key", sa.String(120)),
        sa.UniqueConstraint("tenant_id", "bill_number", name="uq_ferti_bill_tenant_number"),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_ferti_bill_idempotency"),
        schema="ferti",
    )
    op.create_index("ix_ferti_bills_tenant_id", "bills", ["tenant_id"], schema="ferti")
    op.create_index("ix_ferti_bills_tenant_farmer_date", "bills", ["tenant_id", "farmer_id", "bill_date"], schema="ferti")
    op.create_table(
        "bill_items", *_tenant_columns(),
        sa.Column("bill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.bills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.packs.id"), nullable=False),
        sa.Column("product_name", sa.String(180), nullable=False),
        sa.Column("pack_name", sa.String(80), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("quantity_base", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        schema="ferti",
    )
    op.create_index("ix_ferti_bill_items_tenant_id", "bill_items", ["tenant_id"], schema="ferti")
    op.create_table(
        "payments", *_tenant_columns(),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.farmers.id"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("mode", sa.String(12), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("bill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.bills.id")),
        sa.Column("idempotency_key", sa.String(120)),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_ferti_payment_idempotency"),
        schema="ferti",
    )
    op.create_index("ix_ferti_payments_tenant_id", "payments", ["tenant_id"], schema="ferti")
    op.create_index("ix_ferti_payments_tenant_farmer_date", "payments", ["tenant_id", "farmer_id", "payment_date"], schema="ferti")
    op.create_table(
        "payment_allocations", *_tenant_columns(),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.payments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.bills.id"), nullable=False),
        sa.Column("interest_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("principal_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        schema="ferti",
    )
    op.create_index("ix_ferti_payment_allocations_tenant_id", "payment_allocations", ["tenant_id"], schema="ferti")
    op.create_table(
        "khata_entries", *_tenant_columns(),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.farmers.id"), nullable=False),
        sa.Column("bill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.bills.id")),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.payments.id")),
        sa.Column("entry_type", sa.String(24), nullable=False),
        sa.Column("debit", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("credit", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("reverses_entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.khata_entries.id")),
        schema="ferti",
    )
    op.create_index("ix_ferti_khata_entries_tenant_id", "khata_entries", ["tenant_id"], schema="ferti")
    op.create_index("ix_ferti_khata_tenant_farmer_date", "khata_entries", ["tenant_id", "farmer_id", "created_at"], schema="ferti")
    op.create_table(
        "stock_movements", *_tenant_columns(),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.packs.id"), nullable=False),
        sa.Column("stock_lot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ferti.stock_lots.id")),
        sa.Column("movement_type", sa.String(24), nullable=False),
        sa.Column("quantity_base", sa.Numeric(14, 3), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("source_id", postgresql.UUID(as_uuid=True)),
        sa.Column("source_type", sa.String(24)),
        schema="ferti",
    )
    op.create_index("ix_ferti_stock_movements_tenant_id", "stock_movements", ["tenant_id"], schema="ferti")
    op.create_index("ix_ferti_stock_movements_pack_date", "stock_movements", ["tenant_id", "pack_id", "created_at"], schema="ferti")
    op.create_table(
        "cashbook_entries", *_tenant_columns(),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("description", sa.Text()),
        schema="ferti",
    )
    op.create_index("ix_ferti_cashbook_entries_tenant_id", "cashbook_entries", ["tenant_id"], schema="ferti")
    op.create_index("ix_ferti_cashbook_tenant_date", "cashbook_entries", ["tenant_id", "entry_date"], schema="ferti")
    op.create_table(
        "bill_drafts", *_tenant_columns(),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        schema="ferti",
    )
    op.create_index("ix_ferti_bill_drafts_tenant_id", "bill_drafts", ["tenant_id"], schema="ferti")
    op.create_table(
        "audit_logs", *_tenant_columns(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("old_values", postgresql.JSONB()),
        sa.Column("new_values", postgresql.JSONB()),
        schema="ferti",
    )
    op.create_index("ix_ferti_audit_logs_tenant_id", "audit_logs", ["tenant_id"], schema="ferti")
    op.create_index("ix_ferti_audit_tenant_entity", "audit_logs", ["tenant_id", "entity_type", "entity_id"], schema="ferti")
    op.create_table(
        "idempotency_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation", sa.String(40), nullable=False),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("response", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "operation", "key", name="uq_ferti_idempotency_tenant_operation_key"),
        schema="ferti",
    )
    op.create_index("ix_ferti_idempotency_records_tenant_id", "idempotency_records", ["tenant_id"], schema="ferti")
    op.create_table(
        "auth_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.org_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(24), nullable=False),
        sa.Column("provider_subject", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_ferti_auth_provider_subject"),
        schema="ferti",
    )
    op.create_index("ix_ferti_auth_identities_tenant_id", "auth_identities", ["tenant_id"], schema="ferti")
    op.create_table(
        "otp_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone", sa.String(24), nullable=False),
        sa.Column("subdomain", sa.String(40)),
        sa.Column("purpose", sa.String(16), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="ferti",
    )
    op.create_index("ix_ferti_otp_phone_purpose_created", "otp_challenges", ["phone", "purpose", "created_at"], schema="ferti")
    op.create_table(
        "auth_action_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.org_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(24), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="ferti",
    )
    op.create_index("ix_ferti_auth_action_tokens_tenant_id", "auth_action_tokens", ["tenant_id"], schema="ferti")
    op.create_index("ix_ferti_auth_tokens_tenant_user", "auth_action_tokens", ["tenant_id", "user_id", "purpose"], schema="ferti")
    op.create_table(
        "refresh_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.org_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="ferti",
    )
    op.create_index("ix_ferti_refresh_sessions_tenant_id", "refresh_sessions", ["tenant_id"], schema="ferti")
    op.create_index("ix_ferti_refresh_tenant_user", "refresh_sessions", ["tenant_id", "user_id"], schema="ferti")
    op.create_table(
        "auth_rate_limits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("subject_hash", sa.String(64), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.UniqueConstraint("action", "subject_hash", "window_start", name="uq_ferti_rate_limit_bucket"),
        schema="ferti",
    )


def downgrade() -> None:
    op.drop_table("auth_rate_limits", schema="ferti")
    op.drop_table("refresh_sessions", schema="ferti")
    op.drop_table("auth_action_tokens", schema="ferti")
    op.drop_table("otp_challenges", schema="ferti")
    op.drop_table("auth_identities", schema="ferti")
    op.drop_table("idempotency_records", schema="ferti")
    op.drop_table("audit_logs", schema="ferti")
    op.drop_table("bill_drafts", schema="ferti")
    op.drop_table("cashbook_entries", schema="ferti")
    op.drop_table("stock_movements", schema="ferti")
    op.drop_table("khata_entries", schema="ferti")
    op.drop_table("payment_allocations", schema="ferti")
    op.drop_table("payments", schema="ferti")
    op.drop_table("bill_items", schema="ferti")
    op.drop_table("bills", schema="ferti")
    op.drop_table("stock_lots", schema="ferti")
    op.drop_table("packs", schema="ferti")
    op.drop_table("products", schema="ferti")
    op.drop_table("settings", schema="ferti")
    op.drop_table("seasons", schema="ferti")
    op.drop_table("farmers", schema="ferti")
    op.drop_table("categories", schema="ferti")
    op.drop_table("brands", schema="ferti")
    op.drop_column("org_users", "language", schema="org")
    op.drop_constraint("uq_org_user_tenant_phone", "org_users", schema="org", type_="unique")
    op.drop_column("org_users", "email_verified", schema="org")
    op.drop_column("org_users", "phone", schema="org")
    op.drop_column("tenants", "logo_url", schema="org")
    op.drop_column("tenants", "phone", schema="org")
    op.drop_column("tenants", "gstin", schema="org")
    op.drop_column("tenants", "address", schema="org")
    op.execute("DROP SCHEMA ferti")
