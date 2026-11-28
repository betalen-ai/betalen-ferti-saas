"""Onboarding, approval, auth and audit tables.

Revision ID: e1f2a3b4c5d6
Revises: d4e5f6a7b8c9
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("refresh_sessions", sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=True), schema="ferti")
    op.add_column("refresh_sessions", sa.Column("replaced_by_id", postgresql.UUID(as_uuid=True), nullable=True), schema="ferti")
    op.add_column("refresh_sessions", sa.Column("revoked_reason", sa.String(40), nullable=True), schema="ferti")
    op.add_column("refresh_sessions", sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True), schema="ferti")
    op.add_column("refresh_sessions", sa.Column("ip", sa.String(64), nullable=True), schema="ferti")
    op.add_column("refresh_sessions", sa.Column("user_agent", sa.Text(), nullable=True), schema="ferti")
    op.add_column("refresh_sessions", sa.Column("device_label", sa.String(120), nullable=True), schema="ferti")
    op.execute("ALTER TABLE org.tenants ALTER COLUMN status SET DEFAULT 'PENDING_REVIEW'")
    for name, type_, nullable in [
        ("shop_types", postgresql.ARRAY(sa.String()), False),
        ("pan", sa.String(10), True),
        ("address_line", sa.Text(), True),
        ("village_town", sa.String(120), True),
        ("mandal_taluk", sa.String(120), True),
        ("district", sa.String(120), True),
        ("state", sa.String(80), True),
        ("pincode", sa.String(6), True),
        ("latitude", sa.Numeric(9, 6), True),
        ("longitude", sa.Numeric(9, 6), True),
        ("years_in_business", sa.Integer(), True),
        ("farmers_served_range", sa.String(40), True),
        ("current_system", sa.String(40), True),
        ("referral_code", sa.String(80), True),
        ("heard_from", sa.String(120), True),
        ("fertilizer_licence_no", sa.String(120), True),
        ("fertilizer_licence_expiry", sa.Date(), True),
        ("pesticide_licence_no", sa.String(120), True),
        ("pesticide_licence_expiry", sa.Date(), True),
        ("seed_licence_no", sa.String(120), True),
        ("seed_licence_expiry", sa.Date(), True),
        ("language", sa.String(8), False),
        ("alternate_mobile", sa.String(24), True),
        ("submitted_at", sa.DateTime(timezone=True), True),
        ("reviewed_at", sa.DateTime(timezone=True), True),
        ("reviewed_by", postgresql.UUID(as_uuid=True), True),
        ("review_reason", sa.Text(), True),
        ("approved_at", sa.DateTime(timezone=True), True),
        ("suspended_at", sa.DateTime(timezone=True), True),
        ("closed_at", sa.DateTime(timezone=True), True),
        ("reference_no", sa.String(40), True),
        ("consent_terms_version", sa.String(40), True),
        ("consent_at", sa.DateTime(timezone=True), True),
        ("consent_ip", sa.String(64), True),
        ("consent_whatsapp", sa.Boolean(), False),
        ("version", sa.Integer(), False),
        ("updated_at", sa.DateTime(timezone=True), True),
    ]:
        kwargs = {"server_default": sa.text("'{}'::varchar[]") if name == "shop_types" else (sa.text("'en'") if name == "language" else (sa.text("false") if name == "consent_whatsapp" else (sa.text("1") if name == "version" else None)))}
        if kwargs["server_default"] is None:
            kwargs.pop("server_default")
        op.add_column("tenants", sa.Column(name, type_, nullable=nullable, **kwargs), schema="org")

    op.execute("ALTER TABLE org.org_users ALTER COLUMN password_hash DROP NOT NULL")
    op.add_column("org_users", sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.false()), schema="org")
    op.add_column("org_users", sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"), schema="org")
    op.add_column("org_users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True), schema="org")
    op.add_column("org_users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True), schema="org")
    op.add_column("org_users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True), schema="org")

    op.create_table(
        "tenant_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doc_type", sa.String(40), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("scan_status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True)),
        schema="org",
    )
    op.create_table(
        "tenant_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(24), nullable=False),
        sa.Column("admin_id", postgresql.UUID(as_uuid=True)),
        sa.Column("reason_code", sa.String(80)),
        sa.Column("note", sa.Text()),
        sa.Column("data_snapshot", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="org",
    )
    op.create_table(
        "platform_admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("totp_secret_encrypted", sa.String(255)),
        sa.Column("role", sa.String(24), nullable=False, server_default="SUPER_ADMIN"),
        sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        schema="org",
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.org_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_reason", sa.String(40)),
        sa.Column("replaced_by_id", postgresql.UUID(as_uuid=True)),
        sa.Column("ip", sa.String(64)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("device_label", sa.String(120)),
        schema="org",
    )
    op.create_table(
        "auth_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.tenants.id", ondelete="SET NULL")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.org_users.id", ondelete="SET NULL")),
        sa.Column("identifier", sa.String(255)),
        sa.Column("method", sa.String(24), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(80)),
        sa.Column("ip", sa.String(64)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("device", sa.String(120)),
        sa.Column("approx_location", sa.String(120)),
        sa.Column("request_id", sa.String(80)),
        schema="org",
    )
    op.create_table(
        "password_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.org_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("change_type", sa.String(24), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("changed_by", sa.String(80)),
        sa.Column("ip", sa.String(64)),
        sa.Column("user_agent", sa.Text()),
        schema="org",
    )
    op.create_table(
        "otp_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone", sa.String(24), nullable=False),
        sa.Column("purpose", sa.String(24), nullable=False),
        sa.Column("otp_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("ip", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="org",
    )
    op.create_table(
        "audit_log",
        sa.Column("audit_log_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("actor_type", sa.String(24), nullable=False),
        sa.Column("action", sa.String(24), nullable=False),
        sa.Column("entity_name", sa.String(120), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("json_payload", postgresql.JSONB(), nullable=False),
        sa.Column("request_id", sa.String(80)),
        sa.Column("ip", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="org",
    )
    op.create_index("ix_org_audit_log_tenant_created", "audit_log", ["tenant_id", "created_at"], schema="org")
    op.create_index("ix_org_audit_log_entity", "audit_log", ["tenant_id", "entity_name", "entity_id"], schema="org")
    op.create_index("ix_org_auth_events_tenant_created", "auth_events", ["tenant_id", "created_at"], schema="org")
    op.create_index("ix_org_refresh_tokens_family", "refresh_tokens", ["family_id"], schema="org")
    op.create_index("ix_org_refresh_tokens_user_revoked", "refresh_tokens", ["user_id", "revoked_at"], schema="org")

    op.execute("""
    CREATE OR REPLACE FUNCTION org.prevent_audit_log_mutation()
    RETURNS trigger AS $$
    BEGIN
        RAISE EXCEPTION 'audit_log is append-only';
    END;
    $$ LANGUAGE plpgsql
    """)
    op.execute("""
    CREATE TRIGGER audit_log_append_only
    BEFORE UPDATE OR DELETE ON org.audit_log
    FOR EACH ROW EXECUTE FUNCTION org.prevent_audit_log_mutation()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_log_append_only ON org.audit_log")
    op.execute("DROP FUNCTION IF EXISTS org.prevent_audit_log_mutation()")
    op.drop_table("audit_log", schema="org")
