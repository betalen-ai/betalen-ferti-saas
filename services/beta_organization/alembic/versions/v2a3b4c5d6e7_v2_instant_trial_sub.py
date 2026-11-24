"""v2: instant activation, 6-month trial, subscription enforcement

Revision ID: v2a3b4c5d6e7
Revises: a1b2c3d4e5f7
"""
from typing import Sequence, Union

from alembic import op


revision: str = "v2a3b4c5d6e7"
down_revision: Union[str, None] = "a1b2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # trial subscription plan + 180-day trial length platform setting
    op.execute("""
    ALTER TABLE org.tenants ALTER COLUMN status SET DEFAULT 'ACTIVE'
    """)
    op.execute("""
    ALTER TABLE org.subscriptions ALTER COLUMN plan SET DEFAULT 'TRIAL'
    """)
    op.execute("""
    ALTER TABLE org.subscriptions ALTER COLUMN status SET DEFAULT 'TRIAL'
    """)
    # add platform settings table for trial length, grace period, expired mode
    op.execute("""
    CREATE TABLE IF NOT EXISTS org.platform_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """)
    op.execute("INSERT INTO org.platform_settings (key, value) VALUES ('trial_days', '180') ON CONFLICT DO NOTHING")
    op.execute("INSERT INTO org.platform_settings (key, value) VALUES ('grace_days', '7') ON CONFLICT DO NOTHING")
    op.execute("INSERT INTO org.platform_settings (key, value) VALUES ('expired_mode', 'read_only') ON CONFLICT DO NOTHING")
    op.execute("INSERT INTO org.platform_settings (key, value) VALUES ('max_refresh_days', '30') ON CONFLICT DO NOTHING")
    op.execute("INSERT INTO org.platform_settings (key, value) VALUES ('access_token_minutes', '15') ON CONFLICT DO NOTHING")
    op.execute("INSERT INTO org.platform_settings (key, value) VALUES ('admin_token_minutes', '10') ON CONFLICT DO NOTHING")
    # subscription plans catalog
    op.execute("""
    CREATE TABLE IF NOT EXISTS org.subscription_plans (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        max_staff INTEGER NOT NULL DEFAULT 2,
        features JSONB NOT NULL DEFAULT '{}',
        price_monthly NUMERIC(10,2) NOT NULL DEFAULT 0,
        price_yearly NUMERIC(10,2) NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """)
    op.execute("INSERT INTO org.subscription_plans (code, name, max_staff, features) VALUES ('TRIAL', 'Free Trial', 2, '{\"billing\":true,\"inventory\":true,\"farmers\":true,\"khata\":true,\"reports\":true,\"exports\":true}') ON CONFLICT DO NOTHING")
    op.execute("INSERT INTO org.subscription_plans (code, name, max_staff, features) VALUES ('BASIC', 'Basic', 3, '{\"billing\":true,\"inventory\":true,\"farmers\":true,\"khata\":true,\"reports\":true,\"exports\":true}') ON CONFLICT DO NOTHING")
    op.execute("INSERT INTO org.subscription_plans (code, name, max_staff, features) VALUES ('STANDARD', 'Standard', 10, '{\"billing\":true,\"inventory\":true,\"farmers\":true,\"khata\":true,\"reports\":true,\"exports\":true,\"multi_user\":true}') ON CONFLICT DO NOTHING")
    op.execute("INSERT INTO org.subscription_plans (code, name, max_staff, features) VALUES ('PREMIUM', 'Premium', 999, '{\"billing\":true,\"inventory\":true,\"farmers\":true,\"khata\":true,\"reports\":true,\"exports\":true,\"multi_user\":true,\"whatsapp\":true,\"multi_branch\":true,\"advanced_reports\":true}') ON CONFLICT DO NOTHING")
    # subscription events audit
    op.execute("""
    CREATE TABLE IF NOT EXISTS org.subscription_events (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES org.tenants(id) ON DELETE CASCADE,
        subscription_id UUID REFERENCES org.subscriptions(id) ON DELETE CASCADE,
        event_type TEXT NOT NULL,
        from_status TEXT, to_status TEXT, from_plan TEXT, to_plan TEXT,
        reason TEXT, actor_type TEXT, actor_id UUID,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """)
    # staff management
    op.execute("""
    CREATE TABLE IF NOT EXISTS org.staff (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES org.tenants(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        mobile TEXT,
        email TEXT,
        role_template TEXT,
        permissions JSONB NOT NULL DEFAULT '[]',
        is_active BOOLEAN NOT NULL DEFAULT true,
        must_change_password BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_org_staff_tenant ON org.staff (tenant_id)")
    # notifications
    op.execute("""
    CREATE TABLE IF NOT EXISTS org.notifications (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES org.tenants(id) ON DELETE CASCADE,
        notification_key TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        level TEXT NOT NULL DEFAULT 'INFO',
        is_read BOOLEAN NOT NULL DEFAULT false,
        action_label TEXT, action_route TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_org_notifications_tenant ON org.notifications (tenant_id, is_read)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_org_notification_key ON org.notifications (tenant_id, notification_key) WHERE is_read = false")
    # subscription access cache (optional; we compute live)
    op.execute("""
    CREATE TABLE IF NOT EXISTS org.subscription_payments (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        tenant_id UUID REFERENCES org.tenants(id) ON DELETE CASCADE,
        subscription_id UUID REFERENCES org.subscriptions(id) ON DELETE CASCADE,
        gateway TEXT, gateway_order_id TEXT, gateway_payment_id TEXT,
        amount NUMERIC(12,2) NOT NULL, currency TEXT NOT NULL DEFAULT 'INR',
        status TEXT NOT NULL DEFAULT 'PENDING',
        paid_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS org.subscription_payments")
    op.execute("DROP TABLE IF EXISTS org.notifications")
    op.execute("DROP TABLE IF EXISTS org.staff")
    op.execute("DROP TABLE IF EXISTS org.subscription_events")
    op.execute("DROP TABLE IF EXISTS org.subscription_plans")
    op.execute("DROP TABLE IF EXISTS org.platform_settings")
    op.execute("ALTER TABLE org.subscriptions ALTER COLUMN plan DROP DEFAULT")
    op.execute("ALTER TABLE org.subscriptions ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE org.tenants ALTER COLUMN status DROP DEFAULT")