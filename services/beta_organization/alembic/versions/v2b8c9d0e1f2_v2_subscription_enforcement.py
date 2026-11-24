"""v2: instant activation, 6-month trial, subscription enforcement

Revision ID: v2b8c9d0e1f2
Revises: v2a3b4c5d6e7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "v2b8c9d0e1f2"
down_revision: Union[str, None] = "v2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. org.tenants -> align to spec v2
    op.execute("ALTER TABLE org.tenants DROP CONSTRAINT IF EXISTS org_tenants_subdomain_key")
    op.drop_column("tenants", "subdomain", schema="org")
    op.drop_column("tenants", "subscription_plan", schema="org")

    tenant_cols = [
        ("shop_types", postgresql.ARRAY(sa.String()), False, "ARRAY[]::varchar[]"),
        ("gstin", sa.String(15), True, None),
        ("pan", sa.String(10), True, None),
        ("address_line", sa.Text(), True, None),
        ("village_town", sa.String(120), True, None),
        ("mandal_taluk", sa.String(120), True, None),
        ("district", sa.String(120), True, None),
        ("state", sa.String(80), True, None),
        ("pincode", sa.String(6), True, None),
        ("latitude", postgresql.JSONB(astext_type=sa.Text()), True, None),
        ("longitude", postgresql.JSONB(astext_type=sa.Text()), True, None),
        ("years_in_business", sa.Integer(), True, None),
        ("farmers_served_range", sa.String(40), True, None),
        ("current_system", sa.String(40), True, None),
        ("referral_code", sa.String(80), True, None),
        ("heard_from", sa.String(120), True, None),
        ("fertilizer_licence_no", sa.String(120), True, None),
        ("fertilizer_licence_expiry", sa.Date(), True, None),
        ("pesticide_licence_no", sa.String(120), True, None),
        ("pesticide_licence_expiry", sa.Date(), True, None),
        ("seed_licence_no", sa.String(120), True, None),
        ("seed_licence_expiry", sa.Date(), True, None),
        ("language", sa.String(8), False, "'en'"),
        ("registered_at", sa.DateTime(timezone=True), False, None),
        ("suspended_at", sa.DateTime(timezone=True), True, None),
        ("suspended_reason", sa.Text(), True, None),
        ("closed_at", sa.DateTime(timezone=True), True, None),
        ("consent_terms_version", sa.String(40), True, None),
        ("consent_at", sa.DateTime(timezone=True), True, None),
        ("consent_ip", sa.String(64), True, None),
        ("version", sa.Integer(), False, "1"),
    ]
    for name, type_, nullable, default in tenant_cols:
        op.add_column(
            "tenants",
            sa.Column(name, type_, nullable=nullable, server_default=sa.text(default) if default else None),
            schema="org",
        )
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_org_tenant_reference_no' AND conrelid = 'org.tenants'::regclass
        ) THEN
            ALTER TABLE org.tenants ADD CONSTRAINT uq_org_tenant_reference_no UNIQUE (reference_no);
        END IF;
    END $$;
    """)

    # 2. org.org_users -> align to spec v2
    op.execute("ALTER TABLE org.org_users DROP CONSTRAINT IF EXISTS uq_org_user_email")
    op.execute("ALTER TABLE org.org_users DROP CONSTRAINT IF EXISTS uq_org_user_tenant_email")
    op.execute("ALTER TABLE org.org_users DROP CONSTRAINT IF EXISTS uq_org_user_tenant_phone")
    op.drop_column("org_users", "role_id", schema="org")
    op.drop_column("org_users", "is_super_admin", schema="org")
    op.drop_column("org_users", "language", schema="org")
    op.drop_column("org_users", "full_name", schema="org")

    user_cols = [
        ("role", sa.String(24), False, "'STAFF'"),
        ("name", sa.String(120), True, None),
        ("email", sa.String(255), True, None),
        ("email_verified", sa.Boolean(), False, "false"),
        ("phone", sa.String(24), True, None),
        ("phone_verified", sa.Boolean(), False, "false"),
        ("password_hash", sa.String(255), True, None),
        ("permissions", postgresql.ARRAY(sa.String()), False, "ARRAY[]::varchar[]"),
        ("role_template_id", postgresql.UUID(as_uuid=True), True, None),
        ("status", sa.String(24), False, "'ACTIVE'"),
        ("created_by", postgresql.UUID(as_uuid=True), True, None),
        ("failed_login_count", sa.Integer(), False, "0"),
        ("locked_until", sa.DateTime(timezone=True), True, None),
        ("last_login_at", sa.DateTime(timezone=True), True, None),
        ("password_changed_at", sa.DateTime(timezone=True), True, None),
    ]
    for name, type_, nullable, default in user_cols:
        op.add_column(
            "org_users",
            sa.Column(name, type_, nullable=nullable, server_default=sa.text(default) if default else None),
            schema="org",
        )
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_org_user_email' AND conrelid = 'org.org_users'::regclass
        ) THEN
            ALTER TABLE org.org_users ADD CONSTRAINT uq_org_user_email UNIQUE (email);
        END IF;
    END $$;
    """)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_org_user_phone' AND conrelid = 'org.org_users'::regclass
        ) THEN
            ALTER TABLE org.org_users ADD CONSTRAINT uq_org_user_phone UNIQUE (phone);
        END IF;
    END $$;
    """)
    op.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS uq_org_user_tenant_one_tenant
    ON org.org_users (tenant_id)
    WHERE role = 'TENANT';
    """)
    op.create_index("ix_org_org_users_tenant_id", "org_users", ["tenant_id"], schema="org")
    op.create_index("ix_org_org_users_role", "org_users", ["role"], schema="org")

    # 3. org.tenant_subscriptions (spec 12.6)
    op.execute("""
    CREATE TABLE IF NOT EXISTS org.tenant_subscriptions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID NOT NULL REFERENCES org.tenants(id) ON DELETE CASCADE,
        plan_id TEXT NOT NULL REFERENCES org.subscription_plans(code),
        status TEXT NOT NULL DEFAULT 'TRIAL',
        start_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        current_period_end TIMESTAMPTZ NOT NULL,
        trial_ends_at TIMESTAMPTZ,
        grace_ends_at TIMESTAMPTZ,
        cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
        cancelled_at TIMESTAMPTZ,
        extended_by_admin_id UUID,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        version INTEGER NOT NULL DEFAULT 1
    );
    """)
    op.create_index("ix_org_tenant_subscriptions_tenant", "tenant_subscriptions", ["tenant_id"], schema="org")
    op.create_index("ix_org_tenant_subscriptions_period_end", "tenant_subscriptions", ["current_period_end"], schema="org")
    op.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS uq_org_tenant_subscriptions_current
    ON org.tenant_subscriptions (tenant_id)
    WHERE status IN ('TRIAL', 'ACTIVE', 'GRACE');
    """)

    # 4. org.auth_identities (spec 12.4)
    op.execute("""
    CREATE TABLE IF NOT EXISTS org.auth_identities (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID NOT NULL REFERENCES org.org_users(id) ON DELETE CASCADE,
        provider TEXT NOT NULL,
        provider_user_id TEXT NOT NULL,
        email_at_link TEXT,
        linked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_used_at TIMESTAMPTZ,
        CONSTRAINT uq_auth_identity_provider_subject UNIQUE (provider, provider_user_id)
    );
    """)
    op.create_index("ix_org_auth_identities_user_id", "auth_identities", ["user_id"], schema="org")

    # 5. org.platform_settings
    op.execute("""
    CREATE TABLE IF NOT EXISTS org.platform_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """)
    for key, val in [
        ("trial_days", "180"), ("grace_days", "7"), ("expired_mode", "read_only"),
        ("max_refresh_days", "30"), ("access_token_minutes", "15"), ("admin_token_minutes", "10"),
    ]:
        op.execute(
            f"INSERT INTO org.platform_settings (key, value) VALUES ('{key}', '{val}') ON CONFLICT (key) DO NOTHING"
        )

    # 6. subscription_plans -> add missing columns (spec 12.5)
    plan_cols = [
        ("duration_days", sa.Integer(), True, None),
        ("price_amount", sa.Numeric(10, 2), False, "0"),
        ("currency", sa.String(8), False, "'INR'"),
        ("billing_period", sa.String(24), False, "'MONTHLY'"),
        ("is_active", sa.Boolean(), False, "true"),
        ("sort_order", sa.Integer(), False, "0"),
    ]
    for name, type_, nullable, default in plan_cols:
        op.add_column(
            "subscription_plans",
            sa.Column(name, type_, nullable=nullable, server_default=sa.text(default) if default else None),
            schema="org",
        )

    # 7. Drop legacy org.subscriptions table (replaced by tenant_subscriptions)
    op.execute("DROP TABLE IF EXISTS org.subscriptions")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS org.tenant_subscriptions")
    op.execute("DROP TABLE IF EXISTS org.auth_identities")